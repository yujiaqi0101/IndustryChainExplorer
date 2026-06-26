from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ..base import PipelineStage
from ..context import BootstrapContext


class LoadStage:
    name = "load"

    def run(self, ctx: BootstrapContext) -> BootstrapContext:
        ctx.raw_objects = {}
        ctx.raw_facts = {}
        ctx.raw_references = {}
        ctx.raw_packages = {}

        for f in ctx.manifest.object_files:
            self._load_file(f, ctx.raw_objects)

        for f in ctx.manifest.reference_files:
            self._load_file(f, ctx.raw_references)

        for f in ctx.manifest.fact_files:
            self._load_file(f, ctx.raw_facts)

        for f in ctx.manifest.package_files:
            data = self._read_yaml(f)
            if data and "id" in data:
                ctx.raw_packages[data["id"]] = data

        if ctx.manifest.ontology_taxonomy and ctx.manifest.ontology_predicates:
            self._load_ontology(ctx)

        return ctx

    def _load_file(self, path: Path, target: dict[str, dict[str, Any]]) -> None:
        data = self._read_yaml(path)
        if not data:
            return
        if isinstance(data, list):
            for item in data:
                if "id" in item:
                    target[item["id"]] = item
        elif isinstance(data, dict):
            if "id" in data:
                target[data["id"]] = data

    def _read_yaml(self, path: Path) -> Any:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception:
            return None

    def _load_ontology(self, ctx: BootstrapContext) -> None:
        from ...models import Ontology, PredicateDefinition, TaxonomyCategory

        tax_data = self._read_yaml(ctx.manifest.ontology_taxonomy) or {}
        pred_data = self._read_yaml(ctx.manifest.ontology_predicates) or {}

        taxonomy = {}
        for cid, cdef in (tax_data.get("categories") or {}).items():
            taxonomy[cid] = TaxonomyCategory(
                id=cid,
                name=cdef.get("name", cid),
                parent=cdef.get("parent")
            )

        predicates = {}
        for pid, pdef in (pred_data.get("predicates") or {}).items():
            predicates[pid] = PredicateDefinition(
                id=pid,
                name=pdef.get("name", pid),
                subject=pdef.get("subject", []),
                object=pdef.get("object", []),
                inverse=pdef.get("inverse"),
                symmetric=pdef.get("symmetric", False)
            )

        ctx.ontology = Ontology(taxonomy=taxonomy, predicates=predicates)
