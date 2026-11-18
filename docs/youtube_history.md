# Collect YouTube comments from 2016 through 2026

The collector uses YouTube Data API v3 to search for public videos in each selected upload year. It uses the same 15 space-travel, Mars, and tourism terms for every upload year. It saves public top-level comments dated January 1, 2016 through December 31, 2026 UTC. The final 2026 data will be available only after the year ends. Replies are excluded, but each comment row includes the reported reply count when available.

## Set up on your computer

1. Get a copy of this repository and open a terminal in its root folder. Use Python 3.11 or newer. The collector uses the Python standard library.
2. Create a Google Cloud project, enable **YouTube Data API v3**, and create an API key restricted to that API. The script prompts for the key without echoing it. For unattended runs, set the `YOUTUBE_API_KEY` environment variable. [Google's setup guide](https://developers.google.com/youtube/v3/getting-started)
3. Generate a private salt once with the command below. Save the value in a password manager and reuse it in future batches so the same author gets the same hash. Keep the salt and API key out of Git and the data directory.

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Set the salt in your current terminal session. Use the value you just generated in place of the placeholder.

```bash
# Bash or Zsh
export COLLECTION_AUTHOR_SALT='paste-your-saved-salt'
```

```powershell
# Windows PowerShell
$env:COLLECTION_AUTHOR_SALT = 'paste-your-saved-salt'
```

## Run the collection

Start with one upload year to check the API key and coverage.

```bash
python src/collect/collect_youtube_history.py --video-years 2016
```

Run the remaining upload years in batches that fit your project's available quota.

```bash
python src/collect/collect_youtube_history.py --video-years 2017 2018 2019 2020
python src/collect/collect_youtube_history.py --video-years 2021 2022 2023 2024
python src/collect/collect_youtube_history.py --video-years 2025 2026
```

The command without `--video-years` plans all 11 upload years. The defaults use 15 search requests per upload year, up to five video results per search page, and up to ten comment pages per video. Use `--help` to see the `--search-pages`, `--videos-per-page`, and `--comment-pages` options. Check your quota in Google Cloud before increasing these settings. If a run stops on an API error or quota limit, finished batches and any partial comments remain on disk. Check the manifest, then rerun the incomplete or unattempted upload years once the issue is resolved. [YouTube API quota documentation](https://developers.google.com/youtube/v3/determine_quota_cost)

## Local files and coverage

Each run writes to a new folder under `data/interim/youtube_history/`, which Git ignores. Keep this folder on the local machine during collection. Before transferring it to private OneDrive, check the applicable storage, refresh, and deletion rules. [YouTube API developer policies](https://developers.google.com/youtube/terms/developer-policies)

- `videos_uploaded_YYYY.jsonl` contains one comment per line. The filename is the video upload year. Use `created_utc` for the comment's year or month in the trend analysis.
- `manifest.json` reports comment counts by actual comment year, skipped videos, and where the API offered more pages than were fetched.
- When combining overlapping runs, deduplicate by `record_id`. Keep the stable author salt private.

Video discovery uses relevance-ranked keyword searches and English as a preference. Comment language still needs to be checked during analysis. The sample covers public comments available at collection time on the selected videos. Older comments on busy videos can fall beyond the newest-first page cap, and videos uploaded before 2016 are outside this search. Inspect years with sparse coverage before comparing sentiment.
