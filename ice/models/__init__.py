"""领域模型（PRD Part 06 第一~七节）。"""

from .object import Object, ObjectKind, EntityType, validate_object_id
from .relation import Relation, RelationType
from .layout import Layout, Section
from .package import Package

__all__ = [
    "Object",
    "ObjectKind",
    "EntityType",
    "validate_object_id",
    "Relation",
    "RelationType",
    "Layout",
    "Section",
    "Package",
]
