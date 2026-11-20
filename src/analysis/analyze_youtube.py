"""Validate, sample, and score local YouTube comments for descriptive analysis."""

import argparse
from collections import Counter, defaultdict
import csv
from datetime import UTC, datetime
from hashlib import sha256
import heapq
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory

TOPIC = re.compile(
    r"\b(?:space\s+(?:travel|exploration|flight|program|touris[mt])|spaceflight|"
    r"going\s+to\s+space|multi[-\s]?planetary|interplanetary|"
    r"mars\s+(?:colony|mission)|coloni[sz]e\s+mars|living\s+on\s+mars)\b",
    re.IGNORECASE,
)
LABELS = ("negative", "neutral", "positive")
MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_row(stream, row):
    stream.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_comments(path):
    seen = set()
    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            try:
                row = json.loads(line)
                record_id = row["record_id"]
                timestamp = datetime.fromisoformat(row["created_utc"])
                raw = row["text"]
                if (row["platform"] != "youtube" or not isinstance(record_id, str)
                        or not record_id or timestamp.tzinfo is None or not isinstance(raw, str)):
                    raise ValueError
            except (ValueError, TypeError, KeyError) as error:
                raise ValueError(f"Invalid YouTube record at line {number}") from error
            duplicate = record_id in seen
            seen.add(record_id)
            yield row, timestamp.astimezone(UTC), duplicate


def prepare(source, expected, output, per_stratum, seed, full):
    coverage = defaultdict(Counter)
    samples = defaultdict(list)
    repeats = set()
    unique = 0
    with (output / "candidates.jsonl").open("w", encoding="utf-8") if full else open(os.devnull, "w") as candidates:
        for row, timestamp, duplicate in read_comments(source):
            month = timestamp.strftime("%Y-%m")
            counts = coverage[month]
            counts["input_rows"] += 1
            if duplicate:
                counts["duplicate_ids"] += 1
                continue
            unique += 1
            text = row["text"].strip()
            if not text:
                counts["empty_text"] += 1
                continue
            record_id = row["record_id"]
            author, video = row.get("author_hash"), row.get("video_id")
            if author and video:
                digest = sha256(" ".join(text.casefold().split()).encode()).digest()
                identity = (author, video, digest)
                if identity in repeats:
                    counts["repeated_author_video_text"] += 1
                    continue
                repeats.add(identity)
            matched = bool(TOPIC.search(text))
            counts["phrase_match" if matched else "no_phrase_match"] += 1
            item = {"record_id": record_id, "month": month, "phrase_match": matched, "text": text}
            if full and matched:
                write_row(candidates, item)
            rank = -int.from_bytes(sha256(f"{seed}:{record_id}".encode()).digest())
            heap = samples[timestamp.year, matched]
            entry = (rank, record_id, item)
            if len(heap) < per_stratum:
                heapq.heappush(heap, entry)
            else:
                heapq.heappushpop(heap, entry)
    if unique != expected:
        raise ValueError(f"Coverage expects {expected:,} unique comments, found {unique:,}")
    sample = [item for stratum in sorted(samples) for _, _, item in sorted(samples[stratum], reverse=True)]
    write_json(output / "coverage.json", {
        "unique_records": unique, "seed": seed, "per_year_phrase_stratum": per_stratum,
        "annotation_rows": len(sample), "monthly": dict(sorted(coverage.items())),
    })
    with (output / "annotation_sample.jsonl").open("w", encoding="utf-8") as stream:
        for item in sample:
            write_row(stream, {**item, "human_relevance": None, "human_sentiment": None})
    return sample


def scores(items, model_name, revision):
    if model_name == "vader":
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        analyzer = SentimentIntensityAnalyzer()
        for item in items:
            value = analyzer.polarity_scores(item["text"])["compound"]
            label = "positive" if value >= 0.05 else "negative" if value <= -0.05 else "neutral"
            yield item, label, value
    else:
        from transformers import pipeline

        classify = pipeline("sentiment-analysis", model=MODEL, revision=revision, framework="pt")
        for item, result in zip(
            items, classify([item["text"] for item in items], truncation=True, batch_size=16), strict=True
        ):
            label = result["label"].lower()
            if label not in LABELS:
                raise ValueError(f"Unexpected RoBERTa label {label!r}")
            yield item, label, float(result["score"])


def score(items, output, model_name, revision, full):
    from langdetect import DetectorFactory, LangDetectException, detect

    DetectorFactory.seed = 0
    eligible = []
    language_counts = defaultdict(Counter)
    for item in items:
        try:
            language = detect(item["text"])
        except LangDetectException:
            language = "undetermined"
        language_counts[item["month"]][language] += 1
        if language == "en":
            eligible.append(item)
    monthly = defaultdict(Counter)
    with (output / "scores.jsonl").open("w", encoding="utf-8") as stream:
        for item, label, value in scores(eligible, model_name, revision):
            monthly[item["month"]][label] += 1
            write_row(stream, {k: v for k, v in item.items() if k != "text"} |
                      {"sentiment": label, "model_score": value})
    write_json(output / "scoring.json", {
        "scope": "phrase-matched English candidates" if full else "stratified pilot",
        "model": MODEL if model_name == "roberta" else model_name,
        "version": revision if model_name == "roberta" else version("vaderSentiment"),
        "score_type": "class probability" if model_name == "roberta" else "VADER compound",
        "language_detector": f"langdetect {version('langdetect')}",
        "language_counts_by_month": dict(sorted(language_counts.items())),
        "scored": sum(map(sum, (c.values() for c in monthly.values()))),
    })
    if not full:
        return
    with (output / "monthly_sentiment.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["month", "scored", *LABELS, *(f"{label}_share" for label in LABELS)])
        for month in sorted(language_counts):
            counts = monthly[month]
            total = sum(counts.values())
            writer.writerow([month, total, *(counts[label] for label in LABELS),
                             *(counts[label] / total if total else "" for label in LABELS)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--coverage", type=Path, required=True, help="Collector coverage JSON")
    parser.add_argument("--output", type=Path, required=True, help="New private output directory")
    parser.add_argument("--per-stratum", type=int, default=14, help="Pilot sample size per year and match group")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model", choices=("vader", "roberta"), default="vader")
    parser.add_argument("--revision", help="Hugging Face model commit SHA for RoBERTa")
    parser.add_argument("--score-all", action="store_true", help="Score all English phrase-matched candidates")
    args = parser.parse_args()
    if args.per_stratum < 1 or (args.model == "roberta" and not re.fullmatch("[0-9a-f]{40}", args.revision or "")):
        parser.error("provide a positive sample cap and, for RoBERTa, a 40-character model revision")
    if args.output.exists():
        parser.error("--output must be a new directory")
    os.umask(0o077)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    expected = json.loads(args.coverage.read_text(encoding="utf-8"))["unique_comments"]
    with TemporaryDirectory(dir=args.output.parent) as tmp:
        stage = Path(tmp) / "results"
        stage.mkdir(mode=0o700)
        sample = prepare(args.input, expected, stage, args.per_stratum, args.seed, args.score_all)
        if args.score_all:
            path = stage / "candidates.jsonl"
            with path.open(encoding="utf-8") as stream:
                score(map(json.loads, stream), stage, args.model, args.revision, True)
            path.unlink()
        else:
            score(sample, stage, args.model, args.revision, False)
        stage.rename(args.output)
    print(f"Verified {expected:,} unique comments. Wrote {len(sample)} annotation rows to {args.output}.")


if __name__ == "__main__":
    main()
