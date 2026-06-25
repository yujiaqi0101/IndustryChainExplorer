"""Package 模型（PRD Part 06 第九节）。

Package 是产业视图容器，聚合 objects + relations + layout。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator

from .layout import Layout
from .object import Object, validate_object_id
from .relation import Relation


class Package(BaseModel):
    """产业包。

    dir_name 是磁盘目录名（也是 Package ID）。
    objects/relations/layout 是加载后的领域对象。
    readme 是 README.md 原文。
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    id: str
    name: str
    industry: str = ""
    description: str = ""
    version: str = "1.0.0"
    keywords: list[str] = []

    objects: list[Object] = []
    relations: list[Relation] = []
    layout: Layout | None = None
    readme: str = ""
    dir_name: str = ""

    @field_validator("id")
    @classmethod
    def _validate_id(cls, v: str) -> str:
        return validate_object_id(v)

    def object_ids(self) -> list[str]:
        return [o.id for o in self.objects]

    def get_object(self, object_id: str) -> Object | None:
        return next((o for o in self.objects if o.id == object_id), None)

    def relations_of(self, object_id: str) -> list[Relation]:
        return [r for r in self.relations if r.from_ == object_id or r.to == object_id]

    def section_of(self, object_id: str):
        if self.layout is None:
            return None
        return self.layout.section_of(object_id)
