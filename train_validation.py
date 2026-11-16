"""Shared validation-only runner. The registry owns model-specific candidates."""
import argparse
import csv
import hashlib
import itertools
import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, confusion_matrix, f1_score,
                             precision_recall_curve, precision_score, recall_score, roc_auc_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from budget_metrics import evaluate

BASE = Path(__file__).resolve().parent
SEED = 42


def lr_candidates():
    grid = itertools.product(('raw', 'log1p'), (.001, .01, .1, 1, 10, 100),
                             (None, 'balanced', {0: 1, 1: 2}))
    # Previously frozen baseline wins AP ties.
    baseline = ('raw', 10, 'balanced')
    for transform, c, weight in itertools.chain((baseline,), (v for v in grid if v != baseline)):
        transforms = [FunctionTransformer(np.log1p)] if transform == 'log1p' else []
        yield dict(transform=transform, C=c, class_weight=weight), make_pipeline(
            *transforms, StandardScaler(),
            LogisticRegression(C=c, class_weight=weight, solver='lbfgs', max_iter=5000, random_state=SEED))


def tree_candidates():
    for depth, leaf, weight in itertools.product((2,4,6,None), (5,15,30), (None,'balanced')):
        params = dict(max_depth=depth, min_samples_leaf=leaf, class_weight=weight)
        yield params, DecisionTreeClassifier(**params, random_state=SEED)


REGISTRY = {'logistic_regression': lr_candidates, 'decision_tree': tree_candidates}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(source):
    contract = json.loads((BASE/'contract.json').read_text(encoding='utf-8'))
    manifest = BASE/'splits.csv'
    split_hash = sha(manifest)
    expected = json.loads((BASE/'decision_tree/protocol.json').read_text(encoding='utf-8'))
    if sha(source) != contract['source_sha256'] or split_hash != expected['splits_sha256']:
        raise ValueError('Dataset or split manifest differs from frozen experiment')
    with manifest.open(encoding='utf-8-sig', newline='') as f:
        groups = {}
        for row in csv.DictReader(f):
            groups.setdefault(row['split'], []).append(row['commit_hash'])
    # Read only training/validation records into the feature and label arrays.
    ids = set(groups['train'] + groups['validation'])
    with source.open(encoding='utf-8-sig', newline='') as f:
        records = {r['commit_hash']: r for r in csv.DictReader(f) if r['commit_hash'] in ids}
    features = contract['features']

    def arrays(group):
        keys = groups[group]
        rows = [records[k] for k in keys]
        x = np.array([[float(r[k]) for k in features] for r in rows])
        y = np.array([int(r['is_bug_inducing']) for r in rows])
        assert len(rows) == contract['split']['groups'][group]['rows']
        assert np.isfinite(x).all() and (x >= 0).all() and set(y) == {0,1}
        return x, y

    return arrays('train'), arrays('validation'), groups['validation'], dict(
        contract_version=contract['version'], source_sha256=contract['source_sha256'],
        splits_sha256=split_hash, feature_order=features, seed=SEED,
        train_rows=len(groups['train']), validation_rows=len(groups['validation']),
        test_evaluated=False, sklearn_version=sklearn.__version__)


def train(name, train_data, validation, ids, metadata, out):
    xt, yt = train_data
    xv, yv = validation
    trials, best = [], None
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        for params, estimator in REGISTRY[name]():
            estimator.fit(xt, yt)
            score = estimator.predict_proba(xv)[:,1]
            ap = float(average_precision_score(yv, score))
            trials.append(dict(parameters=params, validation_ap=ap))
            if best is None or ap > best[0] + 1e-12:
                best = ap, estimator, score, params
    ap, model, score, params = best
    p, r, t = precision_recall_curve(yv, score)
    f = np.divide(2*p[:-1]*r[:-1], p[:-1]+r[:-1], out=np.zeros_like(t), where=(p[:-1]+r[:-1])>0)
    threshold = float(t[np.flatnonzero(f == f.max())[-1]])
    predicted = score >= threshold
    features = metadata['feature_order']
    effort = xv[:,features.index('la')] + xv[:,features.index('ld')]
    rows = [dict(commit_hash=i, label=int(y), score=float(s), prediction=int(z), effort=int(e))
            for i,y,s,z,e in zip(ids,yv,score,predicted,effort)]
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out/'model.joblib')
    np.testing.assert_allclose(joblib.load(out/'model.joblib').predict_proba(xv)[:,1], score, rtol=0, atol=1e-12)
    with (out/'validation_predictions.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return dict(**metadata, model=name, parameters=params, threshold=threshold,
                selection='Highest validation AP; ties retain first candidate; threshold maximizes validation F1, highest threshold breaks ties.',
                trials=trials, metrics=dict(ap=ap, roc_auc=float(roc_auc_score(yv,score)),
                precision=float(precision_score(yv,predicted,zero_division=0)), recall=float(recall_score(yv,predicted)),
                f1=float(f1_score(yv,predicted)), confusion_matrix=confusion_matrix(yv,predicted,labels=[0,1]).tolist(),
                budget=evaluate(rows)))


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--models', nargs='+', choices=list(REGISTRY), default=list(REGISTRY))
    parser.add_argument('--output', type=Path, default=BASE/'unified_validation')
    args = parser.parse_args()
    training, validation, ids, meta = load(args.source)
    reports = []
    for name in dict.fromkeys(args.models):
        out = args.output/name
        report = train(name, training, validation, ids, meta, out)
        save(out/'report.json', report)
        reports.append(dict(model=name, trials=len(report['trials']), threshold=report['threshold'],
                            parameters=report['parameters'], **report['metrics']))
    save(args.output/'comparison.json', dict(**meta, models=reports))
    print(json.dumps(reports))


if __name__ == '__main__':
    main()
