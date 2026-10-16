from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Dict, List

from app.models import AnalyticsEvent, EventRequest, FeatureSnapshot


class AnalyticsService:
    def __init__(self) -> None:
        self._events: List[AnalyticsEvent] = []
        self._count_by_user: Dict[str, int] = defaultdict(int)
        self._theme_by_user: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._hour_by_user: Dict[str, Counter] = defaultdict(Counter)
        self._geo_by_user: Dict[str, Counter] = defaultdict(Counter)
        self._session_step: Dict[str, int] = defaultdict(int)

    def track(self, event: AnalyticsEvent) -> None:
        self._events.append(event)
        self._count_by_user[event.user_id] += 1
        self._session_step[event.session_id] += 1
        theme = str(event.metadata.get("theme", ""))
        if theme:
            self._theme_by_user[event.user_id][theme] += 1
        location = str(event.metadata.get("location", ""))
        if location:
            self._geo_by_user[event.user_id][location] += 1
        hour = event.timestamp.hour
        self._hour_by_user[event.user_id][str(hour)] += 1

    def track_event_request(self, req: EventRequest) -> None:
        metadata = dict(req.metadata)
        if req.theme:
            metadata["theme"] = req.theme
        if req.poi_id:
            metadata["poi_id"] = req.poi_id
        if req.dwell_seconds is not None:
            metadata["dwell_seconds"] = req.dwell_seconds
        if req.clicked is not None:
            metadata["clicked"] = req.clicked
        if req.converted is not None:
            metadata["converted"] = req.converted
        self.track(
            AnalyticsEvent(
                user_id=req.user_id,
                session_id=req.session_id,
                event_type=req.event_type,
                metadata=metadata,
            )
        )

    def user_report(self, user_id: str) -> Dict[str, object]:
        return {
            "event_count": self._count_by_user.get(user_id, 0),
            "theme_distribution": dict(self._theme_by_user.get(user_id, {})),
            "hour_distribution": dict(self._hour_by_user.get(user_id, {})),
            "geo_distribution": dict(self._geo_by_user.get(user_id, {})),
        }

    def build_feature_snapshot(self, user_id: str, session_id: str) -> FeatureSnapshot:
        topic_counter = self._theme_by_user.get(user_id, {})
        total = sum(topic_counter.values())
        topic_distribution = {
            topic: round(count / total, 4) for topic, count in topic_counter.items()
        } if total else {}
        stage = "start"
        steps = self._session_step.get(session_id, 0)
        if steps >= 6:
            stage = "late"
        elif steps >= 3:
            stage = "middle"
        return FeatureSnapshot(
            user_id=user_id,
            topic_distribution=topic_distribution,
            hour_preference=dict(self._hour_by_user.get(user_id, {})),
            geo_hotspots=dict(self._geo_by_user.get(user_id, {})),
            session_stage=stage,
        )

    def export_training_samples(self, output_path: str) -> Dict[str, object]:
        rows: List[Dict[str, object]] = []
        for event in self._events:
            row = {
                "user_id": event.user_id,
                "session_id": event.session_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "metadata": event.metadata,
            }
            rows.append(row)
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"sample_count": len(rows), "output_path": str(target)}
