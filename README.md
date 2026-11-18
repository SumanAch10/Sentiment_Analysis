# Public Sentiment on Space Travel

**Goal:** collect public posts and comments about space travel and becoming multiplanetary, and measure their sentiment (positive / negative / neutral).

This is a first, descriptive step. Nothing here is tied to a research question yet; once the sentiment results are in, we decide where to dig deeper.

**Team:** Suman (lead, AIT_Lab), Dr Das (advisor), Claude (collaborator)

## Data sources

| Source | Status |
|---|---|
| Reddit | Collection pending research data access |
| YouTube comments | Local collector ready for 2016–2026. Live collection pending. |
| Bluesky | Collected 10,160 unique posts across 34 months, January 2024–October 2026 UTC. |
| X / Twitter | Optional (API cost) |
| FAA 2021 public comments on SpaceX Starship/Super Heavy, Boca Chica (~17,000) | Previously obtained separately |

Bluesky is the only social platform collected through this project so far. The 10,160 posts come from monthly keyword searches and are stored outside GitHub. January and February 2024 provide context before and during the transition to public sign-ups. The proposed main Bluesky trend starts in March 2024. See the [research log](docs/research_log.md) for sampling details.

## Run YouTube collection locally

Use Python 3.11 or newer. Create a local `.env` file next to `.gitignore` with `YOUTUBE_API_KEY` and a stable `COLLECTION_AUTHOR_SALT`. The script reads it automatically and Git ignores it.

```bash
python src/collect/collect_youtube_history.py --video-years 2016
```

This starts with videos uploaded in 2016. The collection records each comment's posting date separately for trend analysis. Runs write to the Git-ignored `data/interim/youtube_history/` directory on the local machine. See the [YouTube setup and batching guide](docs/youtube_history.md) for all years through 2026.

## Pipeline

1. **Collect** posts/comments with the keywords and sources in `docs/collection_plan.md`.
2. **Clean** — remove duplicates, spam and non-English text; convert to one format (`docs/data_schema.md`).
3. **Sentiment** — score every item (`docs/sentiment_plan.md`).
4. **Check** — hand-label a small sample to see how well the model does.
5. **Summarise** — sentiment distribution overall and by platform, community, topic and time.

## Folder structure

```
sentiment_analysis/
├── README.md
├── CLAUDE.md                  instructions for Claude when implementing
├── docs/
│   ├── collection_plan.md     platforms, keywords, communities, dates, fields
│   ├── sentiment_plan.md      models, checking, outputs
│   ├── data_schema.md         common record format
│   ├── ethics.md              data ethics and platform terms
│   ├── youtube_history.md     local YouTube collection guide
│   └── research_log.md        dated notes and decisions
├── data/
│   ├── raw/{reddit,youtube,bluesky,faa}/   data as collected (never edited)
│   ├── interim/               cleaned, unified
│   └── processed/             with sentiment scores
├── annotation/
│   ├── sentiment_check_samples/   samples for hand-checking
│   └── sentiment_check_labels/    hand labels
├── src/                       collectors and sentiment demo
├── notebooks/                 exploration
└── outputs/{figures,tables}/  results
```

## Status

Historical Bluesky collection is complete for the listed window. The YouTube collector is ready for its first local run, and Reddit collection is pending access. The RoBERTa demo uses sample text. Sentiment scoring of the collected dataset is pending.
