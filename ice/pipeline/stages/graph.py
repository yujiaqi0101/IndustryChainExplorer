from __future__ import annotations

from ...models import KnowledgeGraph
from ..base import PipelineStage
from ..context import BootstrapContext


class GraphStage:
    name = "graph"

    def run(self, ctx: BootstrapContext) -> BootstrapContext:
        graph = KnowledgeGraph()

        for oid, obj in ctx.objects.items():
            graph.add_object(obj)

        added_edges = 0
        for fid, fact in ctx.facts.items():
            if fact.subject in ctx.objects and fact.object in ctx.objects:
                graph.add_fact(fact)
                added_edges += 1

        ctx.graph = graph
        ctx.stats["graph_nodes"] = len(graph.objects)
        ctx.stats["graph_edges"] = added_edges
        return ctx
