from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .fact import Fact
from .object import Object


@dataclass
class Edge:
    fact: Fact
    source: Object
    target: Object


@dataclass
class KnowledgeGraph:
    objects: dict[str, Object] = field(default_factory=dict)
    facts: dict[str, Fact] = field(default_factory=dict)
    _outgoing: dict[str, list[tuple[str, Fact]]] = field(default_factory=dict)
    _incoming: dict[str, list[tuple[str, Fact]]] = field(default_factory=dict)

    def add_fact(self, fact: Fact) -> None:
        sid = fact.subject
        oid = fact.object
        if sid not in self._outgoing:
            self._outgoing[sid] = []
        if oid not in self._incoming:
            self._incoming[oid] = []
        self._outgoing[sid].append((oid, fact))
        self._incoming[oid].append((sid, fact))
        self.facts[fact.id] = fact

    def add_object(self, obj: Object) -> None:
        self.objects[obj.id] = obj
        if obj.id not in self._outgoing:
            self._outgoing[obj.id] = []
        if obj.id not in self._incoming:
            self._incoming[obj.id] = []

    def outgoing(self, object_id: str) -> list[tuple[Object, Fact]]:
        result = []
        for tid, fact in self._outgoing.get(object_id, []):
            if tid in self.objects:
                result.append((self.objects[tid], fact))
        return result

    def incoming(self, object_id: str) -> list[tuple[Object, Fact]]:
        result = []
        for sid, fact in self._incoming.get(object_id, []):
            if sid in self.objects:
                result.append((self.objects[sid], fact))
        return result

    def neighbors(self, object_id: str) -> list[tuple[Object, Fact, bool]]:
        result = []
        for obj, fact in self.outgoing(object_id):
            result.append((obj, fact, True))
        for obj, fact in self.incoming(object_id):
            result.append((obj, fact, False))
        return result

    def get_object(self, object_id: str) -> Object | None:
        return self.objects.get(object_id)

    def get_fact(self, fact_id: str) -> Fact | None:
        return self.facts.get(fact_id)

    def facts_between(self, subject_id: str, object_id: str) -> list[Fact]:
        return [
            f for tid, f in self._outgoing.get(subject_id, [])
            if tid == object_id
        ]

    def all_edges(self) -> list[Edge]:
        edges = []
        for fid, fact in self.facts.items():
            src = self.objects.get(fact.subject)
            tgt = self.objects.get(fact.object)
            if src and tgt:
                edges.append(Edge(fact=fact, source=src, target=tgt))
        return edges
