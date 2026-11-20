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

## Analyze YouTube comments

Use the [YouTube analysis guide](docs/youtube_analysis.md) to validate the existing archive, generate a private labeling sample, and run the sentiment pilot locally. The pipeline reads the collected files and groups results by comment posting month.

## Agent handoff

**Assignment.** Analyze the existing YouTube comments to describe how sentiment about space travel changed from 2016 through 2026. Use the [existing analysis pipeline](docs/youtube_analysis.md). This assignment is limited to YouTube.

### Inputs

Use `youtube_comments_2016_2026.zip` from Suman's private Google Drive. Extract `comments_2016_2026.jsonl` and `collection_coverage.json` to Git-ignored `data/interim/youtube_history/`. Expect **209,096 unique top-level comments**. Read the [schema](docs/data_schema.md), [ethics rules](docs/ethics.md), and [sentiment plan](docs/sentiment_plan.md).

### Run the pilot

Use Python 3.11 or newer and a fresh output directory. The existing pipeline runs locally.

```bash
python -m pip install vaderSentiment==3.3.2 langdetect==1.0.9
python src/analysis/analyze_youtube.py \
  data/interim/youtube_history/comments_2016_2026.jsonl \
  --coverage data/interim/youtube_history/collection_coverage.json \
  --output data/processed/youtube_pilot
```

1. **Check coverage.** Verify the record count, UTC timestamps, IDs, and monthly counts. Review exclusions and explain any discrepancies. Use `created_utc` as the comment date. Use `video_published_utc` only to assess coverage by video upload cohort.
2. **Review relevance.** The collector matched keywords against videos. Review the stratified annotation sample, including comments without direct phrase matches, for relevance to space travel. Check the English filter on short, multilingual, and ambiguous comments. Report how many records each filter retains by month.
3. **Validate the models.** Run **VADER 3.3.2** as the baseline. Run **CardiffNLP Twitter-RoBERTa** on the same pilot using the pinned model revision and a separate output directory, as described in the analysis guide. Ask Suman for human labels or coordinate human review. Keep relevance separate from positive, neutral, and negative sentiment toward space travel. Compare models on the same human-labeled relevant records and report sample size, accuracy, per-class precision and recall, and examples of disagreement in paraphrase. If labels are unavailable, report that validation is pending.
4. **Review the pilot before full scoring.** Give Suman the coverage report, proposed screening rule, and any available validation results. The existing `--score-all` mode scores English comments that match the phrase filter. Treat that as a narrower subset unless the review supports applying the rule more broadly.

### Full-run outputs after review

- Produce a monthly CSV and trend chart with positive, neutral, and negative shares and the number of comments scored per month. Use 2016–2025 for complete-year comparisons and show 2026 as partial. Use matched calendar months for any comparison that includes 2026.
- Describe the findings as sentiment in the sampled YouTube comments. Document keyword-based video selection, newest-first comment caps, and screening exclusions.
- Save row-level scores and annotations in Git-ignored storage. Save aggregate CSVs and figures under `outputs/tables/` and `outputs/figures/`. Record the commands, model versions, sample seed, and decisions in the [research log](docs/research_log.md). Keep credentials, private Drive links, and comment text out of GitHub.
