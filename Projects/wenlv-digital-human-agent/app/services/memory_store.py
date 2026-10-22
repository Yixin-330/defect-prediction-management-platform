from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from app.models import Turn


class MemoryStore:
    """In-memory session memory with compact long-term summary per user."""

    def __init__(self) -> None:
        self.session_turns: Dict[str, List[Turn]] = defaultdict(list)
        self.user_summary: Dict[str, str] = defaultdict(str)

    def add_turn(self, session_id: str, turn: Turn) -> None:
        self.session_turns[session_id].append(turn)

    def get_turns(self, session_id: str) -> List[Turn]:
        return self.session_turns.get(session_id, [])

    def update_summary(self, user_id: str, latest_user_text: str, latest_agent_text: str) -> str:
        current = self.user_summary.get(user_id, "")
        snippet = f"用户提到: {latest_user_text[:80]} | 助手回应: {latest_agent_text[:80]}"
        merged = f"{current} || {snippet}" if current else snippet
        self.user_summary[user_id] = merged[-2000:]
        return self.user_summary[user_id]

    def get_summary(self, user_id: str) -> str:
        return self.user_summary.get(user_id, "")
