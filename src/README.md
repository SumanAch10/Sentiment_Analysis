# Source code

| Folder | Purpose |
|---|---|
| `collect/` | Public-source collectors |
| `preprocess/` | FAA ingestion, cleaning, de-duplication, conversion to the common schema; writes to `data/interim/` |
| `analysis/` | Sentiment scoring, model-vs-human check, summaries; writes to `data/processed/` and `outputs/` |

[Run the local YouTube historical collector](../docs/youtube_history.md) for video upload years 2016–2026.
