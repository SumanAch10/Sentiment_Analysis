# Source code (not yet implemented)

| Folder | Purpose |
|---|---|
| `collect/` | One collector per platform; writes to `data/raw/<platform>/` |
| `preprocess/` | FAA ingestion, cleaning, de-duplication, conversion to the common schema; writes to `data/interim/` |
| `analysis/` | Sentiment scoring, model-vs-human check, summaries; writes to `data/processed/` and `outputs/` |
