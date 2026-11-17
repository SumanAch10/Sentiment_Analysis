# Common data schema

All sources are converted to one format in `data/interim/`.

| Field | Description |
|---|---|
| `record_id` | `<platform>_<native_id>` |
| `platform` | `reddit`, `youtube`, `bluesky`, `x`, `faa` |
| `community` | Subreddit, YouTube channel/video, or null; FAA: `web_form` / `email` |
| `native_id` | Platform's own ID (FAA: `Record_Number`) |
| `parent_id` | ID of the item replied to, if any |
| `created_utc` | Creation time (UTC) |
| `author_hash` | Salted hash of the username |
| `text` | Cleaned text |
| `text_raw` | Text as received |
| `lang` | Detected language |
| `score` | Upvotes / likes, if available |
| `n_replies` | Replies, if available |
| `url` | Link to original (internal use only) |
| `keyword_group` | Which keyword group matched |
| `query` | Exact query that matched |
| `collected_at` | Collection time |
| `is_duplicate` | Duplicate / template flag |

Added in `data/processed/`:

| Field | Description |
|---|---|
| `sentiment_<model>` | Label from each model |
| `sentiment_<model>_score` | Confidence score |
| `human_label` | Hand label, if in the check sample |
