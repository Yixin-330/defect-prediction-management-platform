from __future__ import annotations

from typing import Dict, List

from app.kg.kg_service import CultureKGService


class GraphRAGService:
    def __init__(self, kg_service: CultureKGService) -> None:
        self.kg = kg_service

    def grounded_answer(self, query: str) -> Dict[str, object]:
        subgraph = self.kg.query_subgraph(query)
        nodes: List[Dict[str, str]] = subgraph["nodes"]
        citations: List[Dict[str, str]] = subgraph["citations"]
        if not nodes:
            return {"answer": "未检索到可靠文化证据，建议补充问题细节。", "citations": []}
        highlights = "、".join(node["name"] for node in nodes[:3])
        answer = f"根据文化知识图谱检索，与你的问题最相关的文化实体包括：{highlights}。以下结论均基于可追溯档案证据。"
        return {"answer": answer, "citations": citations}
