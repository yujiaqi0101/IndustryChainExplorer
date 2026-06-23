"""核心数据模型（Layered Value Chain 分层价值链）。

Industry Layer Explorer 的核心模型是 Layer（层），不是 Tree 也不是 Graph。

分层价值链（Layered Value Chain）：
    Layer / LayerItem / ValueChain
        负责：产业分层视图（默认主视图）
        数据：layers.yaml
        每个产业自定义层数（光模块4层，机器人5层，半导体6层）

产业关系（辅助视图）：
    Relation / RelationType
        负责：关系图（Graph View，第二视图）
        数据：relations.yaml

对象（实体）：
    Node / NodeType
        负责：对象本身属性
        数据：layers.yaml 内嵌 / glossary.yaml 释义
"""

from .layer import Layer, LayerItem, ValueChain
from .node import Node, NodeType
from .relation import Relation, RelationType
from .tag import Tag, get_tag_color, build_tags_with_count

__all__ = [
    "Layer",
    "LayerItem",
    "ValueChain",
    "Node",
    "NodeType",
    "Relation",
    "RelationType",
    "Tag",
    "get_tag_color",
    "build_tags_with_count",
]
