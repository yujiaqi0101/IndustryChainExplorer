"""分层价值链模型（Layered Value Chain）。

Industry Layer Explorer 的核心模型不是 Tree，也不是 Graph，
而是 Layer（层）。

为什么是 Layer？
    用户搜索"光模块"，真正想看的不是 DSP→光模块→AI服务器 的 Graph，
    而是整条价值链的分层视图：
        Application  AI服务器 / 交换机 / 数据中心
        System       800G / 1.6T / CPO
        Component    DSP / EML / VCSEL
        Material     硅片 / PCB / 石英

    Layer 比关系图更符合人的认知：一眼看清整个产业。

Layer 是产业自定义的：
    光模块：Application / System / Component / Material（4 层）
    机器人：Application / Machine / Module / Component / Material（5 层）
    半导体：EDA / IP / Design / Foundry / Packaging / Application（6 层）
    每个产业自己定义自己的 Layer，系统不固定层数。

视图优先级：
    Layer View（默认）- 主视图，首页直接展示分层
    Graph View（切换）- 辅助视图，关系图作为第二视图
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LayerItem:
    """层内条目（如 DSP / EML / 800G光模块）。

    Attributes:
        name: 显示名称（如 DSP）
        summary: 简介（可选，可来自 glossary.yaml）
        tags: 标签
        properties: 附加属性
    """

    name: str
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "summary": self.summary,
            "tags": list(self.tags),
            "properties": dict(self.properties),
        }

    @classmethod
    def from_dict(cls, data: Any) -> "LayerItem":
        # 支持两种格式：字符串 或 dict
        if isinstance(data, str):
            return cls(name=data)
        return cls(
            name=data.get("name", ""),
            summary=data.get("summary", ""),
            tags=data.get("tags", []) or [],
            properties=data.get("properties", {}) or {},
        )


@dataclass
class Layer:
    """一个层（如 Application / System / Component / Material）。

    Attributes:
        id: 层标识（如 application / system / component / material）
        title: 层标题（如 应用层 / 系统层 / 器件层 / 材料层）
        order: 顺序（从上到下，0 开始）
        items: 层内条目列表
    """

    id: str
    title: str
    order: int = 0
    items: list[LayerItem] = field(default_factory=list)

    @property
    def item_names(self) -> list[str]:
        """层内所有条目名称。"""
        return [it.name for it in self.items]

    def has(self, name: str) -> bool:
        """是否包含某条目。"""
        return any(it.name == name for it in self.items)

    def find(self, name: str) -> Optional[LayerItem]:
        """查找条目。"""
        for it in self.items:
            if it.name == name:
                return it
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "order": self.order,
            "items": [it.to_dict() for it in self.items],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], order: int = 0) -> "Layer":
        raw_items = data.get("items", []) or []
        return cls(
            id=data.get("id", data.get("name", "")),
            title=data.get("title", data.get("name", "")),
            order=data.get("order", order),
            items=[LayerItem.from_dict(it) for it in raw_items],
        )


@dataclass
class ValueChain:
    """价值链（一个产业的完整分层视图）。

    Attributes:
        industry: 产业名（如 光模块）
        layers: 层列表（从上到下：Application → ... → Material）
    """

    industry: str = ""
    layers: list[Layer] = field(default_factory=list)

    @property
    def layer_count(self) -> int:
        return len(self.layers)

    def find_layer(self, layer_id: str) -> Optional[Layer]:
        """按 id 查找层。"""
        for layer in self.layers:
            if layer.id == layer_id:
                return layer
        return None

    def find_item(self, name: str) -> Optional[tuple[Layer, LayerItem]]:
        """查找条目所在层。返回 (Layer, LayerItem)。"""
        for layer in self.layers:
            item = layer.find(name)
            if item is not None:
                return layer, item
        return None

    def layer_of(self, name: str) -> Optional[Layer]:
        """条目所在的层。"""
        result = self.find_item(name)
        return result[0] if result else None

    def all_items(self) -> list[str]:
        """所有层所有条目名称。"""
        names: list[str] = []
        for layer in self.layers:
            names.extend(layer.item_names)
        return names

    def upstream_layers(self, name: str) -> list[Layer]:
        """条目所在层之上的所有层（上游方向）。

        Layer 顺序：Application(0) → System(1) → Component(2) → Material(3)
        上游 = order 更大的层（材料是器件的上游）。
        """
        current = self.layer_of(name)
        if current is None:
            return []
        return [l for l in self.layers if l.order > current.order]

    def downstream_layers(self, name: str) -> list[Layer]:
        """条目所在层之下的所有层（下游方向）。

        下游 = order 更小的层（应用是器件的下游）。
        """
        current = self.layer_of(name)
        if current is None:
            return []
        return [l for l in self.layers if l.order < current.order]

    def to_dict(self) -> dict[str, Any]:
        return {
            "industry": self.industry,
            "layers": [l.to_dict() for l in self.layers],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValueChain":
        industry = data.get("industry", data.get("name", ""))
        raw_layers = data.get("layers", []) or []
        layers: list[Layer] = []
        for idx, raw in enumerate(raw_layers):
            layers.append(Layer.from_dict(raw, order=idx))
        return cls(industry=industry, layers=layers)
