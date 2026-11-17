# Sentiment plan

## Labels

`positive`, `negative`, `neutral` — plus the model's confidence score.

## Models

Run more than one and compare, since social media text is hard for any single model:

1. **Lexicon baseline** — e.g. VADER (fast, built for social media, transparent).
2. **Transformer model** — a model trained on social media sentiment (e.g. a RoBERTa model fine-tuned on tweets).
3. **Optional: LLM labelling** on a subset, for comparison.

Record the exact model names and versions in `research_log.md`.

## Known difficulties

- Sarcasm and jokes ("great, another billionaire joyride").
- Sentiment is about the *text's tone*, not necessarily about space travel itself (e.g. angry at a regulator but excited about the launch).
- Long FAA comments may need splitting or truncation for transformer models.

## Checking

- Random sample of ~300 items, labelled by hand (two people on a shared subset if possible).
- Report agreement of each model with the hand labels (accuracy, per-class precision/recall).

## Outputs

- Overall sentiment distribution.
- By platform, by community/channel, by keyword group, over time.
- Examples of high-confidence positive/negative items (paraphrased, not quoted, if shared outside the team).
