from __future__ import annotations

import hashlib


class ABExperimentService:
    """Stable assignment: even hash -> control, odd hash -> treatment."""

    def assign_variant(self, user_id: str) -> str:
        digest = hashlib.md5(user_id.encode("utf-8")).hexdigest()
        bucket = int(digest[:8], 16) % 2
        return "control" if bucket == 0 else "treatment"
