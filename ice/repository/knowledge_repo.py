from __future__ import annotations

from pathlib import Path
from typing import Any

from ..models import Fact, KnowledgeGraph, Object, Package, ValidationReport
from ..pipeline import BootstrapContext, Pipeline
from ..pipeline.stages import (
    DiscoverStage,
    GraphStage,
    IndexStage,
    LinkStage,
    LoadStage,
    ParseStage,
    ValidateStage,
)


class KnowledgeRepository:
    def __init__(self, root_path: str | Path):
        self.root_path = Path(root_path).resolve()
        self.ctx: BootstrapContext | None = None
        self._pipeline = Pipeline([
            DiscoverStage(),
            LoadStage(),
            ParseStage(),
            ValidateStage(),
            LinkStage(),
            IndexStage(),
            GraphStage(),
        ])

    def load(self, strict: bool = False) -> ValidationReport:
        self.ctx = BootstrapContext(root_path=self.root_path)
        self.ctx = self._pipeline.run(self.ctx)
        if strict and self.ctx.validation_report.has_errors():
            raise RuntimeError(
                f"Knowledge load failed with {self.ctx.validation_report.error_count()} errors\n"
                + self.ctx.validation_report.format()
            )
        return self.ctx.validation_report

    def is_loaded(self) -> bool:
        return self.ctx is not None

    def _ensure_loaded(self) -> BootstrapContext:
        if self.ctx is None:
            raise RuntimeError("Repository not loaded. Call load() first.")
        return self.ctx

    @property
    def graph(self) -> KnowledgeGraph:
        ctx = self._ensure_loaded()
        return ctx.graph

    @property
    def validation_report(self) -> ValidationReport:
        ctx = self._ensure_loaded()
        return ctx.validation_report

    @property
    def ontology(self):
        ctx = self._ensure_loaded()
        return ctx.ontology

    def get_object(self, object_id: str) -> Object | None:
        ctx = self._ensure_loaded()
        return ctx.indexes.by_id.get(object_id) or ctx.indexes.by_id.get(object_id.lower())

    def get_fact(self, fact_id: str) -> Fact | None:
        ctx = self._ensure_loaded()
        return ctx.facts.get(fact_id)

    def get_package(self, package_id: str) -> Package | None:
        ctx = self._ensure_loaded()
        return ctx.packages.get(package_id)

    def all_objects(self) -> list[Object]:
        ctx = self._ensure_loaded()
        return list(ctx.objects.values())

    def all_facts(self) -> list[Fact]:
        ctx = self._ensure_loaded()
        return list(ctx.facts.values())

    def all_packages(self) -> list[Package]:
        ctx = self._ensure_loaded()
        return list(ctx.packages.values())

    def search(self, query: str) -> list[Object]:
        ctx = self._ensure_loaded()
        q = query.lower().strip()
        if not q:
            return []
        results = []
        seen = set()
        if q in ctx.indexes.by_id:
            obj = ctx.indexes.by_id[q]
            results.append(obj)
            seen.add(obj.id)
        if q in ctx.indexes.by_name and q not in seen:
            obj = ctx.indexes.by_name[q]
            if obj.id not in seen:
                results.append(obj)
                seen.add(obj.id)
        if q in ctx.indexes.by_alias:
            obj = ctx.indexes.by_alias[q]
            if obj.id not in seen:
                results.append(obj)
                seen.add(obj.id)
        for name, obj in ctx.indexes.by_name.items():
            if q in name and obj.id not in seen:
                results.append(obj)
                seen.add(obj.id)
        for name, obj in ctx.indexes.by_alias.items():
            if q in name and obj.id not in seen:
                results.append(obj)
                seen.add(obj.id)
        return results

    def stats(self) -> dict[str, Any]:
        ctx = self._ensure_loaded()
        return dict(ctx.stats)

    def timings(self) -> str:
        return self._pipeline.format_timings()
