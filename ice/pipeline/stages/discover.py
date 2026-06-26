from __future__ import annotations

from pathlib import Path

from ..base import PipelineStage
from ..context import BootstrapContext


class DiscoverStage:
    name = "discover"

    def run(self, ctx: BootstrapContext) -> BootstrapContext:
        kp = ctx.knowledge_path
        op = ctx.ontology_path
        pp = ctx.packages_path

        obj_dir = kp / "objects"
        fact_dir = kp / "facts"
        ref_dir = kp / "references"

        ctx.manifest.object_files = self._find_yaml(obj_dir)
        ctx.manifest.fact_files = self._find_yaml(fact_dir)
        ctx.manifest.reference_files = self._find_yaml(ref_dir)

        ctx.manifest.package_files = []
        if pp.exists():
            for pkg_dir in pp.iterdir():
                if pkg_dir.is_dir():
                    pkg_yaml = pkg_dir / "package.yaml"
                    if pkg_yaml.exists():
                        ctx.manifest.package_files.append(pkg_yaml)

        tax_file = op / "taxonomy.yaml"
        pred_file = op / "predicates.yaml"
        ctx.manifest.ontology_taxonomy = tax_file if tax_file.exists() else None
        ctx.manifest.ontology_predicates = pred_file if pred_file.exists() else None

        ctx.stats["object_files_count"] = len(ctx.manifest.object_files)
        ctx.stats["fact_files_count"] = len(ctx.manifest.fact_files)
        ctx.stats["reference_files_count"] = len(ctx.manifest.reference_files)
        ctx.stats["package_count"] = len(ctx.manifest.package_files)

        return ctx

    def _find_yaml(self, directory: Path) -> list[Path]:
        if not directory.exists():
            return []
        return sorted([
            f for f in directory.rglob("*.yaml")
            if f.is_file()
        ])
