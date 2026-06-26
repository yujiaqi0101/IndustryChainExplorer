from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .object import ObjectKind


class TaxonomyCategory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    parent: str | None = None


class PredicateDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    subject: list[str] = []
    object: list[str] = []
    inverse: str | None = None
    symmetric: bool = False


class Ontology(BaseModel):
    model_config = ConfigDict(extra="forbid")

    taxonomy: dict[str, TaxonomyCategory] = Field(default_factory=dict)
    predicates: dict[str, PredicateDefinition] = Field(default_factory=dict)

    def has_predicate(self, predicate_id: str) -> bool:
        return predicate_id in self.predicates

    def get_predicate(self, predicate_id: str) -> PredicateDefinition | None:
        return self.predicates.get(predicate_id)

    def has_category(self, category_id: str) -> bool:
        return category_id in self.taxonomy

    def get_category(self, category_id: str) -> TaxonomyCategory | None:
        return self.taxonomy.get(category_id)

    def is_valid_predicate_for(self, predicate_id: str, subject_kind: str, object_kind: str) -> bool:
        pred = self.get_predicate(predicate_id)
        if pred is None:
            return False
        subj_ok = len(pred.subject) == 0 or subject_kind in pred.subject
        obj_ok = len(pred.object) == 0 or object_kind in pred.object
        return subj_ok and obj_ok

    def all_predicate_ids(self) -> list[str]:
        return list(self.predicates.keys())

    def all_category_ids(self) -> list[str]:
        return list(self.taxonomy.keys())

    def children_of(self, category_id: str) -> list[str]:
        return [cid for cid, cat in self.taxonomy.items() if cat.parent == category_id]
