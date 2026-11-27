import copy
import csv
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest

import joblib
import numpy as np

import user_training as service

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'handoff_v1'))
from adapter import Predictor


class UserTrainingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.root = Path(self.tmp.name).resolve()
        assert self.root.is_relative_to(Path(__file__).parent.resolve())
        self.addCleanup(self.tmp.cleanup)
        self.source = self.root / 'input.csv'
        self.rows = []
        for project in ('a', 'b'):
            for i in range(90):
                row = dict(project_id=project, commit_hash=f'{i:040x}',
                           commit_time=(datetime(2020, 1, 1, tzinfo=timezone.utc) + timedelta(days=i)).isoformat(),
                           **{k:1 for k in service.FEATURES}, is_bug_inducing=i % 2)
                row.update(age=i, entropy=0, la=2+i%5, ld=1, fix=i%2)
                self.rows.append(row)
        self.write()

    def write(self):
        with self.source.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(self.rows[0]))
            w.writeheader()
            w.writerows(self.rows)

    def test_new_dataset_and_composite_identity(self):
        rows, summary = service.validate_and_preview(self.source)
        self.assertEqual(len(rows), 180)
        self.assertEqual(len(summary), 2)
        self.assertEqual(sum(v['train']['rows'] for v in summary.values()), 126)

    def test_duplicate_rejected_within_project(self):
        self.rows.append(copy.deepcopy(self.rows[0]))
        self.write()
        with self.assertRaises(service.TrainingError):
            service.read_dataset(self.source)

    def test_bad_feature_and_label_errors(self):
        for value in ('nan', 'inf', '-1', '', 'bad'):
            self.rows[0]['la'] = value
            self.write()
            with self.assertRaises(service.TrainingError):
                service.read_dataset(self.source)
        self.rows[0]['la'] = 2
        self.rows[0]['is_bug_inducing'] = ''
        self.write()
        with self.assertRaises(service.TrainingError) as error:
            service.read_dataset(self.source)
        self.assertEqual(error.exception.code, 'LABELS_REQUIRED')

    def test_invalid_ratios_and_timestamps(self):
        for ratios in ((.8,.2,.2), (1,0,0), (float('nan'),.1,.2)):
            with self.assertRaises(service.TrainingError):
                service.validate_and_preview(self.source, ratios)
        self.rows[0]['commit_time'] = '2020-01-01'
        self.write()
        with self.assertRaises(service.TrainingError):
            service.read_dataset(self.source)

    def test_single_class_rejected(self):
        for row in self.rows:
            row['is_bug_inducing'] = 0
        self.write()
        with self.assertRaises(service.TrainingError) as error:
            service.validate_and_preview(self.source)
        self.assertEqual(error.exception.code, 'SINGLE_CLASS')

    def test_global_cutoffs_and_ties(self):
        rows, _ = service.validate_and_preview(self.source, mode='global',
            boundaries=['2020-03-01T00:00:00+00:00', '2020-03-16T00:00:00+00:00'])
        by_time = {}
        for row in rows:
            by_time.setdefault(row['time'], set()).add(row['split'])
        self.assertTrue(all(len(s) == 1 for s in by_time.values()))
        for name, first in [('validation', '2020-03-01'), ('test', '2020-03-16')]:
            self.assertEqual(min(r['time'] for r in rows if r['split'] == name).date().isoformat(), first)

    def test_pipeline_fit_only_train_and_adapter_compatibility(self):
        before = service.digest(self.source)
        result = service.train_dataset(self.source, self.root/'run', 'fixture-v1', 'fixture-schema',
            models=('logistic_regression', 'gaussian_nb'), transform='log1p',
            parameters={'logistic_regression': {'C':.1, 'class_weight': None}})
        self.assertFalse(result['test_evaluated'])
        self.assertEqual(before, service.digest(self.source))
        split_rows, _ = service.validate_and_preview(self.source)
        train = np.array([r['x'] for r in split_rows if r['split'] == 'train'])
        for name in ('logistic_regression', 'gaussian_nb'):
            model = joblib.load(self.root/'run/models'/name/'model.joblib')
            np.testing.assert_allclose(model[-2].mean_, np.log1p(train).mean(axis=0))
            request = dict(feature_schema_version='fixture-schema', model_id=name,
                records=[dict(project_id='demo', commit_sha='a'*40,
                              features={k:float(self.rows[0][k]) for k in service.FEATURES})])
            self.assertEqual(Predictor(self.root/'run').predict_batch(request)['successful'], 1)
        with self.assertRaises(FileExistsError):
            service.train_dataset(self.source, self.root/'run', 'v1', 's1')
        self.assertEqual(json.loads((self.root/'run/status.json').read_text())['state'], 'success')

    def test_invalid_model_parameters_record_failed_status(self):
        with self.assertRaises(service.TrainingError):
            service.train_dataset(self.source, self.root/'failed', 'v1', 's1',
                parameters={'logistic_regression': {'not_a_parameter':42}})
        self.assertEqual(json.loads((self.root/'failed/status.json').read_text())['state'], 'failed')
        self.assertFalse((self.root/'failed/manifest.json').exists())


if __name__ == '__main__':
    unittest.main()
