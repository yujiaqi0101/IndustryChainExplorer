"""Layout 模型（PRD Part 06 第十节）。

Layout 是配置，负责展示。对象不感知所属层。
Section 是运行时对象，不单独持久化（存在 layout.yaml 的 sections 列表里）。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator

from .object import validate_object_id


class Section(BaseModel):
    """布局分区（运行时对象）。

    object_ids 引用 Object ID（格式校验，存在性由 Repository 校验）。
    order 越大越上游。
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    object_ids: list[str] = []
    order: int = 0

    @field_validator("object_ids")
    @classmethod
    def _validate_ids(cls, v: list[str]) -> list[str]:
        for oid in v:
            validate_object_id(oid)
        return v


class Layout(BaseModel):
    """布局配置（持久化在 layout.yaml）。

    sections 按 order 升序排列。
    """

    model_config = ConfigDict(extra="forbid")

    sections: list[Section] = []

    def section_of(self, object_id: str) -> Section | None:
        """查找对象所在 Section。"""
        for sec in self.sections:
            if object_id in sec.object_ids:
                return sec
        return None

    def ordered_sections(self) -> list[Section]:
        """按 order 升序。"""
        return sorted(self.sections, key=lambda s: s.order)
