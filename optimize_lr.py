import csv
import hashlib
import json
import sys
import warnings
from pathlib import Path

import joblib
import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_curve, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from budget_metrics import evaluate

base = Path(__file__).resolve().parent
source = Path(sys.argv[1])
contract = json.loads((base / 'contract.json').read_text(encoding='utf-8'))
assert hashlib.sha256(source.read_bytes()).hexdigest() == contract['source_sha256']
with source.open(encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))
data = {r['commit_hash']: r for r in rows}
with (base / 'splits.csv').open(encoding='utf-8', newline='') as f:
    splits = list(csv.DictReader(f))
assert len(data) == len(rows) == len(splits) == len({r['commit_hash'] for r in splits})
assert set(data) == {r['commit_hash'] for r in splits}
features = contract['features']

def arrays(group):
    records = [data[r['commit_hash']] for r in splits if r['split'] == group]
    assert len(records) == contract['split']['groups'][group]['rows']
    x = np.array([[float(r[k]) for k in features] for r in records])
    y = np.array([int(r['is_bug_inducing']) for r in records])
    assert np.isfinite(x).all() and (x >= 0).all() and set(y) == {0, 1}
    return x, y

xt, yt = arrays('train')
xv, yv = arrays('validation')
effort = xv[:, features.index('la')] + xv[:, features.index('ld')]
assert (effort > 0).all()
out = base / 'lr_optimization'
out.mkdir(exist_ok=True)

def save(name, value):
    (out / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')

grid = [(scale, c, weight) for scale in ('raw', 'log1p')
        for c in (.001, .01, .1, 1, 10, 100)
        for weight in (None, 'balanced', {0: 1, 1: 2})]
baseline_config = json.loads((base / 'selection.json').read_text(encoding='utf-8'))
baseline = joblib.load(base / 'model.joblib')
bs = baseline.predict_proba(xv)[:, 1]
best = (float(average_precision_score(yv, bs)), baseline, bs,
        {'transform': 'raw', 'C': baseline_config['C'], 'class_weight': baseline_config['class_weight']})
trials = []
with warnings.catch_warnings():
    warnings.simplefilter('error', ConvergenceWarning)
    for scale, c, weight in grid:
        steps = [FunctionTransformer(np.log1p)] if scale == 'log1p' else []
        model = make_pipeline(*steps, StandardScaler(), LogisticRegression(
            C=c, class_weight=weight, solver='lbfgs', max_iter=5000, random_state=42))
        model.fit(xt, yt)
        expected = np.log1p(xt) if scale == 'log1p' else xt
        np.testing.assert_allclose(model[-2].mean_, expected.mean(axis=0))
        score = model.predict_proba(xv)[:, 1]
        ap = float(average_precision_score(yv, score))
        config = {'transform':scale, 'C':c, 'class_weight':weight}
        trials.append(dict(config, validation_ap=ap))
        if ap > best[0] + 1e-12:
            best = ap, model, score, config

_, model, score, config = best
p,r,t = precision_recall_curve(yv,score)
f = np.divide(2*p[:-1]*r[:-1],p[:-1]+r[:-1],out=np.zeros_like(t),where=(p[:-1]+r[:-1])>0)
threshold = float(t[np.flatnonzero(f==f.max())[-1]])

def measures(scores, cut):
    pred = scores >= cut
    return dict(ap=float(average_precision_score(yv,scores)), auc=float(roc_auc_score(yv,scores)),
                precision=float(precision_score(yv,pred,zero_division=0)), recall=float(recall_score(yv,pred)),
                f1=float(f1_score(yv,pred)), threshold=cut)

def budget(rank_score):
    return evaluate([dict(score=str(s),label=str(y),effort=str(e)) for s,y,e in zip(rank_score,yv,effort)])

joblib.dump(model, out / 'model.joblib')
np.testing.assert_allclose(joblib.load(out / 'model.joblib').predict_proba(xv)[:,1], score)
report = dict(source_sha256=contract['source_sha256'],
              splits_sha256=hashlib.sha256((base/'splits.csv').read_bytes()).hexdigest(),
              feature_order=features, train_rows=len(yt), validation_rows=len(yv), test_evaluated=False,
              selection='highest validation AP; retain baseline on ties; max validation F1 threshold',
              selected=config, baseline=measures(bs,baseline_config['threshold']), candidate=measures(score,threshold),
              budget_comparison={name:budget(s) for name,s in [('baseline_risk',bs),('candidate_risk',score),
                                  ('candidate_risk_per_line',score/effort),('smallest_first',-effort)]},
              trials=trials)
save('report.json',report)
print(json.dumps({k:v for k,v in report.items() if k in ('selected','baseline','candidate','budget_comparison')},indent=2))
