from __future__ import annotations

import re
from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


_OBJECT_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def validate_object_id(oid: str) -> str:
    if not isinstance(oid, str) or not _OBJECT_ID_RE.match(oid):
        raise ValueError(f"非法 Object ID（须全小写、下划线、无空格无中文）: {oid!r}")
    return oid


class ObjectKind(str, Enum):
    CONCEPT = "concept"
    ORGANIZATION = "organization"
    DOCUMENT = "document"


_KIND_LABELS = {
    ObjectKind.CONCEPT: "概念",
    ObjectKind.ORGANIZATION: "组织",
    ObjectKind.DOCUMENT: "文献",
}


class Object(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    id: str
    kind: ObjectKind
    name: str
    aliases: list[str] = []
    summary: str = ""
    tags: list[str] = []
    deprecated_ids: list[str] = []

    organization_type: str = ""
    code: str = ""
    market: str = ""

    document_type: str = ""
    title: str = ""
    author: str = ""
    published_date: str = ""
    source_url: str = ""

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

    def kind_label(self) -> str:
        return _KIND_LABELS.get(self.kind, self.kind.value)

    def is_concept(self) -> bool:
        return self.kind == ObjectKind.CONCEPT

    def is_organization(self) -> bool:
        return self.kind == ObjectKind.ORGANIZATION

    def is_document(self) -> bool:
        return self.kind == ObjectKind.DOCUMENT

    def all_names(self) -> list[str]:
        names = [self.name]
        names.extend(self.aliases)
        return [n for n in names if n]
