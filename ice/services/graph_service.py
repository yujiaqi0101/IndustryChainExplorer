"""Graph Service：NetworkX DiGraph 运行时构建（PRD Part 06 第十节）。

核心思想：upstream/downstream 不落盘，启动时由 Repository + Relations 构建 DiGraph。
查询上下游通过图算法，不通过存储。

边方向 = 上游 → 下游。RelationType 的方向语义：
    supply/produce    from → to   from 是 to 上游（供应/生产方在上游）
    use/integrate     to → from   to 是 from 上游（被使用/被集成方在上游）
    belong_to         to → from   to 是 from 上游（父类/归属方在上游）
    standardize       to → from   to 是 from 上游（标准在上游）
    replace/compete/related_to/research  对称，双向边，无上下游
"""

from __future__ import annotations

from typing import Any

import networkx as nx

from ice.models import Relation, RelationType
from ice.repository import Repository

# from 是 to 上游（供应/生产方向）
_FROM_IS_UPSTREAM = {RelationType.SUPPLY, RelationType.PRODUCE}
# to 是 from 上游（使用/集成/归属/标准化方向，被依赖方在上游）
_TO_IS_UPSTREAM = {RelationType.USE, RelationType.INTEGRATE, RelationType.BELONG_TO, RelationType.STANDARDIZE}
# 对称关系，无上下游
_SYMMETRIC = {RelationType.REPLACE, RelationType.COMPETE, RelationType.RELATED_TO, RelationType.RESEARCH}


class GraphService:
    """运行时图模型。

    构建有向图：
        - SUPPLY/PRODUCE：from → to（上游 → 下游）
        - USE/INTEGRATE/BELONG_TO/STANDARDIZE：to → from（上游 → 下游）
        - REPLACE/COMPETE/RELATED_TO/RESEARCH：双向边（对称关系）
    """

    def __init__(self, repo: Repository) -> None:
        self.repo = repo
        self.graph: nx.DiGraph = nx.DiGraph()
        self._build()

    def _build(self) -> None:
        for obj in self.repo.all_objects():
            self.graph.add_node(obj.id, kind=obj.kind.value, name=obj.name)
        for r in self.repo.all_relations():
            self._add_edge(r)

    def _add_edge(self, r: Relation) -> None:
        rt = r.type
        if rt in _FROM_IS_UPSTREAM:
            # from → to（上游 → 下游）
            self.graph.add_edge(r.from_, r.to, relation=r)
        elif rt in _TO_IS_UPSTREAM:
            # to → from（上游 → 下游）
            self.graph.add_edge(r.to, r.from_, relation=r)
        else:
            # 对称关系，双向
            self.graph.add_edge(r.from_, r.to, relation=r)
            self.graph.add_edge(r.to, r.from_, relation=r)

    # -- 上下游查询 ------------------------------------------------------
    def get_upstream(self, object_id: str) -> list[dict[str, Any]]:
        """上游对象 = 图中的前驱（predecessors，边指向自己）。

        边方向是 上游 → 下游，所以 predecessors 是上游。
        """
        if object_id not in self.graph:
            return []
        result: list[dict[str, Any]] = []
        for pred in self.graph.predecessors(object_id):
            edge = self.graph.edges[pred, object_id]
            r: Relation = edge["relation"]
            result.append(self._neighbor_entry(pred, r, object_id))
        return result

    def get_downstream(self, object_id: str) -> list[dict[str, Any]]:
        """下游对象 = 图中的后继（successors，自己指向的）。"""
        if object_id not in self.graph:
            return []
        result: list[dict[str, Any]] = []
        for succ in self.graph.successors(object_id):
            edge = self.graph.edges[object_id, succ]
            r: Relation = edge["relation"]
            result.append(self._neighbor_entry(succ, r, object_id))
        return result

    def get_neighbors(self, object_id: str) -> list[dict[str, Any]]:
        """所有邻居（上下游合并）。"""
        return self.get_upstream(object_id) + self.get_downstream(object_id)

    def _neighbor_entry(self, other_id: str, r: Relation, anchor_id: str) -> dict[str, Any]:
        obj = self.repo.get_object(other_id)
        # direction：判断 other 相对 anchor 是上游还是下游
        rt = r.type
        if rt in _FROM_IS_UPSTREAM:
            direction = "upstream" if other_id == r.from_ else "downstream"
        elif rt in _TO_IS_UPSTREAM:
            direction = "upstream" if other_id == r.to else "downstream"
        else:
            direction = "related"
        return {
            "object_id": other_id,
            "name": obj.name if obj else other_id,
            "kind": obj.kind.value if obj else "",
            "relation_id": r.id,
            "relation_type": r.type.value,
            "relation_label": r.label(),
            "direction": direction,
            "references": list(r.references),
        }

    # -- 关系查询 --------------------------------------------------------
    def get_relations(self, object_id: str) -> list[dict[str, Any]]:
        """涉及该对象的所有关系。"""
        if self.repo.get_object(object_id) is None:
            return []
        result: list[dict[str, Any]] = []
        for r in self.repo.relations_of(object_id):
            src = self.repo.get_object(r.from_)
            tgt = self.repo.get_object(r.to)
            result.append({
                "id": r.id,
                "from": r.from_,
                "from_name": src.name if src else r.from_,
                "to": r.to,
                "to_name": tgt.name if tgt else r.to,
                "type": r.type.value,
                "label": r.label(),
                "weight": r.weight,
                "description": r.description,
                "references": list(r.references),
                "role": "from" if r.from_ == object_id else "to",
            })
        return result
