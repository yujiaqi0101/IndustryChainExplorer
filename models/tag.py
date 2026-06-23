"""Tag 模型（PRD Part 04）。

Tag 重新定义：
    - Tag 不是 Node
    - Tag 只是过滤器
    - Tag 只有 name 和 color
    - Tag 没有 Relation

例如：
    AI          #蓝色
    算力        #绿色
    高速        #橙色
    海外        #紫色
    800G        #红色
    热门        #黄色

Tag 的作用：
    点击 Tag -> 立即过滤出所有相关 Node
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# 预设颜色（按主题分组）
DEFAULT_COLORS: dict[str, str] = {
    # 主题色
    "AI": "#3B82F6",          # 蓝色
    "算力": "#10B981",        # 绿色
    "通信": "#06B6D4",        # 青色
    "高速": "#F59E0B",        # 橙色
    "海外": "#8B5CF6",        # 紫色
    "国内": "#EF4444",        # 红色
    "热门": "#F97316",        # 橙红色
    # 速率
    "400G": "#3B82F6",
    "800G": "#EF4444",
    "1.6T": "#DC2626",
    # 行业
    "半导体": "#0EA5E9",
    "机器人": "#8B5CF6",
    "消费电子": "#F59E0B",
    "新能源": "#10B981",
}

# 默认颜色（未在预设表中的 Tag）
DEFAULT_TAG_COLOR = "#6B7280"  # 灰色


@dataclass
class Tag:
    """标签（PRD Part 04：只是过滤器，不是 Node）。

    Attributes:
        name: 标签名称（如 "AI" / "算力" / "800G"）
        color: 显示颜色（hex 格式，如 "#3B82F6"）
        count: 关联 Node 数量（用于展示）
    """

    name: str
    color: str = ""
    count: int = 0

    def __post_init__(self) -> None:
        if not self.color:
            self.color = DEFAULT_COLORS.get(self.name, DEFAULT_TAG_COLOR)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "color": self.color,
            "count": self.count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Tag":
        return cls(
            name=data["name"],
            color=data.get("color", ""),
            count=data.get("count", 0),
        )


def get_tag_color(name: str) -> str:
    """获取标签颜色（未配置则返回默认色）。"""
    return DEFAULT_COLORS.get(name, DEFAULT_TAG_COLOR)


def build_tags_with_count(
    tag_names: list[str], tag_counts: dict[str, int]
) -> list[Tag]:
    """根据标签名列表和计数构建 Tag 列表。"""
    return [Tag(name=name, count=tag_counts.get(name, 0)) for name in tag_names]
