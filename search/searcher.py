"""搜索引擎（Layered Value Chain 分层价值链）。

输入关键词（如"光"），返回匹配的条目/公司。
支持名称模糊匹配与股票代码匹配。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from repository import ChainMap


@dataclass
class SearchResult:
    """单条搜索结果。"""

    id: str
    name: str
    type: str
    score: float  # 匹配度 0~1
    chain: str = ""
    layer: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "score": self.score,
            "chain": self.chain,
            "layer": self.layer,
        }


class Searcher:
    """搜索引擎（Layered Value Chain）。"""

    def __init__(self, chain_map: ChainMap) -> None:
        self.map = chain_map

    def search(self, keyword: str, limit: int = 20) -> list[SearchResult]:
        """搜索条目/公司。

        匹配规则（按优先级）：
            1. 名称完全匹配 → 1.0
            2. 名称前缀匹配 → 0.9
            3. 名称包含匹配 → 0.7
            4. 股票代码匹配 → 0.6
            5. 标签匹配 → 0.5
        """
        if not keyword:
            return []
        kw = keyword.strip().lower()
        results: list[SearchResult] = []

        # 搜索 layers.yaml 中的条目
        for chain, vc in self.map.value_chains.items():
            for layer in vc.layers:
                for item in layer.items:
                    score = self._match_item(item.name, item.tags, kw)
                    if score > 0:
                        results.append(
                            SearchResult(
                                id=item.name,
                                name=item.name,
                                type="Item",
                                score=score,
                                chain=chain,
                                layer=layer.title,
                            )
                        )

        # 搜索 companies.yaml 中的公司
        for chain, comp_map in self.map.companies.items():
            for layer_id, items in comp_map.items():
                for item_name, comps in items.items():
                    for c in comps:
                        score = self._match_company(c, kw)
                        if score > 0:
                            results.append(
                                SearchResult(
                                    id=f"company_{c.name}",
                                    name=c.name,
                                    type="Company",
                                    score=score,
                                    chain=chain,
                                    layer=item_name,
                                )
                            )

        # 按匹配度降序，再按名称排序
        results.sort(key=lambda r: (-r.score, r.name))
        return results[:limit]

    def _match_item(self, name: str, tags: list[str], kw: str) -> float:
        name_lower = name.lower()
        # 1. 完全匹配
        if name_lower == kw or name == kw:
            return 1.0
        # 2. 前缀匹配
        if name_lower.startswith(kw) or name.startswith(kw):
            return 0.9
        # 3. 包含匹配
        if kw in name_lower or kw in name:
            return 0.7
        # 5. 标签匹配
        for tag in tags:
            if kw in str(tag).lower():
                return 0.5
        return 0.0

    def _match_company(self, comp, kw: str) -> float:
        name = comp.name.lower()
        name_full = comp.name
        # 1. 完全匹配
        if name == kw or name_full == kw:
            return 1.0
        # 2. 前缀匹配
        if name.startswith(kw) or name_full.startswith(kw):
            return 0.9
        # 3. 包含匹配
        if kw in name or kw in name_full:
            return 0.7
        # 4. 股票代码匹配
        if comp.code and kw in comp.code.lower():
            return 0.6
        # 5. 标签匹配
        for tag in comp.tags:
            if kw in str(tag).lower():
                return 0.5
        return 0.0

    def suggest(self, prefix: str, limit: int = 10) -> list[dict[str, Any]]:
        """搜索框自动补全建议。"""
        if not prefix:
            return []
        results = self.search(prefix, limit=limit)
        return [r.to_dict() for r in results]
