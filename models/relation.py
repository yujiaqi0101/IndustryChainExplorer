r"""产业关系模型（PRD Part 04 双模型架构 - Model B）。

双模型架构核心思想：
    Model A：Structure（浏览树）- Tree，由 catalog.yaml 承担
    Model B：Relation（产业关系）- Graph，由 relations.yaml 承担

两种数据彻底分开：
    浏览结构（catalog.yaml）只负责左侧导航、面包屑
    产业关系（relations.yaml）只负责页面里的关系图

5 种产业关系（去掉结构关系 Parent/Child/Contains）：
    Upstream    上游   A 的上游是 B（光模块 上游 DSP）
    Downstream  下游   A 的下游是 B（光模块 下游 AI服务器）
    Supplies    供应   A 供应 B（DSP 供应 光模块）
    Uses        使用   A 使用 B（800G 使用 DSP）
    Related     关联   A 关联 B（CPO 关联 硅光）

数据维护原则（PRD Part 04 第九节）：
    原则1：人工维护优先（不 AI 自动生成）
    原则2：一个关系必须有来源（reference 列表）
    原则3：允许多个来源（可信度更高）

没有 reference 的关系不进入正式数据。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RelationType(str, Enum):
    """产业关系类型（PRD Part 04 双模型架构，5 种）。

    语义说明：
        Upstream    A 的上游是 B（A 依赖 B）
        Downstream  A 的下游是 B（B 依赖 A）
        Supplies    A 供应给 B（产品供应产品/技术）
        Uses        A 使用 B（产品使用产品/技术）
        Related     A 关联 B（任意关联）
    """

    UPSTREAM = "Upstream"
    DOWNSTREAM = "Downstream"
    SUPPLIES = "Supplies"
    USES = "Uses"
    RELATED = "Related"

    @property
    def label(self) -> str:
        """中文显示标签。"""
        return _LABELS.get(self.value, self.value)

    @property
    def category(self) -> str:
        """所属类别（用于 UI 分组）。"""
        if self in (RelationType.UPSTREAM, RelationType.SUPPLIES):
            return "上游关系"
        if self in (RelationType.DOWNSTREAM,):
            return "下游关系"
        if self == RelationType.USES:
            return "使用关系"
        return "关联关系"


# 中文标签映射
_LABELS: dict[str, str] = {
    "Upstream": "上游",
    "Downstream": "下游",
    "Supplies": "供应",
    "Uses": "使用",
    "Related": "关联",
}


@dataclass
class Relation:
    """产业关系（PRD Part 04 双模型架构 - Model B）。

    Attributes:
        source: 起点节点 ID
        target: 终点节点 ID
        relation: 关系类型（5 种之一）
        description: 关系描述（如"DSP是光模块核心芯片"）
        reference: 引用来源列表（允许多个，PRD Part 04 第九节）
            没有来源的关系不进入正式数据。
        properties: 附加属性（如 product/ratio/year 等）
    """

    source: str
    target: str
    relation: RelationType = RelationType.RELATED
    description: str = ""
    reference: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.relation, RelationType):
            self.relation = _parse_relation_type(self.relation)
        if isinstance(self.reference, str):
            self.reference = [self.reference] if self.reference else []
        elif self.reference is None:
            self.reference = []

    @property
    def label(self) -> str:
        """中文显示标签。"""
        return self.relation.label

    @property
    def has_reference(self) -> bool:
        """是否有引用来源（PRD Part 04：无来源不进入正式数据）。"""
        return bool(self.reference)

    @property
    def references_text(self) -> str:
        """引用来源文本（用于展示）。"""
        return "；".join(self.reference)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation.value,
            "label": self.label,
            "category": self.relation.category,
            "description": self.description,
            "reference": list(self.reference),
            "properties": dict(self.properties),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Relation":
        return cls(
            source=data["source"],
            target=data["target"],
            relation=data.get("relation", "Related"),
            description=data.get("description", ""),
            reference=data.get("reference", []) or [],
            properties=data.get("properties", {}) or {},
        )


def _parse_relation_type(value: Any) -> RelationType:
    """解析关系类型，兼容英文枚举名与中文标签。"""
    if isinstance(value, RelationType):
        return value
    s = str(value).strip()
    try:
        return RelationType(s)
    except ValueError:
        pass
    for key, label in _LABELS.items():
        if s == label:
            return RelationType(key)
    return RelationType.RELATED
