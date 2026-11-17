"""Try three-way sentiment classification on sample space-travel comments.

Install with: python -m pip install 'transformers<5' torch
Run from the repository root: python src/analysis/roberta_sentiment_demo.py
The first run downloads the model from Hugging Face.
"""

from transformers import pipeline


def main():
    classify = pipeline(
        "sentiment-analysis",
        model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    )
    comments = [
        "I'd love to travel to space someday.",
        "Space tourism is a waste of money.",
        "The launch is scheduled for Friday.",
    ]

    for comment, result in zip(comments, classify(comments, truncation=True)):
        print(f"{result['label']:8} {result['score']:.2f}  {comment}")


if __name__ == "__main__":
    main()
