"""Search Service：对象索引（PRD Part 06 第十一节）。

只索引 Object，不索引 Relation。
索引项：id / name / aliases / tags / summary

匹配优先级：
    1. id 完全匹配        → 1.0
    2. name 完全匹配      → 1.0
    3. alias 完全匹配     → 0.95
    4. id 前缀匹配        → 0.9
    5. name 前缀匹配      → 0.9
    6. id/name 包含匹配   → 0.7
    7. tag 匹配           → 0.5
    8. summary 包含匹配   → 0.4
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ice.models import Object
from ice.repository import Repository


@dataclass
class SearchHit:
    """单条搜索结果。"""

    object_id: str
    name: str
    kind: str
    score: float
    matched: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "name": self.name,
            "kind": self.kind,
            "score": round(self.score, 3),
            "matched": self.matched,
        }


class SearchService:
    """对象搜索索引。"""

    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def search(self, keyword: str, limit: int = 20) -> list[SearchHit]:
        kw = (keyword or "").strip().lower()
        if not kw:
            return []
        hits: list[SearchHit] = []
        for obj in self.repo.all_objects():
            score, matched = self._match(obj, kw)
            if score > 0:
                hits.append(SearchHit(
                    object_id=obj.id, name=obj.name,
                    kind=obj.kind.value, score=score, matched=matched,
                ))
        hits.sort(key=lambda h: (-h.score, h.name))
        return hits[:limit]

    def suggest(self, prefix: str, limit: int = 10) -> list[dict[str, Any]]:
        return [h.to_dict() for h in self.search(prefix, limit=limit)]

    def _match(self, obj: Object, kw: str) -> tuple[float, str]:
        oid = obj.id.lower()
        name = obj.name.lower()
        aliases = [a.lower() for a in obj.aliases]

        if oid == kw:
            return 1.0, "id"
        if name == kw:
            return 1.0, "name"
        for a in aliases:
            if a == kw:
                return 0.95, "alias"
        if oid.startswith(kw):
            return 0.9, "id"
        if name.startswith(kw):
            return 0.9, "name"
        if kw in oid:
            return 0.7, "id"
        if kw in name:
            return 0.7, "name"
        for a in aliases:
            if kw in a:
                return 0.65, "alias"
        for tag in obj.tags:
            if kw in tag.lower():
                return 0.5, "tag"
        if kw in obj.summary.lower():
            return 0.4, "summary"
        return 0.0, ""
