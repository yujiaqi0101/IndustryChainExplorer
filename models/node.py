"""对象模型（PRD Part 04 双模型架构）。

双模型架构：
    Model A：Structure（浏览树）- catalog.yaml，Tree
    Model B：Relation（产业关系）- relations.yaml，Graph
    entities（products.yaml）只描述对象本身，不承担结构或关系。

统一对象 Node，type 只有 5 种：
    Industry     产业（光通信、PCB、GPU...）
    SubIndustry   子产业（光模块、CPO、高速连接器...）
    Product       产品（800G、1.6T、DSP、VCSEL...）
    Company       公司（中际旭创、新易盛...）
    Technology    技术（硅光、CPO、液冷...）

为什么不要 Material？
    硅片 / 铜 / 石英 本质也是 Product。
为什么不要 Concept？
    AI / 机器人 本质也是 Industry。
对象越少越稳定。

字段（PRD Part 04）：
    id       唯一标识
    name     显示名称
    type     类型（5 种之一）
    title    标题（较详细的显示名）
    summary  简介
    tags     标签（只是过滤器，不是 Node）
    properties  附加属性（code/market 等）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    """节点类型（PRD Part 04 规定 5 种）。

    语义说明：
        Industry     产业 - L1 一级产业（光通信、PCB、GPU、存储）
        SubIndustry   子产业 - L2 二级产业（光模块、CPO、高速连接器）
        Product       产品 - L3 产品（800G、1.6T、DSP、VCSEL）
        Company       公司 - 产业链上的公司节点
        Technology    技术 - 可被多个产品使用的技术
    """

    INDUSTRY = "Industry"        # 产业
    SUB_INDUSTRY = "SubIndustry"  # 子产业
    PRODUCT = "Product"          # 产品
    COMPANY = "Company"          # 公司
    TECHNOLOGY = "Technology"    # 技术


@dataclass
class Node:
    """节点（PRD Part 04 统一对象）。

    Attributes:
        id: 唯一标识（如 c_zjxc / p_dsp / optical_module）
        name: 显示名称（如 中际旭创 / DSP / 光模块）
        type: 节点类型（5 种之一）
        title: 标题（较详细的显示名，如"中际旭创股份有限公司"）
        summary: 简介（一句话描述）
        tags: 标签列表（只是过滤器，不是 Node）
        properties: 任意附加属性（code/market/category 等）
    """

    id: str
    name: str
    type: NodeType = NodeType.PRODUCT
    title: str = ""
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # 兼容字符串类型输入
        if not isinstance(self.type, NodeType):
            try:
                self.type = NodeType(self.type)
            except ValueError:
                self.type = NodeType.PRODUCT
        # 兼容旧 description 字段
        if not self.summary and "description" in self.properties:
            self.summary = self.properties["description"]

    @property
    def code(self) -> str:
        """公司股票代码（公司节点常用属性）。"""
        return self.properties.get("code", "")

    @property
    def description(self) -> str:
        """描述（兼容旧字段，优先 summary）。"""
        return self.summary or self.properties.get("description", "")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "title": self.title,
            "summary": self.summary,
            "tags": list(self.tags),
            "properties": dict(self.properties),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Node":
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            type=data.get("type", "Product"),
            title=data.get("title", ""),
            summary=data.get("summary", "") or data.get("description", ""),
            tags=data.get("tags", []) or [],
            properties=data.get("properties", {}) or {},
        )
