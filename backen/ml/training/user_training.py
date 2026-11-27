"""Train registered models on a validated user CSV without changing legacy experiments."""
import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import warnings

import joblib
import numpy as np
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import average_precision_score, roc_auc_score, precision_recall_curve, precision_score, recall_score, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from train_validation import REGISTRY
from budget_metrics import evaluate

FEATURES = 'ns nd nf entropy la ld lt fix ndev age nuc exp rexp sexp'.split()
COUNTS = set(FEATURES) - {'entropy', 'age', 'rexp'}


class TrainingError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_dataset(source):
    with Path(source).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        required = {'project_id', 'commit_hash', 'commit_time', 'is_bug_inducing', *FEATURES}
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)) or not required.issubset(headers):
            raise TrainingError('INVALID_COLUMNS', 'Require unique headers: ' + ','.join(sorted(required)))
        rows, seen = [], set()
        for line, row in enumerate(reader, 2):
            try:
                if None in row or any(v is None for v in row.values()):
                    raise ValueError('CSV column count mismatch')
                identity = (row['project_id'].strip(), row['commit_hash'])
                if not identity[0] or len(identity[1]) != 40 or any(c not in '0123456789abcdef' for c in identity[1]):
                    raise ValueError('Require project_id and full lowercase SHA-1')
                if identity in seen:
                    raise ValueError('Duplicate project/commit identity')
                seen.add(identity)
                time = datetime.fromisoformat(row['commit_time'])
                if time.tzinfo is None:
                    raise ValueError('commit_time needs a timezone')
                values = [float(row[k]) for k in FEATURES]
                if any(not math.isfinite(v) or v < 0 for v in values):
                    raise ValueError('Features must be finite nonnegative raw values')
                if any(not v.is_integer() for k, v in zip(FEATURES, values) if k in COUNTS):
                    raise ValueError('Count features must be integers')
                if any(values[FEATURES.index(k)] < 1 for k in ('ns', 'nd', 'nf')) or row['fix'] not in ('0', '1'):
                    raise ValueError('Invalid file counts or fix flag')
                if row['is_bug_inducing'] not in ('0', '1'):
                    raise TrainingError('LABELS_REQUIRED', f'Line {line}: training requires explicit 0/1 labels; unknown is not negative')
                if values[4] + values[5] <= 0:
                    raise ValueError('Positive la+ld required by effort evaluation')
                rows.append(dict(project_id=identity[0], commit_hash=identity[1],
                                 time=time.astimezone(timezone.utc), x=values,
                                 y=int(row['is_bug_inducing'])))
            except TrainingError:
                raise
            except (ValueError, TypeError, OverflowError) as error:
                raise TrainingError('INVALID_DATASET', f'Line {line}: {error}') from error
    if not rows:
        raise TrainingError('EMPTY_DATASET', 'No data records')
    return sorted(rows, key=lambda r: (r['time'], r['project_id'], r['commit_hash']))


def split_dataset(rows, ratios=(.7, .15, .15), mode='per_project', boundaries=None):
    if mode not in ('per_project', 'global'):
        raise TrainingError('INVALID_SPLIT', 'mode must be per_project or global')
    if len(ratios) != 3 or any(not math.isfinite(v) or not 0 < v < 1 for v in ratios) or not math.isclose(sum(ratios), 1, abs_tol=1e-9):
        raise TrainingError('INVALID_SPLIT', 'Three positive ratios must sum to one')
    groups = {}
    for row in rows:
        groups.setdefault(row['project_id'] if mode == 'per_project' else '__all__', []).append(dict(row))
    if boundaries:
        try:
            cut1, cut2 = [datetime.fromisoformat(t) for t in boundaries]
            if any(t.tzinfo is None for t in (cut1, cut2)) or cut1 >= cut2:
                raise ValueError()
        except (ValueError, TypeError):
            raise TrainingError('INVALID_SPLIT', 'Two ordered timezone-aware boundaries required')
    result = []
    for key, group in groups.items():
        group.sort(key=lambda r: (r['time'], r['project_id'], r['commit_hash']))
        if boundaries:
            for r in group:
                r['split'] = 'train' if r['time'] < cut1 else ('validation' if r['time'] < cut2 else 'test')
        else:
            cuts = []
            for fraction in (ratios[0], ratios[0] + ratios[1]):
                i = int(Decimal(len(group)) * Decimal(str(fraction)))
                while 0 < i < len(group) and group[i-1]['time'] == group[i]['time']:
                    i += 1
                cuts.append(i)
            a, b = cuts
            for i, r in enumerate(group):
                r['split'] = 'train' if i < a else ('validation' if i < b else 'test')
        if any(not any(r['split'] == name for r in group) for name in ('train', 'validation', 'test')):
            raise TrainingError('INVALID_SPLIT', key + ': empty split; enlarge sample or change boundaries')
        result += group
    return sorted(result, key=lambda r: (r['time'], r['project_id'], r['commit_hash']))


def validate_and_preview(source, ratios=(.7, .15, .15), mode='per_project', boundaries=None):
    rows = split_dataset(read_dataset(source), ratios, mode, boundaries)
    summary = {}
    for project in sorted({r['project_id'] for r in rows}):
        summary[project] = {}
        for name in ('train', 'validation', 'test'):
            group = [r for r in rows if r['project_id'] == project and r['split'] == name]
            summary[project][name] = dict(rows=len(group), positive=sum(r['y'] for r in group),
                first=group[0]['time'].isoformat() if group else None,
                last=group[-1]['time'].isoformat() if group else None)
    for name in ('train', 'validation'):
        if {r['y'] for r in rows if r['split'] == name} != {0, 1}:
            raise TrainingError('SINGLE_CLASS', name + ' must have both classes for AP selection')
    return rows, summary


def train_dataset(source, output, dataset_version, feature_schema_version, models=('logistic_regression',),
                  ratios=(.7, .15, .15), mode='per_project', boundaries=None,
                  parameters=None, transform='raw', seed=42):
    source, output = Path(source), Path(output)
    if not dataset_version.strip() or not feature_schema_version.strip():
        raise TrainingError('VERSION_REQUIRED', 'Dataset and feature versions are required')
    if transform not in ('raw', 'log1p') or not models or any(m not in REGISTRY for m in models):
        raise TrainingError('INVALID_CONFIG', 'Unsupported transform or algorithm')
    parameters = parameters or {}
    if not isinstance(parameters, dict) or set(parameters) - set(models):
        raise TrainingError('INVALID_CONFIG', 'Parameters must be keyed by requested algorithm')
    source_hash = digest(source)
    rows, summary = validate_and_preview(source, ratios, mode, boundaries)
    output.mkdir(parents=True, exist_ok=False)
    status = dict(state='running', dataset_version=dataset_version, models=list(models))
    save(output / 'status.json', status)
    try:
        with (output / 'splits.csv').open('w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['project_id', 'commit_hash', 'commit_time_utc', 'split'])
            writer.writerows((r['project_id'], r['commit_hash'], r['time'].isoformat(), r['split']) for r in rows)
        policy = dict(dataset_version=dataset_version, source_sha256=source_hash,
            feature_schema_version=feature_schema_version, feature_order=FEATURES,
            split_mode=mode, ratios=list(ratios), boundaries=boundaries, summary=summary,
            split_sha256=digest(output / 'splits.csv'), seed=seed, parameters=parameters,
            transform=transform, test_evaluated=False,
            notes=['Feature version and label provenance are caller declarations, not verified by CSV validation.',
                   'Per-project time splits can have overlapping calendar periods across projects; this is not global historical forecasting.',
                   'No automatic parameter search; threshold selected on pooled validation F1.'])
        save(output / 'run.json', policy)
        tr = [r for r in rows if r['split'] == 'train']
        va = [r for r in rows if r['split'] == 'validation']
        xt, yt = np.array([r['x'] for r in tr]), np.array([r['y'] for r in tr])
        xv, yv = np.array([r['x'] for r in va]), np.array([r['y'] for r in va])
        entries, metrics = {}, {}
        for name in dict.fromkeys(models):
            _, template = next(REGISTRY[name]())
            estimator = template.steps[-1][1] if hasattr(template, 'steps') else template
            overrides = parameters.get(name, {})
            if not isinstance(overrides, dict) or set(overrides) - set(estimator.get_params(deep=False)):
                raise TrainingError('INVALID_CONFIG', 'Unknown parameters: ' + name)
            estimator.set_params(**overrides)
            if 'random_state' in estimator.get_params():
                estimator.set_params(random_state=seed)
            if name == 'deep_mlp':
                estimator.set_params(early_stopping=False)
            if name == 'rbf_svm':
                estimator.set_params(probability=True)
            if name == 'knn' and estimator.n_neighbors > len(tr):
                raise TrainingError('INVALID_CONFIG', 'KNN neighbors exceed training sample count')
            steps = [FunctionTransformer(np.log1p)] if transform == 'log1p' else []
            if name in ('logistic_regression', 'gaussian_nb', 'knn', 'rbf_svm', 'deep_mlp'):
                steps.append(StandardScaler())
            model = make_pipeline(*steps, estimator)
            with warnings.catch_warnings():
                warnings.simplefilter('error', ConvergenceWarning)
                model.fit(xt, yt)
            score = model.predict_proba(xv)[:, list(model.classes_).index(1)]
            if not np.isfinite(score).all():
                raise TrainingError('INFERENCE_FAILED', name + ': nonfinite validation scores')
            p, r, t = precision_recall_curve(yv, score)
            f1 = np.divide(2*p[:-1]*r[:-1], p[:-1]+r[:-1], out=np.zeros_like(t), where=(p[:-1]+r[:-1])>0)
            threshold = float(t[np.flatnonzero(f1 == f1.max())[-1]])
            predicted = score >= threshold
            records = [dict(project_id=row['project_id'], commit_hash=row['commit_hash'],
                label=int(y), score=float(s), prediction=int(z), effort=int(row['x'][4]+row['x'][5]))
                for row, y, s, z in zip(va, yv, score, predicted)]
            metrics[name] = dict(ap=float(average_precision_score(yv, score)),
                roc_auc=float(roc_auc_score(yv, score)), precision=float(precision_score(yv, predicted, zero_division=0)),
                recall=float(recall_score(yv, predicted)), f1=float(f1_score(yv, predicted)), budget=evaluate(records))
            artifact = output / 'models' / name / 'model.joblib'
            artifact.parent.mkdir(parents=True)
            joblib.dump(model, artifact)
            np.testing.assert_allclose(joblib.load(artifact).predict_proba(xv)[:, 1], score, rtol=0, atol=1e-12)
            entries[name] = dict(version=dataset_version + '-run', artifact=artifact.relative_to(output).as_posix(),
                sha256=digest(artifact), threshold=threshold, parameters=estimator.get_params(deep=False),
                feature_schema_version=feature_schema_version)
        if digest(source) != source_hash:
            raise TrainingError('SOURCE_CHANGED', 'Source changed during training')
        schema = dict(version=feature_schema_version, feature_order=FEATURES,
            fields={k:dict(integer=k in COUNTS, minimum=0, missing='reject') for k in FEATURES})
        save(output / 'feature_schema.json', schema)
        save(output / 'metrics.json', metrics)
        save(output / 'manifest.json', dict(package_version='user-training-v1', status='experimental',
             default_model=next(iter(entries)), models=entries, dataset_version=dataset_version,
             source_sha256=source_hash, splits_sha256=policy['split_sha256'],
             runtime=dict(numpy=np.__version__, sklearn=sklearn.__version__, joblib=joblib.__version__),
             explanation_available=False))
        save(output / 'status.json', dict(status, state='success'))
        return dict(output=str(output.resolve()), summary=summary, validation_metrics=metrics, test_evaluated=False)
    except Exception as error:
        save(output / 'status.json', dict(status, state='failed',
             error=dict(code=getattr(error, 'code', 'TRAINING_FAILED'), message=str(error))))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--dataset-version', default='')
    parser.add_argument('--feature-schema-version', default='')
    parser.add_argument('--models', nargs='+', choices=list(REGISTRY), default=['logistic_regression'])
    parser.add_argument('--ratios', nargs=3, type=float, default=[.7, .15, .15])
    parser.add_argument('--split-mode', choices=['per_project', 'global'], default='per_project')
    parser.add_argument('--boundaries', nargs=2)
    parser.add_argument('--parameters', type=Path)
    parser.add_argument('--transform', choices=['raw', 'log1p'], default='raw')
    parser.add_argument('--preview-only', action='store_true')
    args = parser.parse_args()
    try:
        if args.preview_only:
            _, summary = validate_and_preview(args.source, args.ratios, args.split_mode, args.boundaries)
            print(json.dumps(dict(summary=summary, trained=False), ensure_ascii=False))
        else:
            if args.output is None:
                parser.error('--output required for training')
            params = json.loads(args.parameters.read_text(encoding='utf-8')) if args.parameters else None
            print(json.dumps(train_dataset(args.source, args.output, args.dataset_version,
                args.feature_schema_version, args.models, args.ratios, args.split_mode,
                args.boundaries, params, args.transform), ensure_ascii=False))
    except TrainingError as error:
        print(json.dumps(dict(error=dict(code=error.code, message=str(error))), ensure_ascii=False))
        raise SystemExit(1)
