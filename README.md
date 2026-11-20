# Public Sentiment on Space Travel

**Goal:** collect public posts and comments about space travel and becoming multiplanetary, and measure their sentiment (positive / negative / neutral).

This is a first, descriptive step. Nothing here is tied to a research question yet; once the sentiment results are in, we decide where to dig deeper.

**Team:** Suman (lead, AIT_Lab), Dr Das (advisor), Claude (collaborator)

## Data sources

| Source | Status |
|---|---|
| Reddit | Collection pending research data access |
| YouTube comments | Collected 209,096 unique top-level comments from videos uploaded in 2016–2026. |
| Bluesky | Collected 10,160 unique posts across 34 months, January 2024–October 2026 UTC. |
| X / Twitter | Optional (API cost) |
| FAA 2021 public comments on SpaceX Starship/Super Heavy, Boca Chica (~17,000) | Previously obtained separately |

The YouTube and Bluesky datasets are available as private Google Drive archives. YouTube comments were collected from relevance-ranked video searches and capped, newest-first comment pages. Bluesky posts were collected from capped monthly keyword searches. See the [YouTube collection guide](docs/youtube_history.md) and [research log](docs/research_log.md) for sampling details.

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

## Agent handoff

The next task is to prepare and validate the existing YouTube and Bluesky samples for descriptive sentiment and trend analysis. Start with the two archives in the project owner's private Google Drive. Use the owner's supplied files or authorized Drive access.

| Archive | Data file | Coverage files |
|---|---|---|
| `youtube_comments_2016_2026.zip` | `comments_2016_2026.jsonl` | `collection_coverage.json` |
| `bluesky_posts_2024_2026.zip` | `bluesky_history.jsonl` | `monthly_coverage.csv`, `yearly_coverage.csv` |

1. **Verify inputs.** Read [the schema](docs/data_schema.md) and [data handling rules](docs/ethics.md). Extract to Git-ignored storage. Check valid JSONL, unique `record_id` values within each platform, UTC timestamps, nonempty text, and counts against the coverage files (209,096 YouTube rows and 10,160 Bluesky rows). Report any discrepancies. Preserve the original archives.
2. **Prepare the sample.** Flag off-topic records, non-English text, spam, and duplicate text using documented rules. YouTube search terms matched videos, so the comments still need relevance screening. Keep counts of included and excluded rows by platform and month. Pilot the screening before applying it at scale.
3. **Validate sentiment.** Draw a reproducible sample of about 300 records across platforms, years, and topics for human review. Label relevance separately from sentiment and include examples where the tone of a post differs from its attitude toward space travel. Compare VADER and CardiffNLP Twitter-RoBERTa with human labels. Report accuracy and per-class precision and recall. Use the [sentiment plan](docs/sentiment_plan.md) and log model versions and labeling decisions.
4. **Analyze the trend.** Group by the UTC `created_utc` field. YouTube's `video_published_utc` is the video upload date and can be used to check coverage by upload cohort. Show monthly positive, neutral, and negative shares with denominators for each platform. Treat YouTube's 2026 data as partial. Use March 2024 onward for the main Bluesky trend and retain January and February 2024 as context. For comparisons across years, use matched calendar months. Describe the results as trends in the collected samples.
5. **Save reproducible outputs.** Put row-level scores in Git-ignored `data/processed/`. Save aggregate tables and figures in `outputs/tables/` and `outputs/figures/`. Record the commands, exclusions, and coverage limits in the [research log](docs/research_log.md). Keep comment text, identifiers, private Drive links, and credentials out of GitHub.

Begin with an input coverage report and a pilot screening and annotation plan. Bring decisions that affect the results to Suman for review before full scoring. Reddit collection is pending research access, and the FAA data was obtained separately. The RoBERTa demo currently uses sample text.
