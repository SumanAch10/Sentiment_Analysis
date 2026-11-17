# Instructions for Claude

You are helping Suman collect social media data about space travel and run sentiment analysis on it. Read `README.md` and the files in `docs/` first.

The task is **descriptive sentiment analysis only**. Do not add research questions, hypotheses, argument frames or interpretive coding unless Suman asks.

## Current phase

**Planning.** Do not write code until Suman says to start. Then implement **one step at a time** and stop for review after each.

## Steps

1. **Collect** (`src/collect/`): one collector per platform (Reddit, YouTube, Bluesky; X optional), using the keywords, communities and dates in `docs/collection_plan.md`. Save raw output to `data/raw/<platform>/` exactly as received.
2. **FAA ingestion** (`src/preprocess/`): load `data/raw/faa/FAA_All_Volumes_Compiled.xlsx` (sheet `Comments`), join the `Body*` columns into one text field, flag duplicate/template comments (don't delete them).
3. **Clean** (`src/preprocess/`): de-duplicate, filter spam and non-English text, convert all sources to `docs/data_schema.md`. Save to `data/interim/`.
4. **Sentiment** (`src/analysis/`): score every item as in `docs/sentiment_plan.md`. Save to `data/processed/`.
5. **Check**: draw a random sample into `annotation/sentiment_check_samples/` for hand labelling; once labelled, report agreement between model and humans.
6. **Summarise**: tables and figures in `outputs/`.

## Rules

- Never edit files in `data/raw/`; every step writes new files downstream.
- API keys in a git-ignored `.env`, read from environment variables. Never hard-code them.
- Keywords, communities, dates and model names in config files (e.g. `config/*.yaml`), matching `docs/collection_plan.md`.
- Hash usernames on ingestion (`docs/ethics.md`).
- Use official APIs and respect rate limits and platform terms.
- Pin package versions, set random seeds, and log query parameters and collection times.
- Add a dated entry to `docs/research_log.md` for each significant choice (keyword changes, model choice, filtering rules).
- Ask before making a choice that would change the results.

Python 3.11+.
