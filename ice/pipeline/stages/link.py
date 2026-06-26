from __future__ import annotations

from ..base import PipelineStage
from ..context import BootstrapContext


class LinkStage:
    name = "link"

    def run(self, ctx: BootstrapContext) -> BootstrapContext:
        linked = 0
        for fid, fact in ctx.facts.items():
            fact.subject_ref = ctx.objects.get(fact.subject)
            fact.object_ref = ctx.objects.get(fact.object)
            if fact.subject_ref is not None and fact.object_ref is not None:
                linked += 1

        ctx.stats["facts_linked"] = linked
        ctx.stats["facts_unlinked"] = len(ctx.facts) - linked
        return ctx
