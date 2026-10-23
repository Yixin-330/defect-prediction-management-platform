"""Prepare JITMovingTarget CSVs and fit separate chronological LR baselines."""

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import warnings

import joblib
import numpy as np
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[3]
FEATURES = ["la", "ld", "nf", "nd", "ns", "ent", "ndev", "age", "nuc", "aexp", "asexp"]
VERSION = "jitmovingtarget-source11-v1"
WINDOWS = {"openstack": (1322599384, 1393590700), "qt": (1308350292, 1395090476)}
SOURCES = [
    "https://github.com/software-rebels/JITMovingTarget/blob/master/scripts/load_data.r",
    "https://github.com/software-rebels/JITMovingTarget/blob/master/scripts/experimental_settings.r",
    "https://posl.ait.kyushu-u.ac.jp/~kamei/publications/McIntosh_TSE2017.pdf",
]
LIMITATIONS = [
    "Offline archival benchmark only; not a production-ready 14-feature model.",
    "Blank bugcount becomes negative by source convention, not proof of no defect.",
    "Fix discovery dates and per-sample label availability are absent; historical label-time leakage cannot be ruled out.",
    "age retains source numeric units; conversion to seconds/days has not been verified.",
    "ent retains source bounded scale; no synthetic entropy or age conversion is applied.",
    "CSV cannot independently establish extraction as-of timing or reproduce SZZ labels.",
    "Missing history is unknown, not asserted to be zero history; train-only median imputation differs from source zero-fill.",
]


def dump_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def dump_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(value, name, blank_ok=False):
    if value is None:
        raise ValueError(f"missing cell: {name}")
    if value.strip() == "":
        if blank_ok:
            return None
        raise ValueError(f"blank: {name}")
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"nonfinite/negative: {name}")
    if name not in ("age", "ent") and not result.is_integer():
        raise ValueError(f"not integer count: {name}")
    return result


def split_rows(rows):
    """Keep equal timestamps together, moving each boundary to the right."""
    rows = sorted(rows, key=lambda row: (row["author_date"], row["commit_sha"]))
    boundaries = []
    for fraction in (0.7, 0.85):
        position = int(len(rows) * fraction)
        while 0 < position < len(rows) and rows[position - 1]["author_date"] == rows[position]["author_date"]:
            position += 1
        boundaries.append(position)
    a, b = boundaries
    if not 0 < a < b < len(rows):
        raise ValueError("Cannot form three nonempty strict time intervals")
    for i, row in enumerate(rows):
        row["split"] = "train" if i < a else ("validation" if i < b else "test")
    return rows


def prepare(path, project):
    start, end = WINDOWS[project]
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"commit_id", "author_date", "bugcount", "fixcount", *FEATURES}
        if len(reader.fieldnames or []) != len(set(reader.fieldnames or [])):
            raise ValueError("Duplicate header names")
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Missing columns: {sorted(required - set(reader.fieldnames or []))}")
        raw = list(reader)
    counts, rejected, rows, ids = Counter(), [], [], set()
    for line, record in enumerate(raw, 2):
        try:
            if None in record or any(v is None for v in record.values()):
                raise ValueError("wrong CSV column count")
            sha = record["commit_id"]
            if not re.fullmatch(r"[0-9a-f]{40}", sha):
                raise ValueError("invalid commit_id")
            if sha in ids:
                raise ValueError("duplicate commit_id")
            ids.add(sha)
            timestamp = int(number(record["author_date"], "author_date"))
            la, ld, nf = (number(record[key], key) for key in ("la", "ld", "nf"))
            reason = ("outside_source_time_window" if not start <= timestamp < end else
                      "no_added_lines" if la == 0 else
                      "churn_over_10000" if la + ld > 10000 else
                      "files_over_100" if nf > 100 else None)
            if reason:
                counts[reason] += 1
                rejected.append({"source_line": line, "commit_sha": sha, "reason": reason})
                continue
            features = {key: number(record[key], key, blank_ok=key not in ("la", "ld", "nf", "nd", "ns", "ent")) for key in FEATURES}
            if not (1 <= features["ns"] <= nf and 1 <= features["nd"] <= nf):
                raise ValueError("invalid ns/nd relative to nf")
            # Source subsystem/directory grouping need not form our assumed hierarchy.
            # Preserve these observations, flag them rather than inventing values.
            if features["ns"] > features["nd"]:
                counts["source_ns_greater_than_nd_preserved"] += 1
            if features["ent"] > 1 + 1e-12:
                raise ValueError("entropy out of source [0,1] scale")
            if features["ent"] > 1:
                features["ent"] = 1.0
                counts["entropy_roundoff_clipped"] += 1
            bugcount = number(record["bugcount"], "bugcount", blank_ok=True)
            fixcount = number(record["fixcount"], "fixcount", blank_ok=True)
            counts["blank_bugcount_to_negative"] += bugcount is None
            counts["blank_fixcount_to_false"] += fixcount is None
            counts["rows_with_missing_features"] += any(v is None for v in features.values())
            rows.append({"project_id": project, "commit_sha": sha, "author_date": timestamp,
                         "committed_at": datetime.fromtimestamp(timestamp, timezone.utc).isoformat(),
                         "feature_schema_version": VERSION,
                         **{k: "" if v is None else v for k, v in features.items()},
                         "is_bug_inducing": int((bugcount or 0) > 0),
                         "fix_audit_only": int((fixcount or 0) > 0),
                         "label_was_blank": int(bugcount is None),
                         "effort": int(la + ld)})
        except (ValueError, TypeError, OverflowError) as error:
            # Malformed retained records must be reviewed, never silently recoded.
            raise ValueError(f"{path.name}:{line}: {error}") from error
    if not rows:
        raise ValueError("No eligible records")
    rows = split_rows(rows)
    return rows, rejected, {"raw_rows": len(raw), "retained_rows": len(rows),
                            "excluded_rows": len(rejected), "counts": dict(counts)}


def matrix(rows):
    return np.array([[np.nan if r[k] == "" else float(r[k]) for k in FEATURES] for r in rows])


def score_metrics(y, scores, effort):
    predicted = scores >= 0.5
    order = np.argsort(-scores, kind="stable")
    inspected = order[np.cumsum(effort[order]) <= effort.sum() * 0.2]
    return {"roc_auc": float(roc_auc_score(y, scores)),
            "average_precision": float(average_precision_score(y, scores)),
            "precision_at_0_5": float(precision_score(y, predicted, zero_division=0)),
            "recall_at_0_5": float(recall_score(y, predicted, zero_division=0)),
            "f1_at_0_5": float(f1_score(y, predicted, zero_division=0)),
            "confusion_matrix_0_1": confusion_matrix(y, predicted, labels=[0, 1]).tolist(),
            "recall_at_20_percent_effort": float(y[inspected].sum() / y.sum()),
            "actual_effort_fraction": float(effort[inspected].sum() / effort.sum()),
            "effort_ranking": "descending risk, stable ties, whole-commit prefix within budget"}


def train(rows, output, seed):
    x, y = matrix(rows), np.array([r["is_bug_inducing"] for r in rows])
    indices = {name: np.array([i for i, r in enumerate(rows) if r["split"] == name])
               for name in ("train", "validation", "test")}
    training = indices["train"]
    for name, ix in indices.items():
        if len(np.unique(y[ix])) != 2:
            raise ValueError(f"{name}: both labels required for evaluation")
    if np.any(np.all(np.isnan(x[training]), axis=0)):
        raise ValueError("All-missing training feature: cannot fit median")
    model = make_pipeline(SimpleImputer(strategy="median", add_indicator=True),
                          StandardScaler(), LogisticRegression(C=1.0, solver="lbfgs", max_iter=5000, random_state=seed))
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        model.fit(x[training], y[training])
    np.testing.assert_allclose(model[0].statistics_, np.nanmedian(x[training], axis=0))
    scores = model.predict_proba(x)[:, list(model.classes_).index(1)]
    model_path = output / "model.joblib"
    joblib.dump(model, model_path)
    loaded = joblib.load(model_path)
    np.testing.assert_allclose(loaded.predict_proba(x)[:, 1], scores, rtol=0, atol=1e-12)
    metrics = {}
    for name, ix in indices.items():
        selected = [rows[i] for i in ix]
        metrics[name] = {"rows": len(ix), "positive": int(y[ix].sum()),
                         "positive_fraction": float(y[ix].mean()),
                         "from": selected[0]["committed_at"], "to": selected[-1]["committed_at"],
                         "missing_by_feature": {k: int(np.isnan(x[ix, j]).sum()) for j, k in enumerate(FEATURES)},
                         **score_metrics(y[ix], scores[ix], np.array([r["effort"] for r in selected]))}
    dump_csv(output / "test_predictions.csv", [
        {"project_id": rows[i]["project_id"], "commit_sha": rows[i]["commit_sha"],
         "committed_at": rows[i]["committed_at"], "label": int(y[i]),
         "risk_score": float(scores[i]), "predicted_label": int(scores[i] >= 0.5)} for i in indices["test"]])
    dump_json(output / "metrics.json", metrics)
    dump_json(output / "model_metadata.json", {
        "feature_schema_version": VERSION, "feature_order": FEATURES, "seed": seed,
        "parameters": model[-1].get_params(), "classification_threshold": 0.5,
        "priority_thresholds": None, "class_weight": None,
        "preprocessing": "train-only median + train-observed missing indicators + StandardScaler",
        "imputer_statistics": model[0].statistics_.tolist(),
        "indicator_features": [FEATURES[i] for i in model[0].indicator_.features_],
        "source_feature_units": {"age": "unverified source unit (no conversion)", "ent": "source bounded scale [0,1]"},
        "model_sha256": digest(model_path),
        "training_input_sha256": digest(output / "samples.csv"),
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "scikit-learn": sklearn.__version__, "joblib": joblib.__version__},
        "limitations": LIMITATIONS,
    })
    return metrics


def run(project, source_dir, output_root, seed):
    source = source_dir / f"{project}.csv"
    before = digest(source)
    rows, rejected, audit = prepare(source, project)
    output = output_root / project
    output.mkdir(parents=True, exist_ok=True)
    dump_csv(output / "samples.csv", rows)
    if rejected:
        dump_csv(output / "excluded_rows.csv", rejected)
    dump_csv(output / "splits.csv", [{k: r[k] for k in ("project_id", "commit_sha", "author_date", "split")} for r in rows])
    dump_json(output / "feature_schema.json", {
        "version": VERSION, "feature_order": FEATURES,
        "fields": {k: {"source": k, "unit": "source numeric time unit, unverified" if k == "age" else
                        "source bounded entropy" if k == "ent" else "count",
                        "missing": "preserve blank; train-only median and indicator"} for k in FEATURES},
        "excluded_from_X": ["commit_id", "author_date", "bugcount", "fixcount", "fix_audit_only", "label_was_blank", "effort", "rexp", "arexp", "lt", "review metrics"],
        "mapping_notes": {"aexp": "author experience; do not map reviewer rexp to author recent experience",
                          "asexp": "author subsystem experience", "arexp": "not used; relative/recent naming ambiguity not inferred",
                          "lt": "absent; never filled with fabricated zeros"},
    })
    metrics = train(rows, output, seed)
    if digest(source) != before:
        raise RuntimeError("Source file changed during experiment")
    dump_json(output / "dataset_manifest.json", {
        "project": project, "source_file": str(source.resolve()), "source_sha256": before,
        "feature_schema_version": VERSION, "sources": SOURCES, "audit": audit,
        "source_window_unix_start_inclusive_end_exclusive": WINDOWS[project],
        "filter": "source window; la>0; la+ld<=10000; nf<=100",
        "label": "int((bugcount or 0)>0), per source benchmark convention",
        "label_cutoff_at": None, "label_cutoff_note": "Not provided by CSV; not inferred from last commit date",
        "split": "chronological approx 70/15/15, equal timestamps kept together",
        "no_test_resampling": True, "no_parameter_search": True,
        "limitations": LIMITATIONS,
    })
    lines = [f"# {project} 真实数据清洗与逻辑回归实验", "",
             f"原始 {audit['raw_rows']} 条；保留 {len(rows)} 条；筛除 {len(rejected)} 条。原文件 SHA256 已检查未变。",
             "", "| 划分 | 样本 | 正例 | ROC-AUC | AP | F1@0.5 | Recall@20% effort |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for name, values in metrics.items():
        lines.append(f"| {name} | {values['rows']} | {values['positive']} | {values['roc_auc']:.4f} | "
                     f"{values['average_precision']:.4f} | {values['f1_at_0_5']:.4f} | {values['recall_at_20_percent_effort']:.4f} |")
    lines += ["", "阈值固定 0.5；未调参，未重采样；工作量为 la+ld，按风险降序检查完整提交。",
              "缺失值按训练集的中位数填补并添加训练时发现的缺失标记，标准化也仅拟合训练集。",
              "采用独立11维源数据契约，age保留源尺度，不能宣称与线上14维特征一致。",
              "这是归档数据时间留出评估；缺少标签发现日期，不能证明历史标签在训练时已可获得。", "",
              "限制：", *[f"- {item}" for item in LIMITATIONS], "", "来源：", *[f"- {url}" for url in SOURCES]]
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"project": project, "retained": len(rows), "test": metrics["test"]}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=[*WINDOWS, "all"], default="all")
    parser.add_argument("--source-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "artifacts")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.source_dir.resolve() == args.output.resolve():
        parser.error("Output must differ from source directory")
    for project in WINDOWS if args.project == "all" else [args.project]:
        run(project, args.source_dir, args.output, args.seed)
