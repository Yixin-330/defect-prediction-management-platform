"""Evaluate two whole-commit review policies on saved predictions."""
import argparse
import csv
import json
from decimal import Decimal
from pathlib import Path


def evaluate(rows):
    ranked = sorted(rows, key=lambda row: -Decimal(row["score"]))
    costs = [Decimal(row["effort"]) for row in ranked]
    labels = [int(row["label"]) for row in ranked]
    if not ranked or any(not c.is_finite() or c <= 0 for c in costs) or not set(labels) <= {0, 1} or not sum(labels):
        raise ValueError("Expected positive finite effort and binary labels with at least one positive")
    budget = sum(costs) * Decimal("0.2")
    results = {}
    for policy in ("strict_prefix", "skip_over_budget"):
        spent = Decimal(0)
        reviewed = found = skipped = 0
        for cost, label in zip(costs, labels):
            if spent + cost > budget:
                if policy == "strict_prefix":
                    break
                skipped += 1
                continue
            spent += cost
            reviewed += 1
            found += label
        assert spent <= budget
        results[policy] = dict(reviewed=reviewed, found=found, spent=float(spent),
                               recall=found / sum(labels), skipped=skipped)
    return dict(budget=float(budget), positives=sum(labels), rows=len(rows),
                rule="Stable descending score; whole commits; skip if cost exceeds remaining budget and continue.",
                results=results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predictions", type=Path)
    args = parser.parse_args()
    with args.predictions.open(encoding="utf-8-sig", newline="") as stream:
        print(json.dumps(evaluate(list(csv.DictReader(stream))), indent=2))
