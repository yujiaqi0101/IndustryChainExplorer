from __future__ import annotations

from ..base import PipelineStage
from ..context import BootstrapContext


class IndexStage:
    name = "index"

    def run(self, ctx: BootstrapContext) -> BootstrapContext:
        ctx.indexes.by_id = {}
        ctx.indexes.by_alias = {}
        ctx.indexes.by_name = {}
        ctx.indexes.by_tag = {}

        for oid, obj in ctx.objects.items():
            ctx.indexes.by_id[oid] = obj
            ctx.indexes.by_id[oid.lower()] = obj

            for name in obj.all_names():
                name_lower = name.lower()
                ctx.indexes.by_name[name_lower] = obj
                ctx.indexes.by_alias[name_lower] = obj

            for alias in obj.aliases:
                alias_lower = alias.lower()
                ctx.indexes.by_alias[alias_lower] = obj

            for tag in obj.tags:
                tag_lower = tag.lower()
                if tag_lower not in ctx.indexes.by_tag:
                    ctx.indexes.by_tag[tag_lower] = []
                ctx.indexes.by_tag[tag_lower].append(obj)

        ctx.stats["indexed_objects"] = len(ctx.indexes.by_id)
        ctx.stats["indexed_aliases"] = len(ctx.indexes.by_alias)
        ctx.stats["indexed_tags"] = len(ctx.indexes.by_tag)
        return ctx
