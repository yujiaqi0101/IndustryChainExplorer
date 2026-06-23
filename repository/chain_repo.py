"""产业链数据仓库（Layered Value Chain 分层价值链）。

加载产业包数据：
    overview.yaml    → chain_meta / chain_notes
    layers.yaml      → value_chains（ValueChain，核心）
    companies.yaml   → companies（按 Layer 分组）
    relations.yaml   → relations（Graph View，辅助）
    glossary.yaml    → glossary（名词解释）

产业包目录结构：
    chains/{name}/
        overview.yaml
        layers.yaml
        companies.yaml
        relations/relations.yaml
        glossary.yaml
        README.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from models import Node, NodeType, Relation, ValueChain
from models.layer import Layer, LayerItem


@dataclass
class CompanyInfo:
    """公司信息（按 Layer 分组）。"""

    code: str
    name: str
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "summary": self.summary,
            "tags": list(self.tags),
            "properties": dict(self.properties),
        }

    @classmethod
    def from_dict(cls, data: Any) -> "CompanyInfo":
        if isinstance(data, str):
            return cls(code="", name=data)
        return cls(
            code=str(data.get("code", "")),
            name=data.get("name", ""),
            summary=data.get("summary", ""),
            tags=data.get("tags", []) or [],
            properties=data.get("properties", {}) or {},
        )


@dataclass
class ChainMap:
    """产业链数据地图（Layered Value Chain）。

    Attributes:
        value_chains: 产业包 → ValueChain（分层价值链，核心）
        companies: 产业包 → {Layer → {Item → [CompanyInfo]}}
        relations: 所有产业关系列表（Graph View，辅助）
        glossary: 产业包 → {名词 → 释义}
        chain_meta: 产业包 → 元信息（name/parent/description/keywords）
        chain_notes: 产业包 → README.md 内容
        chain_index: 产业包 → 所有条目名称集合
    """

    value_chains: dict[str, ValueChain] = field(default_factory=dict)
    companies: dict[str, dict[str, dict[str, list[CompanyInfo]]]] = field(default_factory=dict)
    relations: list[Relation] = field(default_factory=list)
    glossary: dict[str, dict[str, str]] = field(default_factory=dict)
    chain_meta: dict[str, dict[str, Any]] = field(default_factory=dict)
    chain_notes: dict[str, str] = field(default_factory=dict)
    chain_index: dict[str, set[str]] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # ValueChain 访问
    # ------------------------------------------------------------------
    def get_value_chain(self, chain: str) -> Optional[ValueChain]:
        return self.value_chains.get(chain)

    def find_chain_of(self, name: str) -> Optional[str]:
        """查找条目所属的产业包。"""
        for chain, names in self.chain_index.items():
            if name in names:
                return chain
        return None

    def find_value_chain_of(self, name: str) -> Optional[ValueChain]:
        """查找条目所属的 ValueChain。"""
        chain = self.find_chain_of(name)
        if chain is None:
            return None
        return self.value_chains.get(chain)

    # ------------------------------------------------------------------
    # 公司访问
    # ------------------------------------------------------------------
    def companies_of_item(self, chain: str, item_name: str) -> list[CompanyInfo]:
        """获取某产业包中某条目的所有公司。"""
        comp_map = self.companies.get(chain, {})
        result: list[CompanyInfo] = []
        for layer_items in comp_map.values():
            if item_name in layer_items:
                result.extend(layer_items[item_name])
        return result

    def get_company_by_name(self, name: str) -> Optional[CompanyInfo]:
        """按公司名查找（跨产业包）。"""
        for comp_map in self.companies.values():
            for layer_items in comp_map.values():
                for comps in layer_items.values():
                    for c in comps:
                        if c.name == name:
                            return c
        return None

    # ------------------------------------------------------------------
    # 词典访问
    # ------------------------------------------------------------------
    def get_glossary(self, chain: str) -> dict[str, str]:
        return self.glossary.get(chain, {})

    def lookup_term(self, name: str) -> str:
        """查找名词释义（跨产业包）。"""
        for terms in self.glossary.values():
            if name in terms:
                return terms[name]
        return ""

    # ------------------------------------------------------------------
    # 统计
    # ------------------------------------------------------------------
    @property
    def total_items(self) -> int:
        return sum(len(names) for names in self.chain_index.values())

    @property
    def total_companies(self) -> int:
        count = 0
        seen: set[str] = set()
        for comp_map in self.companies.values():
            for layer_items in comp_map.values():
                for comps in layer_items.values():
                    for c in comps:
                        if c.name not in seen:
                            seen.add(c.name)
                            count += 1
        return count


class ChainRepository:
    """产业包加载器。"""

    def __init__(self, chains_dir: Path):
        self.chains_dir = Path(chains_dir)

    def load(self) -> ChainMap:
        m = ChainMap()
        if not self.chains_dir.exists():
            return m

        for chain_dir in sorted(self.chains_dir.iterdir()):
            if not chain_dir.is_dir():
                continue
            self._load_chain(m, chain_dir)

        # 加载全局关系（合并所有产业包）
        return m

    def _load_chain(self, m: ChainMap, chain_dir: Path) -> None:
        chain_name = chain_dir.name

        # overview.yaml
        overview_path = chain_dir / "overview.yaml"
        if overview_path.exists():
            data = self._read_yaml(overview_path)
            m.chain_meta[chain_name] = data or {}

        # README.md
        readme_path = chain_dir / "README.md"
        if readme_path.exists():
            m.chain_notes[chain_name] = readme_path.read_text(encoding="utf-8")

        # layers.yaml（核心）
        layers_path = chain_dir / "layers.yaml"
        if layers_path.exists():
            data = self._read_yaml(layers_path) or {}
            vc = ValueChain.from_dict(data)
            m.value_chains[chain_name] = vc
            # 建立索引
            m.chain_index[chain_name] = set(vc.all_items())

        # companies.yaml（按 Layer 分组）
        companies_path = chain_dir / "companies.yaml"
        if companies_path.exists():
            data = self._read_yaml(companies_path) or {}
            comp_map: dict[str, dict[str, list[CompanyInfo]]] = {}
            for layer_id, items in data.items():
                if not isinstance(items, dict):
                    continue
                comp_map[layer_id] = {}
                for item_name, comp_list in items.items():
                    comps = [CompanyInfo.from_dict(c) for c in (comp_list or [])]
                    comp_map[layer_id][item_name] = comps
            m.companies[chain_name] = comp_map

        # relations/relations.yaml
        relations_path = chain_dir / "relations" / "relations.yaml"
        if relations_path.exists():
            data = self._read_yaml(relations_path) or {}
            for raw in data.get("relations", []) or []:
                m.relations.append(Relation.from_dict(raw))

        # glossary.yaml
        glossary_path = chain_dir / "glossary.yaml"
        if glossary_path.exists():
            data = self._read_yaml(glossary_path) or {}
            m.glossary[chain_name] = data.get("terms", {}) or {}

    def _read_yaml(self, path: Path) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
