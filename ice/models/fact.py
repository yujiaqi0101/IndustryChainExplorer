from __future__ import annotations

import re
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from .object import validate_object_id


_FACT_ID_RE = re.compile(r"^fact_[0-9]+$")


def validate_fact_id(fid: str) -> str:
    if not isinstance(fid, str) or not _FACT_ID_RE.match(fid):
        raise ValueError(f"非法 Fact ID（须为 fact_00001 格式）: {fid!r}")
    return fid


class Fact(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    id: str
    subject: str
    predicate: str
    object: str
    statement: str = ""
    qualifiers: dict[str, Any] = {}
    citations: list[str] = []
    weight: float | None = None
    created_at: date | None = None
    updated_at: date | None = None

    subject_ref: Any = None
    object_ref: Any = None

    @field_validator("id")
    @classmethod
    def _validate_id(cls, v: str) -> str:
        return validate_fact_id(v)

    @field_validator("subject", "object")
    @classmethod
    def _validate_endpoint(cls, v: str) -> str:
        return validate_object_id(v)

    def triple(self) -> tuple[str, str, str]:
        return (self.subject, self.predicate, self.object)
