"""产业链浏览服务（Layered Value Chain 分层价值链）。

核心模型是 Layer（层），不是 Tree 也不是 Graph。

视图优先级：
    Layer View（默认主视图）- layer_view()
        产业分层视图，一眼看清整个产业
        Application → System → Component → Material
    Graph View（辅助视图）- graph_view()
        关系图，DSP→光模块→交换机→AI服务器

详情页（get_detail）：
    基于 Layer，展示条目所在层、同层条目、上下游层、关联公司
"""

from __future__ import annotations

from typing import Any, Optional

from models import Relation, RelationType, ValueChain
from models.layer import Layer, LayerItem
from repository import ChainMap, CompanyInfo


class ExplorerService:
    """产业链浏览器服务（Layered Value Chain）。"""

    def __init__(self, chain_map: ChainMap):
        self.map = chain_map

    # ==================================================================
    # Layer View（主视图）
    # ==================================================================
    def layer_view(self, chain: Optional[str] = None) -> list[dict[str, Any]]:
        """分层价值链视图（默认主视图）。

        Args:
            chain: 产业包名（如 optical）。None 返回所有产业包。

        Returns:
            [{chain, industry, layers: [{id, title, order, items: [...]}]}]
        """
        result: list[dict[str, Any]] = []
        if chain:
            vc = self.map.get_value_chain(chain)
            if vc is not None:
                result.append(self._value_chain_to_dict(chain, vc))
        else:
            for name, vc in self.map.value_chains.items():
                result.append(self._value_chain_to_dict(name, vc))
        return result

    def _value_chain_to_dict(self, chain: str, vc: ValueChain) -> dict[str, Any]:
        meta = self.map.chain_meta.get(chain, {})
        return {
            "chain": chain,
            "industry": vc.industry or meta.get("name", chain),
            "description": meta.get("description", ""),
            "keywords": meta.get("keywords", []) or meta.get("tags", []),
            "layers": [l.to_dict() for l in vc.layers],
        }

    # ==================================================================
    # 详情页（基于 Layer）
    # ==================================================================
    def get_detail(
        self, name: str, show_companies: bool = False
    ) -> Optional[dict[str, Any]]:
        """获取条目详情（基于 Layer）。

        Args:
            name: 条目名（如 光模块 / DSP）
            show_companies: 公司模式（显示公司）

        Returns:
            {
                name, summary, glossary,
                chain, layer (所在层),
                upstream_layers (上游层),
                downstream_layers (下游层),
                same_layer_items (同层条目),
                core_companies (公司模式),
                references (引用来源),
                notes (产业说明),
                show_companies,
            }
        """
        vc = self.map.find_value_chain_of(name)
        if vc is None:
            return None

        chain = self.map.find_chain_of(name)
        found = vc.find_item(name)
        if found is None:
            return None
        current_layer, item = found

        # 上游层 / 下游层
        upstream_layers = [l.to_dict() for l in vc.upstream_layers(name)]
        downstream_layers = [l.to_dict() for l in vc.downstream_layers(name)]

        # 同层条目（排除自己）
        same_layer = [
            it.to_dict() for it in current_layer.items if it.name != name
        ]

        # 公司
        core_companies: list[dict[str, Any]] = []
        if show_companies and chain:
            comps = self.map.companies_of_item(chain, name)
            core_companies = [c.to_dict() for c in comps]

        # 词典释义
        glossary = self.map.lookup_term(name)

        # 引用来源（从 relations 聚合）
        references = self._references_of(name)

        # 产业说明
        notes = self.map.chain_notes.get(chain, "") if chain else ""

        # 元信息
        meta = self.map.chain_meta.get(chain, {}) if chain else {}

        return {
            "name": name,
            "summary": item.summary,
            "tags": list(item.tags),
            "glossary": glossary,
            "chain": chain,
            "industry": vc.industry or meta.get("name", ""),
            "layer": current_layer.to_dict(),
            "upstream_layers": upstream_layers,
            "downstream_layers": downstream_layers,
            "same_layer_items": same_layer,
            "core_companies": core_companies,
            "references": references,
            "notes": notes,
            "show_companies": show_companies,
        }

    def _references_of(self, name: str) -> list[dict[str, Any]]:
        """聚合所有涉及该条目的关系引用来源。"""
        refs: list[dict[str, Any]] = []
        for rel in self.map.relations:
            if rel.source == name or rel.target == name:
                refs.append(
                    {
                        "source": rel.source,
                        "target": rel.target,
                        "relation": rel.relation.value,
                        "label": rel.label,
                        "description": rel.description,
                        "reference": list(rel.reference),
                    }
                )
        return refs

    # ==================================================================
    # Graph View（辅助视图）
    # ==================================================================
    def graph_data(
        self,
        name: str,
        depth: int = 1,
        show_companies: bool = False,
    ) -> Optional[dict[str, Any]]:
        """关系图数据（vis-network 格式，辅助视图）。

        基于 relations.yaml 构建 Graph。
        """
        # 确认条目存在
        vc = self.map.find_value_chain_of(name)
        if vc is None:
            # 也可能是公司
            comp = self.map.get_company_by_name(name)
            if comp is None:
                return None

        nodes: dict[str, dict[str, Any]] = {}
        edges: list[dict[str, Any]] = []

        # 中心节点
        nodes[name] = self._graph_node(name, "Item")

        # BFS 展开
        visited: set[str] = {name}
        frontier: set[str] = {name}
        for _ in range(depth):
            next_frontier: set[str] = set()
            for node_name in frontier:
                for rel in self.map.relations:
                    neighbor = None
                    if rel.source == node_name:
                        neighbor = rel.target
                    elif rel.target == node_name:
                        neighbor = rel.source
                    if neighbor and neighbor not in visited:
                        next_frontier.add(neighbor)
                        nodes[neighbor] = self._graph_node(neighbor, "Item")
                        edges.append(
                            {
                                "from": rel.source,
                                "to": rel.target,
                                "label": rel.label,
                                "relation": rel.relation.value,
                            }
                        )
            visited.update(next_frontier)
            frontier = next_frontier

        # 公司模式：加入公司节点
        if show_companies:
            chain = self.map.find_chain_of(name)
            if chain:
                for item_name in list(nodes.keys()):
                    comps = self.map.companies_of_item(chain, item_name)
                    for c in comps:
                        comp_id = f"company_{c.name}"
                        if comp_id not in nodes:
                            nodes[comp_id] = {
                                "id": comp_id,
                                "label": c.name,
                                "type": "Company",
                                "code": c.code,
                            }
                            edges.append(
                                {
                                    "from": item_name,
                                    "to": comp_id,
                                    "label": "生产",
                                    "relation": "Produces",
                                }
                            )

        return {
            "center": name,
            "nodes": list(nodes.values()),
            "edges": edges,
        }

    def _graph_node(self, name: str, node_type: str) -> dict[str, Any]:
        vc = self.map.find_value_chain_of(name)
        layer_title = ""
        if vc:
            layer = vc.layer_of(name)
            if layer:
                layer_title = layer.title
        return {
            "id": name,
            "label": name,
            "type": node_type,
            "layer": layer_title,
        }

    # ==================================================================
    # 列表
    # ==================================================================
    def list_chains(self) -> list[dict[str, Any]]:
        """所有产业包。"""
        result: list[dict[str, Any]] = []
        for chain, vc in self.map.value_chains.items():
            meta = self.map.chain_meta.get(chain, {})
            result.append(
                {
                    "name": chain,
                    "industry": vc.industry or meta.get("name", chain),
                    "description": meta.get("description", ""),
                    "layer_count": vc.layer_count,
                    "item_count": len(vc.all_items()),
                }
            )
        return result

    def list_all_items(self) -> list[dict[str, Any]]:
        """所有条目（跨产业包）。"""
        result: list[dict[str, Any]] = []
        for chain, vc in self.map.value_chains.items():
            for layer in vc.layers:
                for item in layer.items:
                    result.append(
                        {
                            "name": item.name,
                            "summary": item.summary,
                            "chain": chain,
                            "layer": layer.title,
                            "layer_id": layer.id,
                        }
                    )
        return result

    def list_all_tags(self) -> list[dict[str, Any]]:
        """所有标签（带计数）。"""
        from models import Tag

        counter: dict[str, int] = {}
        for vc in self.map.value_chains.values():
            for layer in vc.layers:
                for item in layer.items:
                    for t in item.tags:
                        counter[t] = counter.get(t, 0) + 1
        tags = [Tag(name=name, count=count) for name, count in counter.items()]
        tags.sort(key=lambda t: t.count, reverse=True)
        return [t.to_dict() for t in tags]

    def list_all_tags_simple(self) -> list[str]:
        return [t["name"] for t in self.list_all_tags()]

    def search_by_tag(self, tag: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for chain, vc in self.map.value_chains.items():
            for layer in vc.layers:
                for item in layer.items:
                    if tag in item.tags:
                        result.append(
                            {
                                "name": item.name,
                                "summary": item.summary,
                                "chain": chain,
                                "layer": layer.title,
                            }
                        )
        return result

    # ==================================================================
    # 词典
    # ==================================================================
    def glossary(self, chain: Optional[str] = None) -> dict[str, str]:
        """名词解释。"""
        if chain:
            return self.map.get_glossary(chain)
        # 合并所有
        merged: dict[str, str] = {}
        for terms in self.map.glossary.values():
            merged.update(terms)
        return merged

    # ==================================================================
    # 统计
    # ==================================================================
    def stats(self) -> dict[str, Any]:
        return {
            "chains": len(self.map.value_chains),
            "items": self.map.total_items,
            "companies": self.map.total_companies,
            "relations": len(self.map.relations),
            "glossary_terms": sum(len(t) for t in self.map.glossary.values()),
        }

    def hot_industries(self, limit: int = 10) -> list[dict[str, Any]]:
        """热门产业（按条目数排序）。"""
        chains = self.list_chains()
        chains.sort(key=lambda c: c["item_count"], reverse=True)
        return chains[:limit]
