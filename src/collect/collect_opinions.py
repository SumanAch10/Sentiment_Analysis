"""Collect public space-travel opinions using official APIs (Python 3.11+).

Run from the repository root: python src/collect/collect_opinions.py
Set COLLECTION_AUTHOR_SALT to a persistent, secret random value. For YouTube
set YOUTUBE_API_KEY. For Reddit set REDDIT_ACCESS_TOKEN (OAuth with read scope)
and REDDIT_USER_AGENT (a descriptive Reddit API user agent). Bluesky search
uses the public AppView. The default pilot covers the last 90 days. Use
--start and --end for repeatable UTC date windows, and --help for collection caps.
"""

import argparse
from datetime import UTC, date, datetime, time, timedelta
import hashlib
import hmac
import json
import os
from pathlib import Path
import sys
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

KEYWORDS = {
    "general": ("space travel", "space exploration", "spaceflight", "space program", "going to space"),
    "multiplanetary": ("multiplanetary", "multi-planetary", "interplanetary", "Mars colony",
                      "colonize Mars", "colonise Mars", "Mars mission", "living on Mars"),
    "moon": ("Moon base", "Moon landing", "Artemis"),
    "companies": ("SpaceX", "Starship", "Blue Origin", "Virgin Galactic"),
    "agencies": ("NASA", "ESA", "ISRO", "CNSA"),
    "tourism": ("space tourism", "space tourist"),
}
SUBREDDITS = (
    "space", "spacex", "SpaceXLounge", "nasa", "BlueOrigin", "Futurology",
    "science", "AskReddit", "NoStupidQuestions", "changemyview", "worldnews",
    "news", "climate", "collapse", "antiwork",
)
SOURCES = ("bluesky", "youtube", "reddit")
YOUTUBE = "https://www.googleapis.com/youtube/v3/"
REDDIT = "https://oauth.reddit.com"
BLUESKY = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"


class ApiError(Exception):
    def __init__(self, status, reason):
        self.status = status
        self.reason = reason
        super().__init__(f"HTTP {status} ({reason})")


def get_json(url, params, headers=None):
    request = Request(f"{url}?{urlencode(params)}", headers=headers or {})
    sleep(0.35)
    for attempt in range(3):
        try:
            with urlopen(request, timeout=20) as response:
                return json.load(response)
        except HTTPError as error:
            reason = "request_failed"
            try:
                detail = json.load(error).get("error")
                if isinstance(detail, dict):
                    reason = detail.get("errors", [{}])[0].get("reason", reason)
                elif isinstance(detail, str):
                    reason = detail
            except (ValueError, IndexError, AttributeError):
                pass
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise ApiError(error.code, reason) from None
            retry_after = error.headers.get("Retry-After", "")
            if retry_after.isdigit() and int(retry_after) > 60:
                raise ApiError(error.code, reason) from None
            sleep(int(retry_after) if retry_after.isdigit() else 2 ** attempt)
        except (URLError, TimeoutError):
            if attempt == 2:
                raise ApiError("network", "connection_failed") from None
            sleep(2 ** attempt)


def pages(url, params, cursor_in, cursor_out, count, headers=None):
    for _ in range(count):
        payload = get_json(url, params, headers)
        yield payload
        cursor = payload.get(cursor_out)
        if not cursor:
            break
        params = {**params, cursor_in: cursor}


def bluesky(query, start, end, args):
    params = {"q": f'"{query}"', "since": start.isoformat(), "until": end.isoformat(),
              "sort": "latest", "limit": 25, "lang": "en"}
    for page in pages(BLUESKY, params, "cursor", "cursor", args.pages):
        for post in page["posts"]:
            record = post["record"]
            author = post["author"]
            uri = post["uri"]
            post_key = uri.rsplit("/", 1)[-1]
            yield {
                "native_id": uri, "author": author["did"], "community": None,
                "parent_id": record.get("reply", {}).get("parent", {}).get("uri"),
                "created_utc": record["createdAt"], "text_raw": record["text"],
                "lang": next(iter(record.get("langs", [])), None),
                "score": post.get("likeCount"), "n_replies": post.get("replyCount"),
                "url": f"https://bsky.app/profile/{author['did']}/post/{post_key}",
            }


def youtube(query, start, end, args):
    key = os.environ["YOUTUBE_API_KEY"]
    search = {"key": key, "part": "id,snippet", "type": "video", "q": query,
              "publishedAfter": start.isoformat(), "publishedBefore": end.isoformat(),
              "relevanceLanguage": "en", "maxResults": args.threads}
    for page in pages(YOUTUBE + "search", search, "pageToken", "nextPageToken", args.pages):
        for video in page["items"]:
            video_id = video["id"]["videoId"]
            options = {"key": key, "part": "snippet", "videoId": video_id,
                       "textFormat": "plainText", "order": "time", "maxResults": 25}
            try:
                for comments in pages(YOUTUBE + "commentThreads", options,
                                      "pageToken", "nextPageToken", args.pages):
                    for thread in comments["items"]:
                        snippet = thread["snippet"]
                        comment = snippet["topLevelComment"]
                        item = comment["snippet"]
                        yield {
                            "native_id": comment["id"],
                            "author": item.get("authorChannelId", {}).get("value")
                            or item.get("authorDisplayName"),
                            "community": video["snippet"]["channelTitle"], "parent_id": None,
                            "created_utc": item["publishedAt"],
                            "text_raw": item.get("textOriginal", item["textDisplay"]),
                            "lang": None, "score": item.get("likeCount"),
                            "n_replies": snippet.get("totalReplyCount"),
                            "url": f"https://www.youtube.com/watch?v={video_id}&lc={comment['id']}",
                        }
            except ApiError as error:
                if error.reason not in ("commentsDisabled", "videoNotFound"):
                    raise


def reddit_record(item, text, url, parent=None):
    return {
        "native_id": item["name"], "author": item.get("author"),
        "community": item["subreddit"], "parent_id": parent,
        "created_utc": datetime.fromtimestamp(item["created_utc"], UTC).isoformat(),
        "text_raw": text, "lang": None, "score": item.get("score"),
        "n_replies": item.get("num_comments"), "url": url,
    }


def reddit(query, start, end, args):
    headers = {"Authorization": f"Bearer {os.environ['REDDIT_ACCESS_TOKEN']}",
               "User-Agent": os.environ["REDDIT_USER_AGENT"]}
    for community in SUBREDDITS:
        params = {"q": f'"{query}"', "restrict_sr": "true", "sort": "new",
                  "limit": args.threads, "raw_json": 1}
        search_url = f"{REDDIT}/r/{community}/search"
        for _ in range(args.pages):
            listing = get_json(search_url, params, headers)["data"]
            for child in listing["children"]:
                post = child["data"]
                if not start.timestamp() <= post["created_utc"] < end.timestamp():
                    continue
                permalink = post["permalink"]
                body = post.get("selftext", "")
                text = f"{post['title']}\n\n{body}" if body not in ("", "[removed]", "[deleted]") else post["title"]
                yield reddit_record(post, text, f"https://www.reddit.com{permalink}")
                thread = get_json(REDDIT + permalink, {"limit": 25, "depth": 1,
                                                       "sort": "new", "raw_json": 1}, headers)
                for reply in thread[1]["data"]["children"]:
                    if reply["kind"] == "t1":
                        item = reply["data"]
                        yield reddit_record(item, item["body"],
                                            f"https://www.reddit.com{item['permalink']}",
                                            item["parent_id"])
            if not listing["after"]:
                break
            params["after"] = listing["after"]


def collect(platform, start, end, args, output, salt):
    records = {}
    completed = []
    errors = []
    collector = {"bluesky": bluesky, "youtube": youtube, "reddit": reddit}[platform]
    for group in args.groups:
        for query in KEYWORDS[group]:
            try:
                for row in collector(query, start, end, args):
                    created = datetime.fromisoformat(row["created_utc"])
                    raw = row["text_raw"]
                    if not start <= created < end or raw.strip() in ("", "[deleted]", "[removed]"):
                        continue
                    native_id = row["native_id"]
                    if native_id in records:
                        continue
                    author = row.pop("author")
                    author_hash = None
                    if author and author != "[deleted]":
                        author_hash = hmac.new(
                            salt, f"{platform}:{author}".encode(), hashlib.sha256
                        ).hexdigest()
                    collected_at = datetime.now(UTC).isoformat()
                    records[native_id] = dict(
                        row, record_id=f"{platform}_{native_id}", platform=platform,
                        created_utc=created.astimezone(UTC).isoformat(), author_hash=author_hash,
                        text=raw.strip(), keyword_group=group, query=query,
                        collected_at=collected_at, is_duplicate=False,
                    )
                completed.append(query)
            except ApiError as error:
                errors.append({"query": query, "error": str(error)})
                if error.status in (401, 429, "network") or error.reason in (
                    "quotaExceeded", "dailyLimitExceeded", "keyInvalid", "accessNotConfigured"
                ):
                    break
        else:
            continue
        break
    if records:
        with (output / f"{platform}.jsonl").open("x", encoding="utf-8") as stream:
            for record in records.values():
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    status = "ok"
    if errors:
        status = "partial" if completed or records else "failed"
    return {"status": status, "records": len(records), "queries_completed": completed, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", nargs="+", choices=SOURCES, default=list(SOURCES))
    parser.add_argument("--groups", nargs="+", choices=KEYWORDS, default=list(KEYWORDS))
    parser.add_argument("--start", type=date.fromisoformat)
    parser.add_argument("--end", type=date.fromisoformat, help="Exclusive UTC date, defaults to tomorrow")
    parser.add_argument("--pages", type=int, default=1, help="Maximum pages per listing")
    parser.add_argument("--threads", type=int, default=2, help="Videos or Reddit threads per search page")
    parser.add_argument("--output", type=Path, default=Path("data/interim/collection_runs"))
    args = parser.parse_args()
    end_date = args.end or datetime.now(UTC).date() + timedelta(days=1)
    start_date = args.start or end_date - timedelta(days=90)
    if start_date >= end_date or args.pages < 1 or not 1 <= args.threads <= 50:
        parser.error("require start < end, pages >= 1, and 1 <= threads <= 50")
    start = datetime.combine(start_date, time.min, UTC)
    end = datetime.combine(end_date, time.min, UTC)
    salt = os.environ.get("COLLECTION_AUTHOR_SALT")
    if not salt:
        parser.error("set COLLECTION_AUTHOR_SALT to a persistent secret random value")
    output = args.output / datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    output.mkdir(mode=0o700, parents=True)
    manifest = {"start_utc": start.isoformat(), "end_utc": end.isoformat(),
                "pages": args.pages, "threads_per_page": args.threads,
                "keywords": {group: KEYWORDS[group] for group in args.groups},
                "sources": {}}
    required = {"youtube": ("YOUTUBE_API_KEY",),
                "reddit": ("REDDIT_ACCESS_TOKEN", "REDDIT_USER_AGENT")}
    for platform in dict.fromkeys(args.sources):
        missing = [name for name in required.get(platform, ()) if not os.getenv(name)]
        if missing:
            result = {"status": "skipped", "records": 0, "missing_environment": missing}
        else:
            result = collect(platform, start, end, args, output, salt.encode())
        manifest["sources"][platform] = result
        print(f"{platform}: {result['status']} ({result['records']} records)", flush=True)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Manifest: {output / 'manifest.json'}")
    return 0 if all(item["status"] == "ok" for item in manifest["sources"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
