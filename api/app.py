"""Industry Knowledge OS API (v2.0 - Knowledge-centric Architecture).

Knowledge OS v2.0: Knowledge (Objects/Facts) → Presentation (Packages/Layers) → Application (Loader/Indexer/Graph)

Endpoints:
    GET  /                          Service info
    GET  /stats                     Knowledge repository statistics
    GET  /validate                  Validation report
    GET  /search?q=关键词            Search objects by keyword
    GET  /objects                   List all objects
    GET  /objects/{object_id}       Get object detail
    GET  /facts                     List all facts
    GET  /facts/{fact_id}           Get fact detail
    GET  /neighbors/{object_id}     Get graph neighbors (relationships)
    GET  /packages                  List all packages/views
    GET  /packages/{package_id}     Get package/view detail

Launch:
    uvicorn api.app:app --reload
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ice.repository import KnowledgeRepository

repo = KnowledgeRepository(ROOT)
validation_report = repo.load(strict=False)

app = FastAPI(title="Industry Knowledge OS API", version="2.0.0")


def _serialize_obj(obj) -> dict[str, Any]:
    return {
        "id": obj.id,
        "kind": obj.kind.value,
        "name": obj.name,
        "aliases": obj.aliases,
        "summary": obj.summary,
        "tags": obj.tags,
        "deprecated_ids": obj.deprecated_ids,
    }


def _serialize_fact(fact) -> dict[str, Any]:
    result = {
        "id": fact.id,
        "subject": fact.subject,
        "predicate": fact.predicate,
        "object": fact.object,
        "statement": fact.statement,
        "qualifiers": fact.qualifiers,
        "citations": fact.citations,
        "weight": fact.weight,
    }
    if fact.subject_ref:
        result["subject_name"] = fact.subject_ref.name
    if fact.object_ref:
        result["object_name"] = fact.object_ref.name
    return result


@app.get("/")
def root() -> dict:
    return {
        "service": "Industry Knowledge OS",
        "version": "2.0.0",
        "architecture": "knowledge-centric",
        "validation": {
            "errors": validation_report.error_count(),
            "warnings": validation_report.warning_count(),
            "quality_score": validation_report.quality_score(),
        }
    }


@app.get("/stats")
def stats() -> dict:
    return repo.stats()


@app.get("/validate")
def validate() -> dict:
    return {
        "errors": validation_report.error_count(),
        "warnings": validation_report.warning_count(),
        "infos": validation_report.info_count(),
        "quality_score": validation_report.quality_score(),
        "issues": [str(i) for i in validation_report.issues],
    }


@app.get("/search")
def search(q: str = Query(..., description="Search keyword")) -> dict:
    results = repo.search(q)
    return {
        "query": q,
        "count": len(results),
        "results": [_serialize_obj(obj) for obj in results]
    }


@app.get("/objects")
def list_objects(
    kind: str | None = Query(None, description="Filter by kind (concept/organization/document)"),
    tag: str | None = Query(None, description="Filter by tag"),
) -> dict:
    objects = list(repo.all_objects().values())
    if kind:
        objects = [o for o in objects if o.kind.value == kind]
    if tag:
        objects = [o for o in objects if tag in o.tags]
    return {
        "count": len(objects),
        "objects": [_serialize_obj(obj) for obj in objects]
    }


@app.get("/objects/{object_id}")
def get_object(object_id: str) -> dict:
    obj = repo.get_object(object_id)
    if obj is None:
        resolved = repo.resolve_id(object_id)
        if resolved:
            obj = repo.get_object(resolved)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"Object not found: {object_id}")

    neighbors = []
    for nbr, fact, outgoing in repo.graph.neighbors(obj.id):
        neighbors.append({
            "direction": "outgoing" if outgoing else "incoming",
            "predicate": fact.predicate,
            "object": _serialize_obj(nbr),
            "fact_id": fact.id,
        })

    result = _serialize_obj(obj)
    result["neighbors"] = neighbors
    result["neighbor_count"] = len(neighbors)
    return result


@app.get("/facts")
def list_facts(
    predicate: str | None = Query(None, description="Filter by predicate"),
    subject: str | None = Query(None, description="Filter by subject ID"),
    object: str | None = Query(None, description="Filter by object ID"),
) -> dict:
    facts = list(repo.all_facts().values())
    if predicate:
        facts = [f for f in facts if f.predicate == predicate]
    if subject:
        facts = [f for f in facts if f.subject == subject]
    if object:
        facts = [f for f in facts if f.object == object]
    return {
        "count": len(facts),
        "facts": [_serialize_fact(f) for f in facts]
    }


@app.get("/facts/{fact_id}")
def get_fact(fact_id: str) -> dict:
    fact = repo.get_fact(fact_id)
    if fact is None:
        raise HTTPException(status_code=404, detail=f"Fact not found: {fact_id}")
    return _serialize_fact(fact)


@app.get("/neighbors/{object_id}")
def get_neighbors(
    object_id: str,
    direction: str = Query("both", description="Direction: both/outgoing/incoming"),
) -> dict:
    obj = repo.get_object(object_id)
    if obj is None:
        resolved = repo.resolve_id(object_id)
        if resolved:
            obj = repo.get_object(resolved)
            object_id = resolved
    if obj is None:
        raise HTTPException(status_code=404, detail=f"Object not found: {object_id}")

    neighbors = []
    if direction in ("both", "outgoing"):
        for nbr, fact in repo.graph.outgoing(object_id):
            neighbors.append({
                "direction": "outgoing",
                "predicate": fact.predicate,
                "object": _serialize_obj(nbr),
                "fact_id": fact.id,
                "statement": fact.statement,
            })
    if direction in ("both", "incoming"):
        for nbr, fact in repo.graph.incoming(object_id):
            neighbors.append({
                "direction": "incoming",
                "predicate": fact.predicate,
                "object": _serialize_obj(nbr),
                "fact_id": fact.id,
                "statement": fact.statement,
            })

    return {
        "object": _serialize_obj(obj),
        "count": len(neighbors),
        "neighbors": neighbors,
    }


@app.get("/packages")
def list_packages() -> dict:
    packages = repo.all_packages()
    return {
        "count": len(packages),
        "packages": [
            {
                "id": pkg.id,
                "name": pkg.name,
                "version": pkg.version,
                "description": pkg.description,
                "entry_points": pkg.entry_points,
                "layers": [
                    {"id": layer.id, "name": layer.name, "order": layer.order}
                    for layer in pkg.layers
                ],
            }
            for pkg in packages.values()
        ]
    }


@app.get("/packages/{package_id}")
def get_package(package_id: str) -> dict:
    pkg = repo.get_package(package_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail=f"Package not found: {package_id}")

    return {
        "id": pkg.id,
        "name": pkg.name,
        "version": pkg.version,
        "description": pkg.description,
        "entry_points": pkg.entry_points,
        "layers": [
            {
                "id": layer.id,
                "name": layer.name,
                "categories": layer.categories,
                "order": layer.order,
                "object_ids": [
                    oid for oid, obj in repo.all_objects().items()
                    if any(c in obj.tags for c in layer.categories)
                ],
            }
            for layer in pkg.layers
        ],
    }
