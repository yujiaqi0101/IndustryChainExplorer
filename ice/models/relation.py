"""Relation 模型（PRD Part 06 第五节 + 第七节）。

关系独立成对象，属于 Package。
upstream/downstream 不是关系类型，是方向——由 GraphService 按 type 语义计算，不落盘。
证据通过 references（reference 对象的 id 列表）绑定到关系（事实需要证据）。

字段名严格遵从 Part 06：from/to/type。
Python 中 from 是关键字，故属性名用 from_，YAML 字段名仍为 from（通过 alias 映射）。
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .object import validate_object_id


class RelationType(str, Enum):
    """关系类型（Part 06 第七节，10 种）。

    不含 upstream/downstream——它们是方向不是关系，由 GraphService 计算。
    """

    SUPPLY = "supply"            # from 供应 to
    USE = "use"                  # from 使用 to
    PRODUCE = "produce"          # from 生产 to
    INTEGRATE = "integrate"      # from 集成 to
    REPLACE = "replace"          # from 替代 to
    COMPETE = "compete"          # from 与 to 竞争
    BELONG_TO = "belong_to"      # from 属于 to
    RELATED_TO = "related_to"    # from 与 to 关联
    STANDARDIZE = "standardize"  # to 标准化 from
    RESEARCH = "research"        # from 研究 to


_RELATION_LABELS = {
    RelationType.SUPPLY: "供应",
    RelationType.USE: "使用",
    RelationType.PRODUCE: "生产",
    RelationType.INTEGRATE: "集成",
    RelationType.REPLACE: "替代",
    RelationType.COMPETE: "竞争",
    RelationType.BELONG_TO: "属于",
    RelationType.RELATED_TO: "关联",
    RelationType.STANDARDIZE: "标准化",
    RelationType.RESEARCH: "研究",
}


class Relation(BaseModel):
    """关系对象（Part 06 第七节）。

    from_/to 引用 Object ID（校验格式，跨文件存在性由 Repository 校验）。
    references 绑定证据，每项是一个 reference 对象的 id。
    weight 可选，表示关系强度（如供应占比）。
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=False, populate_by_name=True)

    id: str
    from_: str = Field(alias="from")
    to: str
    type: RelationType
    weight: float | None = None
    references: list[str] = []
    description: str = ""
    created_at: date | None = None
    updated_at: date | None = None

    @field_validator("from_", "to")
    @classmethod
    def _validate_endpoint(cls, v: str) -> str:
        return validate_object_id(v)

    @field_validator("type", mode="before")
    @classmethod
    def _normalize_type(cls, v: Any) -> Any:
        if isinstance(v, str):
            return RelationType(v)
        return v

    def label(self) -> str:
        return _RELATION_LABELS.get(self.type, self.type.value)
