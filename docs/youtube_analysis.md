# YouTube sentiment analysis

Use the existing `youtube_comments_2016_2026.zip` from private Drive. Extract its JSONL and coverage JSON into the Git-ignored `data/interim/youtube_history/` directory. The analysis runs locally and does not need an API key.

```bash
python -m pip install vaderSentiment==3.3.2 langdetect==1.0.9

python src/analysis/analyze_youtube.py \
  data/interim/youtube_history/comments_2016_2026.jsonl \
  --coverage data/interim/youtube_history/collection_coverage.json \
  --output data/processed/youtube_pilot
```

The pilot verifies the unique record count and UTC timestamps, tallies monthly screening flags, and draws a reproducible sample of up to 14 comments per year in each of two groups. One group contains a project search phrase in the comment text, and the other does not. Exact repeated text by the same author on the same video is excluded from sample selection. The pipeline detects language in the selected comments and scores those it classifies as English.

- `coverage.json` lists input and screening counts by comment month.
- `annotation_sample.jsonl` contains the private review sample with blank `human_relevance` and `human_sentiment` fields.
- `scores.jsonl` contains pilot predictions and record IDs.
- `scoring.json` gives model versions and language counts.

During review, mark each comment's relevance to space travel independently of its sentiment. On relevant comments, assign `positive`, `neutral`, or `negative` using the sentiment plan. Review both phrase groups to catch false positives and missed relevant comments. Inspect the language filter on short comments and check model predictions against human labels before adopting a scoring rule. Pilot sentiment shares are unsuitable as population estimates because the two groups are deliberately sampled at similar sizes.

To compare RoBERTa on the identical pilot, install compatible versions of PyTorch and Transformers (for example, `torch==2.7.1` and `transformers==4.53.3`), use a new output directory, and add `--model roberta --revision MODEL_COMMIT_SHA`. Use the full commit SHA from the [model repository](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest). VADER reports a compound score. RoBERTa reports a class probability.

After reviewing the screen, use a new output directory and add `--score-all` to produce `monthly_sentiment.csv` for English comments matched by the phrase filter. Its denominator is the number scored in each month. Comment dates come from `created_utc`. The 2026 coverage is partial, and the study describes the collected sample. Keep row-level files and annotation text private.
