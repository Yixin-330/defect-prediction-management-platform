"""Local batch-inference boundary for the experimental JIT model package."""
import hashlib
import json
import math
from pathlib import Path

import joblib
import numpy as np


class ModelError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)


class Predictor:
    def __init__(self, bundle=None):
        self.root = Path(bundle or Path(__file__).parent)
        self.manifest = json.loads((self.root / "manifest.json").read_text(encoding="utf-8"))
        self.schema = json.loads((self.root / "feature_schema.json").read_text(encoding="utf-8"))
        self.models = {}

    def load(self, model_id):
        if model_id not in self.manifest["models"]:
            raise ModelError("MODEL_NOT_FOUND", "Model is not registered")
        if model_id not in self.models:
            entry = self.manifest["models"][model_id]
            path = (self.root / entry["artifact"]).resolve()
            if not path.is_relative_to(self.root.resolve()):
                raise ModelError("MODEL_UNAVAILABLE", "Artifact escapes bundle")
            try:
                if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                    raise ModelError("MODEL_UNAVAILABLE", "Artifact checksum mismatch")
                model = joblib.load(path)
                if model.n_features_in_ != len(self.schema["feature_order"]) or list(model.classes_) != [0, 1]:
                    raise ModelError("MODEL_UNAVAILABLE", "Model metadata mismatch")
                self.models[model_id] = model
            except ModelError:
                raise
            except Exception as error:
                raise ModelError("MODEL_UNAVAILABLE", "Model could not be loaded") from error
        return self.models[model_id]

    def vector(self, record):
        if not isinstance(record, dict):
            raise ModelError("INVALID_RECORD", "Record must be an object")
        for key in ("project_id", "commit_sha"):
            if not isinstance(record.get(key), str) or not record[key].strip():
                raise ModelError("INVALID_RECORD", key + " must be a nonempty string")
        sha = record["commit_sha"]
        if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
            raise ModelError("INVALID_RECORD", "commit_sha must be a full lowercase SHA-1")
        features = record.get("features")
        names = self.schema["feature_order"]
        if not isinstance(features, dict) or set(features) != set(names):
            raise ModelError("INVALID_FEATURES", "Exactly the 14 named features are required")
        values = []
        for name in names:
            value = features[name]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ModelError("INVALID_FEATURES", name + " must be numeric")
            try:
                value = float(value)
            except (ValueError, OverflowError) as error:
                raise ModelError("INVALID_FEATURES", name + " is not finite") from error
            if not math.isfinite(value) or value < 0:
                raise ModelError("INVALID_FEATURES", name + " must be finite and nonnegative")
            spec = self.schema["fields"][name]
            if spec["integer"] and not value.is_integer():
                raise ModelError("INVALID_FEATURES", name + " must be an integer")
            if name == "fix" and value not in (0, 1):
                raise ModelError("INVALID_FEATURES", "fix must be 0 or 1")
            if name in ("ns", "nd", "nf") and value < 1:
                raise ModelError("INVALID_FEATURES", name + " must be positive")
            values.append(value)
        return values

    def predict_batch(self, request):
        if not isinstance(request, dict):
            raise ModelError("INVALID_REQUEST", "Request must be an object")
        if request.get("feature_schema_version") != self.schema["version"]:
            raise ModelError("FEATURE_SCHEMA_MISMATCH", "Unsupported feature contract")
        records = request.get("records")
        if not isinstance(records, list) or not 1 <= len(records) <= 1000:
            raise ModelError("INVALID_REQUEST", "Provide between 1 and 1000 records")
        model_id = request.get("model_id", self.manifest["default_model"])
        if not isinstance(model_id, str):
            raise ModelError("INVALID_REQUEST", "model_id must be a string")
        model = self.load(model_id)
        entry = self.manifest["models"][model_id]
        results, seen = [], set()
        for index, record in enumerate(records):
            try:
                vector = self.vector(record)
                identity = (record["project_id"], record["commit_sha"])
                if identity in seen:
                    raise ModelError("DUPLICATE_RECORD", "Repeated project/commit within this batch")
                seen.add(identity)
                score = float(model.predict_proba(np.array([vector], dtype=float))[0, 1])
                if not math.isfinite(score) or not 0 <= score <= 1:
                    raise ModelError("INFERENCE_FAILED", "Model returned an invalid score")
                results.append(dict(index=index, status="success", project_id=identity[0],
                    commit_sha=identity[1], model_id=model_id, model_version=entry["version"],
                    feature_schema_version=self.schema["version"], risk_score=score,
                    threshold=entry["threshold"], predicted_label=int(score >= entry["threshold"]),
                    explanation=dict(available=False, method=None, contributions=None,
                                     reason="Explanation/SHAP not implemented in this package")))
            except ModelError as error:
                results.append(dict(index=index, status="failed",
                                    error=dict(code=error.code, message=error.message)))
            except Exception:
                results.append(dict(index=index, status="failed",
                                    error=dict(code="INFERENCE_FAILED", message="Prediction failed")))
        successful = sum(r["status"] == "success" for r in results)
        return dict(package_version=self.manifest["package_version"], model_id=model_id,
                    total=len(results), successful=successful, failed=len(results)-successful,
                    results=results)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("request", type=Path)
    args = parser.parse_args()
    try:
        result = Predictor().predict_batch(json.loads(args.request.read_text(encoding="utf-8")))
    except ModelError as error:
        print(json.dumps(dict(error=dict(code=error.code, message=error.message))))
        raise SystemExit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
