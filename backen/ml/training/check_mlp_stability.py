"""Check fixed selected MLP structure across seeds; never select the best seed."""
import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import joblib
from sklearn.base import clone
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import average_precision_score, roc_auc_score, f1_score

from train_validation import BASE, load, save
from budget_metrics import evaluate


def main(source):
    training, validation, ids, metadata = load(source)
    xt, yt = training
    xv, yv = validation
    out = BASE / 'unified_validation' / 'deep_mlp'
    model = joblib.load(out / 'model.joblib')
    report = json.loads((out / 'report.json').read_text(encoding='utf-8'))
    seeds = (42, 7, 21)
    save(out / 'stability_protocol.json', dict(seeds=seeds, parameters=report['parameters'],
         policy='Fixed selected configuration and threshold; seed 42 remains published. No seed selection.',
         test_evaluated=False))
    effort = xv[:, metadata['feature_order'].index('la')] + xv[:, metadata['feature_order'].index('ld')]
    results = []
    for seed in seeds:
        candidate = clone(model).set_params(mlpclassifier__random_state=seed)
        with warnings.catch_warnings():
            warnings.simplefilter('error', ConvergenceWarning)
            candidate.fit(xt, yt)
        score = candidate.predict_proba(xv)[:, 1]
        if seed == 42:
            np.testing.assert_allclose(score, model.predict_proba(xv)[:, 1], rtol=0, atol=1e-12)
        expected = np.log1p(xt) if report['parameters']['transform'] == 'log1p' else xt
        np.testing.assert_allclose(candidate[-2].mean_, expected.mean(axis=0))
        assert candidate[-2].n_samples_seen_ == len(xt)
        rows = [dict(score=str(s), label=str(y), effort=str(e)) for s, y, e in zip(score, yv, effort)]
        budget = evaluate(rows)['results']['skip_over_budget']
        results.append(dict(seed=seed, ap=float(average_precision_score(yv, score)),
             roc_auc=float(roc_auc_score(yv, score)),
             f1_at_frozen_threshold=float(f1_score(yv, score >= report['threshold'])),
             recall_at_20_percent_effort=budget['recall'], n_iter=int(candidate[-1].n_iter_),
             training_loss=float(candidate[-1].loss_)))
    stats = {key: dict(mean=float(np.mean([r[key] for r in results])),
                       std_population=float(np.std([r[key] for r in results])))
             for key in ('ap', 'roc_auc', 'f1_at_frozen_threshold', 'recall_at_20_percent_effort')}
    save(out / 'stability.json', dict(**metadata, runs=results, summary=stats,
         note='Configuration was selected on seed 42 validation results. Seeds 7/21 are sensitivity checks, not independent test estimates.'))
    print(json.dumps(dict(runs=results, summary=stats), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    main(parser.parse_args().source)
