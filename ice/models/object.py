"""Object 模型（PRD Part 06 第二节）。

系统根对象。kind 决定类型，一套模型。
对象只描述自己，不存任何关系字段（关系见 relation.py）。

ID 规范（Part 06 第二节）：全小写、下划线、无空格无中文。正则 ^[a-z][a-z0-9_]*$。
"""

from __future__ import annotations

import re
from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


# Object ID 校验正则：小写字母开头，只含小写字母/数字/下划线
_OBJECT_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def validate_object_id(oid: str) -> str:
    """校验 Object ID 规范，通过返回原值，不通过抛 ValueError。"""
    if not isinstance(oid, str) or not _OBJECT_ID_RE.match(oid):
        raise ValueError(f"非法 Object ID（须全小写、下划线、无空格无中文）: {oid!r}")
    return oid


class ObjectKind(str, Enum):
    """对象类型（Part 06 第三节，6 种）。"""

    ENTITY = "entity"
    COMPANY = "company"
    GLOSSARY = "glossary"
    REFERENCE = "reference"
    ORGANIZATION = "organization"
    STANDARD = "standard"


class EntityType(str, Enum):
    """entity 子类型（Part 06 第四节，6 种）。"""

    INDUSTRY = "industry"
    PRODUCT = "product"
    COMPONENT = "component"
    MATERIAL = "material"
    TECHNOLOGY = "technology"
    APPLICATION = "application"


# entity_type 中文标签
_ENTITY_TYPE_LABELS = {
    EntityType.INDUSTRY: "产业",
    EntityType.PRODUCT: "产品",
    EntityType.COMPONENT: "器件",
    EntityType.MATERIAL: "材料",
    EntityType.TECHNOLOGY: "技术",
    EntityType.APPLICATION: "应用",
}

# kind 中文标签
_KIND_LABELS = {
    ObjectKind.ENTITY: "实体",
    ObjectKind.COMPANY: "公司",
    ObjectKind.GLOSSARY: "术语",
    ObjectKind.REFERENCE: "文献",
    ObjectKind.ORGANIZATION: "机构",
    ObjectKind.STANDARD: "标准",
}


class Object(BaseModel):
    """统一对象模型（Part 06 第二节）。

    所有对象共用一套字段，kind 决定类型，entity_type 仅 entity 使用。
    对象不存任何关系字段。
    各 kind 专属可选字段：company(code/market)、reference(title/author/published_date)、
    standard(version)。
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    id: str
    kind: ObjectKind
    name: str
    aliases: list[str] = []
    summary: str = ""
    tags: list[str] = []

    # entity 专属（kind=entity 时必填，其余禁用——由 Validator 校验）
    entity_type: EntityType | None = None

    # company 专属（可选，仅 company 用）
    code: str = ""
    market: str = ""

    # reference 专属（可选，仅 reference 用）
    title: str = ""
    author: str = ""
    published_date: str = ""

    # standard 专属（可选，仅 standard 用）
    version: str = ""

    created_at: date | None = None
    updated_at: date | None = None

    @field_validator("id")
    @classmethod
    def _validate_id(cls, v: str) -> str:
        return validate_object_id(v)

    @field_validator("kind", mode="before")
    @classmethod
    def _normalize_kind(cls, v: Any) -> Any:
        if isinstance(v, str):
            return ObjectKind(v)
        return v

    @field_validator("entity_type", mode="before")
    @classmethod
    def _normalize_entity_type(cls, v: Any) -> Any:
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return EntityType(v)
        return v

    def kind_label(self) -> str:
        return _KIND_LABELS.get(self.kind, self.kind.value)

    def entity_type_label(self) -> str:
        if self.entity_type is None:
            return ""
        return _ENTITY_TYPE_LABELS.get(self.entity_type, self.entity_type.value)

    def is_entity(self) -> bool:
        return self.kind == ObjectKind.ENTITY

    def is_company(self) -> bool:
        return self.kind == ObjectKind.COMPANY

    def is_reference(self) -> bool:
        return self.kind == ObjectKind.REFERENCE
