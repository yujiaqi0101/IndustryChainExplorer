from __future__ import annotations

from typing import Any

from ..models import Fact, Object, ObjectKind, Ontology, ValidationReport


class SchemaValidator:
    def validate(self, objects: dict[str, Object], facts: dict[str, Fact], report: ValidationReport) -> None:
        for oid, obj in objects.items():
            if obj.kind == ObjectKind.ORGANIZATION:
                if not obj.organization_type and obj.code:
                    report.add_warning(
                        "Organization has stock code but no organization_type",
                        source_type="object", source_id=oid
                    )
            if obj.kind == ObjectKind.DOCUMENT:
                if not obj.document_type:
                    report.add_warning(
                        "Document has no document_type",
                        source_type="object", source_id=oid
                    )

        for fid, fact in facts.items():
            if fact.weight is not None and (fact.weight < 0 or fact.weight > 1):
                report.add_error(
                    f"weight must be between 0 and 1, got {fact.weight}",
                    source_type="fact", source_id=fid, field_name="weight"
                )


class OntologyValidator:
    def __init__(self, ontology: Ontology):
        self.ontology = ontology

    def validate(self, objects: dict[str, Object], facts: dict[str, Fact], report: ValidationReport) -> None:
        for fid, fact in facts.items():
            pred = self.ontology.get_predicate(fact.predicate)
            if pred is None:
                report.add_error(
                    f"Unknown predicate: {fact.predicate}",
                    source_type="fact", source_id=fid, field_name="predicate"
                )
                continue

            subj = objects.get(fact.subject)
            obj = objects.get(fact.object)
            if subj is None or obj is None:
                continue

            if not self.ontology.is_valid_predicate_for(
                fact.predicate, subj.kind.value, obj.kind.value
            ):
                allowed_subj = pred.subject or ["*"]
                allowed_obj = pred.object or ["*"]
                report.add_error(
                    f"Predicate '{fact.predicate}' not allowed for "
                    f"subject kind={subj.kind.value} -> object kind={obj.kind.value}. "
                    f"Allowed: subject={allowed_subj}, object={allowed_obj}",
                    source_type="fact", source_id=fid
                )


class ReferenceValidator:
    def validate(self, objects: dict[str, Object], facts: dict[str, Fact], report: ValidationReport) -> None:
        for fid, fact in facts.items():
            if fact.subject not in objects:
                report.add_error(
                    f"Subject not found: {fact.subject}",
                    source_type="fact", source_id=fid, field_name="subject"
                )
            if fact.object not in objects:
                report.add_error(
                    f"Object not found: {fact.object}",
                    source_type="fact", source_id=fid, field_name="object"
                )
            for cid in fact.citations:
                if cid not in objects:
                    report.add_error(
                        f"Citation reference not found: {cid}",
                        source_type="fact", source_id=fid, field_name="citations"
                    )
                    continue
                cited = objects[cid]
                if not cited.is_document():
                    report.add_error(
                        f"Citation {cid} is not a document (kind={cited.kind.value})",
                        source_type="fact", source_id=fid, field_name="citations"
                    )

        deprecated_map = {}
        for oid, obj in objects.items():
            for did in obj.deprecated_ids:
                deprecated_map[did] = oid
                if did in objects:
                    report.add_error(
                        f"Deprecated ID '{did}' exists as active object",
                        source_type="object", source_id=oid
                    )


class BusinessValidator:
    def validate(self, objects: dict[str, Object], facts: dict[str, Fact], report: ValidationReport) -> None:
        seen_triples: dict[tuple[str, str, str], str] = {}

        for fid, fact in facts.items():
            if fact.subject == fact.object:
                report.add_error(
                    "Self-referential fact (subject == object)",
                    source_type="fact", source_id=fid
                )
                continue

            triple = fact.triple()
            if triple in seen_triples:
                report.add_error(
                    f"Duplicate fact (same as {seen_triples[triple]})",
                    source_type="fact", source_id=fid
                )
            else:
                seen_triples[triple] = fid

        self._check_part_of_cycles(objects, facts, report)

    def _check_part_of_cycles(self, objects: dict[str, Object], facts: dict[str, Fact], report: ValidationReport) -> None:
        parent_of: dict[str, set[str]] = {}
        for fid, fact in facts.items():
            if fact.predicate == "part_of":
                if fact.subject not in parent_of:
                    parent_of[fact.subject] = set()
                parent_of[fact.subject].add(fact.object)

        visited = set()
        path = set()

        def dfs(node: str, edge_fid: str = "") -> bool:
            if node in path:
                report.add_error(
                    f"Cycle detected in part_of hierarchy involving '{node}'",
                    source_type="fact", source_id=edge_fid
                )
                return True
            if node in visited:
                return False
            visited.add(node)
            path.add(node)
            for parent in parent_of.get(node, set()):
                if parent in objects:
                    for pfid, pf in facts.items():
                        if pf.triple() == (node, "part_of", parent):
                            if dfs(parent, pfid):
                                return True
                            break
            path.remove(node)
            return False

        for node in parent_of:
            if node not in visited:
                dfs(node)


class QualityValidator:
    def validate(self, objects: dict[str, Object], facts: dict[str, Fact], report: ValidationReport) -> None:
        for oid, obj in objects.items():
            if len(obj.summary) < 10:
                report.add_warning(
                    f"Summary too short ({len(obj.summary)} chars), recommended >= 10",
                    source_type="object", source_id=oid, field_name="summary"
                )
            if len(obj.aliases) == 0 and len(obj.name) > 3:
                report.add_info(
                    "No aliases defined",
                    source_type="object", source_id=oid, field_name="aliases"
                )
            if len(obj.tags) == 0:
                report.add_info(
                    "No tags defined",
                    source_type="object", source_id=oid, field_name="tags"
                )

        for fid, fact in facts.items():
            if len(fact.statement) < 5:
                report.add_warning(
                    f"Statement too short or missing ({len(fact.statement)} chars)",
                    source_type="fact", source_id=fid, field_name="statement"
                )
            if len(fact.citations) == 0:
                report.add_warning(
                    "No citations (evidences) provided",
                    source_type="fact", source_id=fid, field_name="citations"
                )


class CompositeValidator:
    def __init__(self, ontology: Ontology):
        self.schema = SchemaValidator()
        self.ontology_validator = OntologyValidator(ontology)
        self.reference = ReferenceValidator()
        self.business = BusinessValidator()
        self.quality = QualityValidator()

    def validate_all(self, objects: dict[str, Object], facts: dict[str, Fact], report: ValidationReport) -> None:
        self.schema.validate(objects, facts, report)
        if report.has_errors():
            return
        self.ontology_validator.validate(objects, facts, report)
        self.reference.validate(objects, facts, report)
        self.business.validate(objects, facts, report)
        self.quality.validate(objects, facts, report)
