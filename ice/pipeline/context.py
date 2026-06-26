from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..models import Fact, KnowledgeGraph, Object, Ontology, Package, ValidationReport


@dataclass
class FileManifest:
    object_files: list[Path] = field(default_factory=list)
    fact_files: list[Path] = field(default_factory=list)
    reference_files: list[Path] = field(default_factory=list)
    package_files: list[Path] = field(default_factory=list)
    ontology_taxonomy: Path | None = None
    ontology_predicates: Path | None = None


@dataclass
class SearchIndexes:
    by_id: dict[str, Object] = field(default_factory=dict)
    by_alias: dict[str, Object] = field(default_factory=dict)
    by_name: dict[str, Object] = field(default_factory=dict)
    by_tag: dict[str, list[Object]] = field(default_factory=dict)


@dataclass
class BootstrapContext:
    root_path: Path
    manifest: FileManifest = field(default_factory=FileManifest)
    ontology: Ontology = field(default_factory=Ontology)

    raw_objects: dict[str, dict[str, Any]] = field(default_factory=dict)
    raw_facts: dict[str, dict[str, Any]] = field(default_factory=dict)
    raw_references: dict[str, dict[str, Any]] = field(default_factory=dict)
    raw_packages: dict[str, dict[str, Any]] = field(default_factory=dict)

    objects: dict[str, Object] = field(default_factory=dict)
    facts: dict[str, Fact] = field(default_factory=dict)
    references: dict[str, Object] = field(default_factory=dict)
    packages: dict[str, Package] = field(default_factory=dict)

    indexes: SearchIndexes = field(default_factory=SearchIndexes)
    graph: KnowledgeGraph = field(default_factory=KnowledgeGraph)
    validation_report: ValidationReport = field(default_factory=ValidationReport)

    stats: dict[str, Any] = field(default_factory=dict)
    errors: list[Exception] = field(default_factory=list)

    @property
    def knowledge_path(self) -> Path:
        return self.root_path / "knowledge"

    @property
    def ontology_path(self) -> Path:
        return self.root_path / "ontology"

    @property
    def packages_path(self) -> Path:
        return self.root_path / "packages"
