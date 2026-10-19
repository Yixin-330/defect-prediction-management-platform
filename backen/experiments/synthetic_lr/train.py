"""Reproducible synthetic-only logistic regression smoke experiment."""

import argparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import platform
import warnings

import joblib
import numpy as np
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score, confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


FEATURES = [
    "ns", "nd", "nf", "entropy", "la", "ld", "lt", "fix",
    "ndev", "age", "nuc", "exp", "rexp", "sexp",
]
SCHEMA_VERSION = "synthetic-kamei14-v1"
NOTICE = "SYNTHETIC ONLY: labels are simulated, not SZZ; metrics do not measure real defect prediction."


def generate_rows(size, seed):
    """Plausible feature ranges, without pretending to reconstruct Git history."""
    rng = np.random.default_rng(seed)
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    rows = []
    for i in range(size):
        nf = int(rng.integers(1, 16))
        nd = int(rng.integers(1, nf + 1))
        ns = int(rng.integers(1, nd + 1))
        # Every changed file receives >=1 changed line; entropy follows those counts.
        changes = rng.poisson(rng.lognormal(2.0, 0.7), nf) + 1
        additions = rng.binomial(changes, 0.65)
        deletions = changes - additions
        la, ld = int(additions.sum()), int(deletions.sum())
        p = changes / changes.sum()
        entropy = float(-np.sum(p * np.log2(p)))
        exp = int(rng.integers(0, 301))
        nuc = int(rng.integers(0, 201))
        ndev = int(rng.integers(1, min(nuc, 15) + 1)) if nuc else 0
        age = float(rng.exponential(25)) if nuc else 0.0
        fix = int(rng.random() < 0.25)
        rexp = float(exp * rng.uniform(0.1, 1.0))
        sexp = int(rng.integers(0, exp + 1))
        lt = int(ld + rng.integers(0, 700) * nf)
        # Deliberately artificial noisy relationship; never exported as a feature.
        logit = (-2.8 + 0.5 * np.log1p(la + ld) + 0.12 * nf
                 + 0.35 * fix - 0.006 * exp - 0.12 * np.log1p(age))
        label = int(rng.random() < 1 / (1 + np.exp(-logit)))
        values = [ns, nd, nf, entropy, la, ld, lt, fix,
                  ndev, age, nuc, exp, rexp, sexp]
        row = {
            "project_id": "synthetic-demo",
            "commit_sha": hashlib.sha1(f"synthetic:{seed}:{i}".encode()).hexdigest(),
            "committed_at": (start + timedelta(hours=i)).isoformat(),
            "feature_schema_version": SCHEMA_VERSION,
            "label_method": "synthetic-bernoulli-v1",
            **dict(zip(FEATURES, values)),
            "is_bug_inducing": label,
            "effort": la + ld,
            "split": "train" if i < int(size * 0.7) else (
                "validation" if i < int(size * 0.85) else "test"),
        }
        rows.append(row)
    return rows


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def evaluate(y, scores, effort):
    predicted = scores >= 0.5
    # Risk-first ranking, stable ties. Whole commits only, no fractional inspection.
    order = np.argsort(-scores, kind="stable")
    cumulative = np.cumsum(effort[order])
    inspected = order[cumulative <= effort.sum() * 0.2]
    return {
        "effort_unaware": {
            "roc_auc": float(roc_auc_score(y, scores)),
            "average_precision": float(average_precision_score(y, scores)),
            "precision_at_0_5": float(precision_score(y, predicted, zero_division=0)),
            "recall_at_0_5": float(recall_score(y, predicted, zero_division=0)),
            "f1_at_0_5": float(f1_score(y, predicted, zero_division=0)),
            "confusion_matrix_labels_0_1": confusion_matrix(y, predicted, labels=[0, 1]).tolist(),
        },
        "effort_aware": {
            "recall_at_20_percent_effort": float(y[inspected].sum() / y.sum()),
            "actual_effort_fraction": float(effort[inspected].sum() / effort.sum()),
            "inspected_commits": int(len(inspected)),
            "ranking": "risk_score descending; whole-commit prefix within budget",
        },
    }


def run(size, seed, output):
    rows = generate_rows(size, seed)
    x = np.array([[row[name] for name in FEATURES] for row in rows], dtype=float)
    y = np.array([row["is_bug_inducing"] for row in rows])
    effort = np.array([row["effort"] for row in rows])
    split_indices = {name: np.array([i for i, r in enumerate(rows) if r["split"] == name])
                     for name in ("train", "validation", "test")}
    for name, indices in split_indices.items():
        if len(np.unique(y[indices])) != 2:
            raise ValueError(f"{name} must contain both classes; increase --samples or change --seed")
    train, validation, test = split_indices.values()
    if not (rows[train[-1]]["committed_at"] < rows[validation[0]]["committed_at"]
            and rows[validation[-1]]["committed_at"] < rows[test[0]]["committed_at"]):
        raise ValueError("Time split overlap")
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        model = make_pipeline(StandardScaler(), LogisticRegression(
            C=1.0, solver="lbfgs", max_iter=2000, random_state=seed))
        model.fit(x[train], y[train])
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "samples.csv", rows)
    write_csv(output / "splits.csv", [
        {k: r[k] for k in ("project_id", "commit_sha", "committed_at", "split")} for r in rows])
    joblib.dump(model, output / "model.joblib")
    restored = joblib.load(output / "model.joblib")
    scores = model.predict_proba(x)[:, list(model.classes_).index(1)]
    np.testing.assert_allclose(restored.predict_proba(x[test])[:, 1], scores[test], rtol=0, atol=1e-12)
    np.testing.assert_allclose(model[0].mean_, x[train].mean(axis=0))
    report = {"notice": NOTICE, "decision_threshold": 0.5,
              "threshold_note": "Fixed experiment threshold, not a product priority threshold.",
              "splits": {}}
    for name, indices in split_indices.items():
        report["splits"][name] = {
            "samples": len(indices), "positive": int(y[indices].sum()),
            "negative": int(len(indices) - y[indices].sum()),
            "from": rows[indices[0]]["committed_at"],
            "to": rows[indices[-1]]["committed_at"],
            **evaluate(y[indices], scores[indices], effort[indices]),
        }
    write_json(output / "metrics.json", report)
    write_json(output / "metadata.json", {
        "notice": NOTICE, "model_id": "synthetic-logistic-regression",
        "model_version": "demo-v1", "feature_schema_version": SCHEMA_VERSION,
        "feature_order": FEATURES, "seed": seed, "sample_count": size,
        "dataset_sha256": hashlib.sha256((output / "samples.csv").read_bytes()).hexdigest(),
        "model_sha256": hashlib.sha256((output / "model.joblib").read_bytes()).hexdigest(),
        "split": "chronological 70/15/15; no shuffle",
        "preprocessing": "StandardScaler fitted on training data only; bundled in model.joblib",
        "parameters": model[-1].get_params(),
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "scikit-learn": sklearn.__version__, "joblib": joblib.__version__},
        "priority_thresholds": None,
        "explanation": {"available": False, "reason": "Not implemented in this experiment"},
    })
    write_json(output / "sample_prediction.json", {
        "notice": NOTICE, "feature_schema_version": SCHEMA_VERSION,
        "input": {"project_id": rows[test[0]]["project_id"],
                  "commit_sha": rows[test[0]]["commit_sha"],
                  "features": {name: rows[test[0]][name] for name in FEATURES}},
        "risk_score": float(scores[test[0]]),
        "explanation": {"available": False, "reason": "Not implemented", "contributions": None},
    })
    write_csv(output / "test_predictions.csv", [
        {"commit_sha": rows[i]["commit_sha"], "label": int(y[i]),
         "risk_score": float(scores[i]), "predicted_label": int(scores[i] >= 0.5),
         "effort": int(effort[i])} for i in test])
    lines = ["# 模拟数据逻辑回归实验", "", NOTICE, "",
             "标签由人工设定的概率规则生成，不是 SZZ 结果。仅验证生成、划分、训练、评估与保存流程。",
             "", "| 划分 | 样本 | 正例 | ROC-AUC | AP | F1@0.5 | Recall@20% effort |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for name, result in report["splits"].items():
        u, a = result["effort_unaware"], result["effort_aware"]
        lines.append(f"| {name} | {result['samples']} | {result['positive']} | "
                     f"{u['roc_auc']:.4f} | {u['average_precision']:.4f} | "
                     f"{u['f1_at_0_5']:.4f} | {a['recall_at_20_percent_effort']:.4f} |")
    lines += ["", "工作量定义为 la+ld；按风险降序检查完整提交，累计工作量不超过总量的20%。",
              "0.5 为固定实验分类阈值，未进行调参，也未定义产品优先级。",
              "已检查保存后模型预测一致、标准化均值仅来自训练集。"]
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "notice": NOTICE,
                      "test": report["splits"]["test"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "artifacts")
    args = parser.parse_args()
    if args.samples < 200:
        parser.error("--samples must be at least 200 for this demonstration")
    run(args.samples, args.seed, args.output.resolve())
