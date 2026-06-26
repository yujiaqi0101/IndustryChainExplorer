from __future__ import annotations

from ..base import PipelineStage
from ..context import BootstrapContext
from ..validators import CompositeValidator


class ValidateStage:
    name = "validate"

    def run(self, ctx: BootstrapContext) -> BootstrapContext:
        validator = CompositeValidator(ctx.ontology)
        validator.validate_all(ctx.objects, ctx.facts, ctx.validation_report)

        ctx.stats["validation_errors"] = ctx.validation_report.error_count()
        ctx.stats["validation_warnings"] = ctx.validation_report.warning_count()
        ctx.stats["quality_score"] = ctx.validation_report.quality_score()

        return ctx
