from __future__ import annotations

from collections import defaultdict
from typing import Dict


class ObservabilityService:
    def __init__(self) -> None:
        self.metrics = defaultdict(float)

    def inc(self, key: str, value: float = 1.0) -> None:
        self.metrics[key] += value

    def report(self) -> Dict[str, float]:
        return dict(self.metrics)

    def online_guardrail(self) -> Dict[str, object]:
        # Simple rollback condition for MVP demo.
        ctr_treatment = self.metrics.get("ctr_treatment", 0.0)
        ctr_control = self.metrics.get("ctr_control", 0.0)
        should_rollback = ctr_treatment < ctr_control * 0.85 if ctr_control > 0 else False
        return {
            "rollback_recommended": should_rollback,
            "reason": "treatment_ctr_drop" if should_rollback else "healthy",
        }
