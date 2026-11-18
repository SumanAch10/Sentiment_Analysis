"""Collect public top-level YouTube comments into a local historical dataset."""

import argparse
from collections import Counter
from datetime import UTC, datetime, timedelta
from getpass import getpass
import hashlib
import hmac
import json
import os
from pathlib import Path
import sys

from collect_opinions import ApiError, KEYWORDS, YOUTUBE, get_json

FIRST_YEAR = 2016
LAST_YEAR = 2026
GROUPS = ("general", "multiplanetary", "tourism")
COMMENT_START = datetime(FIRST_YEAR, 1, 1, tzinfo=UTC)
COMMENT_END = datetime(LAST_YEAR + 1, 1, 1, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "data" / "interim" / "youtube_history"


def local_settings():
    """Read the collector's two settings from the repository's local .env."""
    path = REPO_ROOT / ".env"
    if not path.is_file():
        return {}
    settings = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        name, _, value = line.partition("=")
        name = name.strip()
        if name in {"YOUTUBE_API_KEY", "COLLECTION_AUTHOR_SALT"}:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            settings[name] = value
    return settings


def utc_timestamp(value):
    return datetime.fromisoformat(value).astimezone(UTC)


def api_pages(resource, parameters, limit, request_counts):
    for _ in range(limit):
        request_counts[resource] += 1
        result = get_json(YOUTUBE + resource, parameters)
        yield result
        token = result.get("nextPageToken")
        if not token:
            break
        parameters = {**parameters, "pageToken": token}


def discover(year, args, key, stats):
    start = datetime(year, 1, 1, tzinfo=UTC)
    end = datetime(year + 1, 1, 1, tzinfo=UTC)
    videos = {}
    for group in GROUPS:
        for query in KEYWORDS[group]:
            params = {
                "key": key, "part": "snippet", "type": "video",
                "q": query, "order": "relevance", "relevanceLanguage": "en",
                "publishedAfter": (start - timedelta(seconds=1)).isoformat(),
                "publishedBefore": end.isoformat(), "maxResults": args.videos_per_page,
            }
            for result in api_pages("search", params, args.search_pages, stats["requests"]):
                for item in result["items"]:
                    snippet = item["snippet"]
                    published = utc_timestamp(snippet["publishedAt"])
                    if not start <= published < end:
                        continue
                    video_id = item["id"]["videoId"]
                    if video_id not in videos:
                        videos[video_id] = {
                            "channel": snippet["channelTitle"],
                            "published_utc": published.isoformat(), "matches": [],
                        }
                    match = {"keyword_group": group, "query": query}
                    if match not in videos[video_id]["matches"]:
                        videos[video_id]["matches"].append(match)
            stats["searches"].append({"query": query, "more_results": bool(result.get("nextPageToken"))})
    return videos


def collect_video(video_id, video, args, key, salt, stats, stream, seen):
    params = {
        "key": key, "part": "snippet", "videoId": video_id,
        "textFormat": "plainText", "order": "time", "maxResults": 100,
    }
    try:
        for result in api_pages("commentThreads", params, args.comment_pages, stats["requests"]):
            for thread in result["items"]:
                snippet = thread["snippet"]
                comment = snippet["topLevelComment"]
                item = comment["snippet"]
                comment_id = comment["id"]
                created = utc_timestamp(item["publishedAt"])
                raw = item.get("textOriginal", item.get("textDisplay", ""))
                if comment_id in seen or not COMMENT_START <= created < COMMENT_END or not raw.strip():
                    continue
                author = (item.get("authorChannelId") or {}).get("value") or item.get("authorDisplayName")
                author_hash = (
                    hmac.new(salt, f"youtube:{author}".encode(), hashlib.sha256).hexdigest()
                    if author else None
                )
                record = {
                    "record_id": f"youtube_{comment_id}", "platform": "youtube",
                    "native_id": comment_id, "parent_id": None,
                    "community": video["channel"], "video_id": video_id,
                    "video_published_utc": video["published_utc"],
                    "created_utc": created.isoformat(), "author_hash": author_hash,
                    "text": raw.strip(), "text_raw": raw, "lang": None,
                    "score": item.get("likeCount"), "n_replies": snippet.get("totalReplyCount"),
                    "url": f"https://www.youtube.com/watch?v={video_id}&lc={comment_id}",
                    **video["matches"][0], "matched_queries": video["matches"],
                    "collected_at": datetime.now(UTC).isoformat(), "is_duplicate": False,
                }
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                seen.add(comment_id)
                stats["comments_by_year"][created.year] += 1
                stats["comments"] += 1
    except ApiError as error:
        if error.reason not in {"commentsDisabled", "videoNotFound", "videoUnavailable"}:
            raise
        stats["skipped_videos"][error.reason] += 1
    else:
        stats["videos_scanned"] += 1
        stats["videos_with_more_comment_pages"] += bool(result.get("nextPageToken"))


def run(args, key, salt, output):
    output.mkdir(mode=0o700, parents=True)
    manifest = {
        "comment_start_utc": COMMENT_START.isoformat(),
        "comment_end_exclusive_utc": COMMENT_END.isoformat(),
        "started_utc": datetime.now(UTC).isoformat(),
        "requested_video_upload_years": args.video_years,
        "search_pages": args.search_pages, "videos_per_page": args.videos_per_page,
        "comment_pages": args.comment_pages, "keywords": {group: KEYWORDS[group] for group in GROUPS},
        "batches": {},
    }
    seen = set()
    failed = False
    for year in args.video_years:
        stats = {
            "status": "ok", "searches": [], "requests": Counter(), "videos_discovered": 0,
            "videos_scanned": 0, "videos_with_more_comment_pages": 0, "skipped_videos": Counter(),
            "comments": 0, "comments_by_year": Counter(),
        }
        manifest["batches"][year] = stats
        try:
            videos = discover(year, args, key, stats)
            stats["videos_discovered"] = len(videos)
            with (output / f"videos_uploaded_{year}.jsonl").open("x", encoding="utf-8") as stream:
                for video_id, video in videos.items():
                    collect_video(video_id, video, args, key, salt, stats, stream, seen)
        except (ApiError, KeyboardInterrupt) as error:
            stats["status"] = "partial" if stats["comments"] else "failed"
            stats["error"] = str(error) if isinstance(error, ApiError) else "interrupted"
            failed = True
        finally:
            tmp = output / "manifest.tmp"
            tmp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            tmp.replace(output / "manifest.json")
        print(f"Video upload year {year}: {stats['comments']} comments ({stats['status']})", flush=True)
        if failed:
            print(f"{stats['error']}. Run again for the incomplete upload years.", file=sys.stderr)
            break
    print(f"Local manifest: {output / 'manifest.json'}", flush=True)
    return int(failed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-years", nargs="+", type=int, choices=range(FIRST_YEAR, LAST_YEAR + 1),
                        default=list(range(FIRST_YEAR, LAST_YEAR + 1)))
    parser.add_argument("--search-pages", type=int, default=1)
    parser.add_argument("--videos-per-page", type=int, default=5)
    parser.add_argument("--comment-pages", type=int, default=10)
    args = parser.parse_args()
    args.video_years = sorted(set(args.video_years))
    if min(args.search_pages, args.comment_pages) < 1 or not 1 <= args.videos_per_page <= 50:
        parser.error("page caps must be positive and --videos-per-page must be 1–50")
    settings = local_settings()
    salt = os.environ.get("COLLECTION_AUTHOR_SALT") or settings.get("COLLECTION_AUTHOR_SALT")
    if not salt:
        parser.error("set COLLECTION_AUTHOR_SALT in the repository .env or shell")
    key = os.environ.get("YOUTUBE_API_KEY") or settings.get("YOUTUBE_API_KEY")
    if not key and sys.stdin.isatty():
        key = getpass("YouTube Data API key: ").strip()
    if not key:
        parser.error("set YOUTUBE_API_KEY in the repository .env or shell")
    os.umask(0o077)
    output = OUTPUT_ROOT / datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    return run(args, key, salt.encode(), output)


if __name__ == "__main__":
    sys.exit(main())
