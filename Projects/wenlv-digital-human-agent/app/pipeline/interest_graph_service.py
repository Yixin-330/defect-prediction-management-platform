from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict


@dataclass
class _Edge:
    weight: float
    updated_at: datetime


class InterestGraphService:
    """User-Topic-POI-Time dynamic graph with decay."""

    def __init__(self, decay: float = 0.92) -> None:
        self.decay = decay
        self.user_topic_edges: Dict[str, Dict[str, _Edge]] = defaultdict(dict)
        self.user_poi_edges: Dict[str, Dict[str, _Edge]] = defaultdict(dict)
        self.user_time_edges: Dict[str, Dict[str, _Edge]] = defaultdict(dict)

    def update(self, user_id: str, topic: str, poi_id: str | None, hour_slot: str) -> None:
        now = datetime.utcnow()
        self._update_edge(self.user_topic_edges[user_id], topic, now)
        if poi_id:
            self._update_edge(self.user_poi_edges[user_id], poi_id, now)
        self._update_edge(self.user_time_edges[user_id], hour_slot, now)

    def get_features(self, user_id: str) -> Dict[str, object]:
        topic_rank = self._rank(self.user_topic_edges.get(user_id, {}))
        poi_rank = self._rank(self.user_poi_edges.get(user_id, {}))
        time_rank = self._rank(self.user_time_edges.get(user_id, {}))
        exploration = self._compute_exploration(user_id)
        return {
            "short_term_topics": topic_rank[:3],
            "long_term_topics": topic_rank[:6],
            "poi_affinity": poi_rank[:5],
            "time_preference": time_rank[:3],
            "exploration_score": exploration,
        }

    def _update_edge(self, bucket: Dict[str, _Edge], key: str, now: datetime) -> None:
        old = bucket.get(key)
        if not old:
            bucket[key] = _Edge(weight=1.0, updated_at=now)
            return
        elapsed_hours = max((now - old.updated_at).total_seconds() / 3600.0, 0.0)
        decayed = old.weight * (self.decay ** elapsed_hours)
        bucket[key] = _Edge(weight=decayed + 1.0, updated_at=now)

    def _rank(self, edges: Dict[str, _Edge]) -> list[tuple[str, float]]:
        now = datetime.utcnow()
        scored = []
        for key, edge in edges.items():
            elapsed_hours = max((now - edge.updated_at).total_seconds() / 3600.0, 0.0)
            score = edge.weight * (self.decay ** elapsed_hours)
            scored.append((key, round(score, 4)))
        return sorted(scored, key=lambda item: item[1], reverse=True)

    def _compute_exploration(self, user_id: str) -> float:
        topics = self.user_topic_edges.get(user_id, {})
        if not topics:
            return 1.0
        weights = [edge.weight for edge in topics.values()]
        total = sum(weights) or 1.0
        concentration = max(weights) / total
        return round(max(0.0, 1.0 - concentration), 4)
