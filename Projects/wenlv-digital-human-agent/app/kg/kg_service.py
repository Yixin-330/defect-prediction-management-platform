from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class CultureKGService:
    def __init__(self) -> None:
        path = Path(__file__).resolve().parent.parent / "data" / "culture_kg.json"
        self.graph = json.loads(path.read_text(encoding="utf-8"))

    def query_subgraph(self, query: str) -> Dict[str, object]:
        nodes = self.graph.get("nodes", [])
        edges = self.graph.get("edges", [])
        evidence = self.graph.get("evidence", {})
        matched_nodes = [node for node in nodes if node["name"] in query or node["type"] in query]
        if not matched_nodes:
            matched_nodes = nodes[:2]
        matched_ids = {node["id"] for node in matched_nodes}
        matched_edges = [edge for edge in edges if edge["source"] in matched_ids or edge["target"] in matched_ids]
        citations: List[Dict[str, str]] = []
        for node in matched_nodes:
            for ev in evidence.get(node["id"], [])[:2]:
                citations.append({"node": node["name"], "source": ev})
        return {"nodes": matched_nodes, "edges": matched_edges, "citations": citations[:4]}
