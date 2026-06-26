from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from ...models import Fact, Object, ObjectKind, Package
from ..base import PipelineStage
from ..context import BootstrapContext


class ParseStage:
    name = "parse"

    def run(self, ctx: BootstrapContext) -> BootstrapContext:
        ctx.objects = {}
        ctx.facts = {}
        ctx.references = {}
        ctx.packages = {}

        for oid, data in ctx.raw_objects.items():
            obj = self._parse_object(oid, data, ctx)
            if obj is not None:
                ctx.objects[oid] = obj

        for rid, data in ctx.raw_references.items():
            doc_data = dict(data)
            doc_data["kind"] = ObjectKind.DOCUMENT.value
            obj = self._parse_object(rid, doc_data, ctx)
            if obj is not None:
                ctx.objects[rid] = obj
                ctx.references[rid] = obj

        for fid, data in ctx.raw_facts.items():
            fact = self._parse_fact(fid, data, ctx)
            if fact is not None:
                ctx.facts[fid] = fact

        for pid, data in ctx.raw_packages.items():
            pkg = self._parse_package(pid, data, ctx)
            if pkg is not None:
                ctx.packages[pid] = pkg

        ctx.stats["objects_parsed"] = len(ctx.objects)
        ctx.stats["facts_parsed"] = len(ctx.facts)
        ctx.stats["packages_parsed"] = len(ctx.packages)

        return ctx

    def _parse_object(self, oid: str, data: dict[str, Any], ctx: BootstrapContext) -> Object | None:
        try:
            if "id" not in data:
                data["id"] = oid
            return Object(**data)
        except ValidationError as e:
            for err in e.errors():
                loc = ".".join(str(l) for l in err.get("loc", []))
                ctx.validation_report.add_error(
                    f"Schema error: {err['msg']}",
                    source_type="object",
                    source_id=oid,
                    field_name=loc
                )
            return None

    def _parse_fact(self, fid: str, data: dict[str, Any], ctx: BootstrapContext) -> Fact | None:
        try:
            if "id" not in data:
                data["id"] = fid
            return Fact(**data)
        except ValidationError as e:
            for err in e.errors():
                loc = ".".join(str(l) for l in err.get("loc", []))
                ctx.validation_report.add_error(
                    f"Schema error: {err['msg']}",
                    source_type="fact",
                    source_id=fid,
                    field_name=loc
                )
            return None

    def _parse_package(self, pid: str, data: dict[str, Any], ctx: BootstrapContext) -> Package | None:
        try:
            if "id" not in data:
                data["id"] = pid
            return Package(**data)
        except ValidationError as e:
            for err in e.errors():
                loc = ".".join(str(l) for l in err.get("loc", []))
                ctx.validation_report.add_error(
                    f"Schema error: {err['msg']}",
                    source_type="package",
                    source_id=pid,
                    field_name=loc
                )
            return None
