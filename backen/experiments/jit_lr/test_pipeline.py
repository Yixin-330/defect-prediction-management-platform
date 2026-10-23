"""Regression checks for labels, temporal boundaries and preprocessing leakage."""

from pathlib import Path
import tempfile
import unittest

import joblib
import numpy as np

import pipeline as experiment


class ContractTests(unittest.TestCase):
    def test_source_label_and_missing_feature_policy(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            self.assertTrue(Path(folder).resolve().is_relative_to(experiment.ROOT))
            path = Path(folder) / "openstack.csv"
            records = []
            for i in range(20):
                records.append({"commit_id": f"{i:040x}", "author_date": 1322599384 + i,
                                "bugcount": "" if i == 0 else str(i % 2), "fixcount": "",
                                **{key: "1" for key in experiment.FEATURES}})
            records[0]["age"] = ""
            experiment.dump_csv(path, records)
            rows, _, audit = experiment.prepare(path, "openstack")
            self.assertEqual(rows[0]["is_bug_inducing"], 0)
            self.assertEqual(rows[1]["is_bug_inducing"], 1)
            self.assertEqual(rows[0]["age"], "")
            self.assertEqual(audit["counts"]["blank_bugcount_to_negative"], 1)
            records[0]["bugcount"] = "unknown"
            experiment.dump_csv(path, records)
            with self.assertRaises(ValueError):
                experiment.prepare(path, "openstack")

    def test_tied_timestamps_never_cross_splits(self):
        rows = [{"author_date": i // 3, "commit_sha": f"{i:040x}"} for i in range(60)]
        result = experiment.split_rows(list(reversed(rows)))
        groups = {}
        for row in result:
            groups.setdefault(row["author_date"], set()).add(row["split"])
        self.assertTrue(all(len(group) == 1 for group in groups.values()))
        windows = [[r["author_date"] for r in result if r["split"] == name]
                   for name in ("train", "validation", "test")]
        self.assertLess(max(windows[0]), min(windows[1]))
        self.assertLess(max(windows[1]), min(windows[2]))

    def test_saved_preprocessing_does_not_fit_future_values(self):
        rows = []
        for i in range(60):
            values = {key: float(i % 5 + 1) for key in experiment.FEATURES}
            values["age"] = "" if i % 4 == 0 else float(i + 1)
            rows.append({"project_id": "fixture", "commit_sha": f"{i:040x}",
                         "author_date": i, "committed_at": str(i), **values,
                         "effort": 2, "is_bug_inducing": i % 2})
        rows = experiment.split_rows(rows)
        for row in rows:
            if row["split"] != "train":
                row["age"] = 1000000000.0
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            self.assertTrue(Path(folder).resolve().is_relative_to(experiment.ROOT))
            output = Path(folder)
            experiment.dump_csv(output / "samples.csv", rows)
            experiment.train(rows, output, 42)
            model = joblib.load(output / "model.joblib")
            training = [r for r in rows if r["split"] == "train"]
            expected = np.nanmedian(experiment.matrix(training), axis=0)
            np.testing.assert_allclose(model[0].statistics_, expected)
            transformed = model[0].transform(experiment.matrix(training))
            np.testing.assert_allclose(model[1].mean_, transformed.mean(axis=0))

    def test_reproducible_preparation_and_source_identity(self):
        for project in experiment.WINDOWS:
            source = experiment.ROOT / "data" / f"{project}.csv"
            before = experiment.digest(source)
            first, _, _ = experiment.prepare(source, project)
            second, _, _ = experiment.prepare(source, project)
            self.assertEqual(first, second)
            self.assertEqual(before, experiment.digest(source))
            self.assertEqual(len(first), 12374 if project == "openstack" else 25150)
            self.assertFalse(set(experiment.FEATURES) & {"bugcount", "fixcount", "rexp", "rtime", "lt"})


if __name__ == "__main__":
    unittest.main()
