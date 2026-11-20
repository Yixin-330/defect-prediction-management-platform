import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from adapter import Predictor, ModelError

BASE = Path(__file__).resolve().parent


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.predictor = Predictor()
        self.request = json.loads((BASE / "sample_request.json").read_text(encoding="utf-8"))

    def test_all_eight_models_and_golden_response(self):
        for model_id in self.predictor.manifest["models"]:
            response = self.predictor.predict_batch(dict(self.request, model_id=model_id))
            self.assertEqual(response["successful"], 2)
            for result in response["results"]:
                self.assertTrue(0 <= result["risk_score"] <= 1)
                self.assertEqual(result["predicted_label"], int(result["risk_score"] >= result["threshold"]))
                self.assertFalse(result["explanation"]["available"])
        golden = json.loads((BASE / "sample_response.json").read_text(encoding="utf-8"))
        self.assertEqual(self.predictor.predict_batch(self.request), golden)

    def test_reordered_named_features_are_identical(self):
        changed = copy.deepcopy(self.request)
        for r in changed["records"]:
            r["features"] = dict(reversed(list(r["features"].items())))
        self.assertEqual(self.predictor.predict_batch(self.request), self.predictor.predict_batch(changed))

    def test_schema_mismatch(self):
        self.request["feature_schema_version"] = "wrong"
        with self.assertRaises(ModelError) as caught:
            self.predictor.predict_batch(self.request)
        self.assertEqual(caught.exception.code, "FEATURE_SCHEMA_MISMATCH")

    def test_unknown_model(self):
        with self.assertRaises(ModelError) as caught:
            self.predictor.predict_batch(dict(self.request, model_id="../unregistered"))
        self.assertEqual(caught.exception.code, "MODEL_NOT_FOUND")

    def test_bad_features_do_not_return_scores(self):
        for value in (None, "12", True, float("nan"), float("inf"), -1, 1.5):
            request = copy.deepcopy(self.request)
            request["records"][0]["features"]["la"] = value
            result = self.predictor.predict_batch(request)
            self.assertEqual(result["results"][0]["error"]["code"], "INVALID_FEATURES")
            self.assertNotIn("risk_score", result["results"][0])
            self.assertEqual(result["successful"], 1)

    def test_missing_and_extra_features(self):
        for extra in (False, True):
            request = copy.deepcopy(self.request)
            if extra:
                request["records"][0]["features"]["label"] = 1
            else:
                del request["records"][0]["features"]["lt"]
            self.assertEqual(self.predictor.predict_batch(request)["failed"], 1)

    def test_duplicate_and_bad_identity(self):
        request = copy.deepcopy(self.request)
        request["records"][1] = copy.deepcopy(request["records"][0])
        response = self.predictor.predict_batch(request)
        self.assertEqual(response["results"][1]["error"]["code"], "DUPLICATE_RECORD")
        request["records"][0]["commit_sha"] = "short"
        self.assertEqual(self.predictor.predict_batch(request)["results"][0]["error"]["code"], "INVALID_RECORD")

    def test_empty_batch(self):
        with self.assertRaises(ModelError):
            self.predictor.predict_batch(dict(self.request, records=[]))

    def test_checksum_rejection_before_deserialization(self):
        with patch("pathlib.Path.read_bytes", return_value=b"corrupt"), patch("adapter.joblib.load") as loader:
            with self.assertRaises(ModelError) as caught:
                self.predictor.load(self.predictor.manifest["default_model"])
            self.assertEqual(caught.exception.code, "MODEL_UNAVAILABLE")
            loader.assert_not_called()


if __name__ == "__main__":
    unittest.main()
