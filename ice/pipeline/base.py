from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

from .context import BootstrapContext


class PipelineStage(Protocol):
    name: str

    def run(self, ctx: BootstrapContext) -> BootstrapContext:
        ...


@dataclass
class StageResult:
    name: str
    duration_ms: float
    error: Exception | None = None


class Pipeline:
    def __init__(self, stages: list[PipelineStage]):
        self._stages = stages
        self._results: list[StageResult] = []

    @property
    def results(self) -> list[StageResult]:
        return self._results

    def run(self, ctx: BootstrapContext) -> BootstrapContext:
        self._results = []
        current_ctx = ctx
        for stage in self._stages:
            start = time.perf_counter()
            error = None
            try:
                current_ctx = stage.run(current_ctx)
            except Exception as e:
                error = e
                current_ctx.errors.append(e)
            duration = (time.perf_counter() - start) * 1000
            self._results.append(StageResult(
                name=stage.name,
                duration_ms=duration,
                error=error
            ))
            if error is not None:
                break
        return current_ctx

    def format_timings(self) -> str:
        lines = ["Pipeline Stage Timings:"]
        for r in self._results:
            status = "OK" if r.error is None else "ERROR"
            lines.append(f"  {r.name:20s} {r.duration_ms:8.2f}ms  {status}")
        return "\n".join(lines)
