from __future__ import annotations


class KnowledgeError(Exception):
    pass


class SchemaError(KnowledgeError):
    pass


class OntologyError(KnowledgeError):
    pass


class ReferenceError(KnowledgeError):
    pass


class BusinessError(KnowledgeError):
    pass


class QualityWarning(KnowledgeError):
    pass
