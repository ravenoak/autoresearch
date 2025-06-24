#!/usr/bin/env python
"""Optimize search ranking weights using evaluation data."""

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

import tomllib
import tomli_w


def load_data(path: Path):
    """Load evaluation data from CSV."""
    data = defaultdict(list)
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            q = row["query"]
            data[q].append(
                {
                    "bm25": float(row["bm25"]),
                    "semantic": float(row["semantic"]),
                    "credibility": float(row["credibility"]),
                    "relevance": float(row["relevance"]),
                }
            )
    return data


def ndcg(scores):
    """Compute normalized discounted cumulative gain."""
    dcg = sum((2 ** s - 1) / math.log2(i + 2) for i, s in enumerate(scores))
    ideal = sorted(scores, reverse=True)
    idcg = sum((2 ** s - 1) / math.log2(i + 2) for i, s in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def evaluate(weights, data):
    w_sem, w_bm, w_cred = weights
    total = 0.0
    for docs in data.values():
        preds = [w_sem * d["semantic"] + w_bm * d["bm25"] + w_cred * d["credibility"] for d in docs]
        # order predicted scores
        ranked = [docs[i]["relevance"] for i in sorted(range(len(docs)), key=lambda i: preds[i], reverse=True)]
        total += ndcg(ranked)
    return total / len(data)


def grid_search(data):
    best = 0.0
    best_w = (0.5, 0.3, 0.2)
    steps = [i / 10 for i in range(11)]
    for w_sem in steps:
        for w_bm in steps:
            w_cred = 1.0 - w_sem - w_bm
            if w_cred < 0 or w_cred > 1:
                continue
            score = evaluate((w_sem, w_bm, w_cred), data)
            if score > best:
                best = score
                best_w = (w_sem, w_bm, w_cred)
    return best_w, best


def update_config(cfg_path: Path, weights):
    data = tomllib.loads(cfg_path.read_text())
    data["search"]["semantic_similarity_weight"] = round(weights[0], 2)
    data["search"]["bm25_weight"] = round(weights[1], 2)
    data["search"]["source_credibility_weight"] = round(weights[2], 2)
    cfg_path.write_text(tomli_w.dumps(data))


def main():
    parser = argparse.ArgumentParser(description="Tune search ranking weights")
    parser.add_argument("dataset", type=Path, help="Path to evaluation CSV")
    parser.add_argument("config", type=Path, help="Path to config TOML to update")
    args = parser.parse_args()

    data = load_data(args.dataset)
    weights, score = grid_search(data)
    print(f"Best weights: semantic={weights[0]:.2f}, bm25={weights[1]:.2f}, cred={weights[2]:.2f} (NDCG={score:.3f})")
    update_config(args.config, weights)


if __name__ == "__main__":
    main()
