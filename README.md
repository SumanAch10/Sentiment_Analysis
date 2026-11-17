# Public Sentiment on Space Travel

**Goal:** collect public posts and comments about space travel and becoming multiplanetary, and measure their sentiment (positive / negative / neutral).

This is a first, descriptive step. Nothing here is tied to a research question yet; once the sentiment results are in, we decide where to dig deeper.

**Team:** Suman (lead, AIT_Lab), Dr Das (advisor), Claude (collaborator)

## Data sources

| Source | Status |
|---|---|
| Reddit | Planned |
| YouTube comments | Planned |
| Bluesky | Planned |
| X / Twitter | Optional (API cost) |
| FAA 2021 public comments on SpaceX Starship/Super Heavy, Boca Chica (~17,000) | In hand |

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
│   └── research_log.md        dated notes and decisions
├── data/
│   ├── raw/{reddit,youtube,bluesky,faa}/   data as collected (never edited)
│   ├── interim/               cleaned, unified
│   └── processed/             with sentiment scores
├── annotation/
│   ├── sentiment_check_samples/   samples for hand-checking
│   └── sentiment_check_labels/    hand labels
├── src/                       code (not yet implemented)
├── notebooks/                 exploration
└── outputs/{figures,tables}/  results
```

## Status

Planning only — no code yet. Next: review `docs/collection_plan.md` and `docs/sentiment_plan.md`, then start collection.
