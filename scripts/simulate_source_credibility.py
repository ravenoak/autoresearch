#!/usr/bin/env python
"""Compare heuristic source credibility scores against a labeled dataset.

Usage:
    uv run scripts/simulate_source_credibility.py
"""

from __future__ import annotations

import re
from statistics import mean
from typing import Iterable, TypedDict


class Document(TypedDict):
    url: str


class LabeledDocument(Document):
    label: int


LABELED_DATASET: list[LabeledDocument] = [
    {"url": "https://en.wikipedia.org/wiki/Artificial_intelligence", "label": 1},
    {"url": "https://nih.gov/research", "label": 1},
    {"url": "https://dept.university.edu/paper", "label": 1},
    {"url": "https://unknown.io/blog", "label": 0},
    {"url": "https://random.xyz/info", "label": 0},
    {"url": "https://example.com/post", "label": 0},
]

AUTHORITY: dict[str, float] = {
    "wikipedia.org": 0.9,
    "nih.gov": 0.95,
    "edu": 0.8,
    "gov": 0.85,
}


def assess_source_credibility(documents: Iterable[Document]) -> list[float]:
    """Return heuristic credibility scores for each document."""
    scores: list[float] = []
    for doc in documents:
        url = doc.get("url", "")
        domain = ""
        match = re.search(r"https?://(?:www\.)?([^/]+)", url)
        if match:
            domain = match.group(1)
        score = 0.5
        if domain in AUTHORITY:
            score = AUTHORITY[domain]
        else:
            for suffix, value in AUTHORITY.items():
                if domain.endswith(suffix):
                    score = value
                    break
        scores.append(score)
    return scores


def score_dataset() -> list[tuple[int, float]]:
    """Return (label, score) pairs for the labeled dataset."""
    docs: list[Document] = [{"url": item["url"]} for item in LABELED_DATASET]
    scores = assess_source_credibility(docs)
    return [(item["label"], score) for item, score in zip(LABELED_DATASET, scores, strict=True)]


def main() -> None:
    pairs = score_dataset()
    positives = [s for label, s in pairs if label == 1]
    negatives = [s for label, s in pairs if label == 0]
    print(f"mean credible={mean(positives):.2f}")
    print(f"mean non_credible={mean(negatives):.2f}")
    for item, (_, score) in zip(LABELED_DATASET, pairs):
        print(f"{item['url']} label={item['label']} score={score:.2f}")


if __name__ == "__main__":
    main()
