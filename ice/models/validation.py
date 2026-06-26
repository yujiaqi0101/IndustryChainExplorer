from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IssueSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    severity: IssueSeverity
    message: str
    source_type: str = ""
    source_id: str = ""
    field_name: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        loc = self.source_id
        if self.field_name:
            loc = f"{loc}.{self.field_name}"
        prefix = f"[{self.severity.value.upper()}]"
        if loc:
            return f"{prefix} {self.source_type} {loc}: {self.message}"
        return f"{prefix} {self.message}"


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    def add_error(self, message: str, **kwargs: Any) -> None:
        self.issues.append(ValidationIssue(severity=IssueSeverity.ERROR, message=message, **kwargs))

    def add_warning(self, message: str, **kwargs: Any) -> None:
        self.issues.append(ValidationIssue(severity=IssueSeverity.WARNING, message=message, **kwargs))

    def add_info(self, message: str, **kwargs: Any) -> None:
        self.issues.append(ValidationIssue(severity=IssueSeverity.INFO, message=message, **kwargs))

    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.ERROR]

    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.WARNING]

    def infos(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.INFO]

    def has_errors(self) -> bool:
        return len(self.errors()) > 0

    def error_count(self) -> int:
        return len(self.errors())

    def warning_count(self) -> int:
        return len(self.warnings())

    def info_count(self) -> int:
        return len(self.infos())

    def quality_score(self) -> int:
        score = 100
        score -= self.error_count() * 10
        score -= self.warning_count() * 2
        score -= self.info_count() * 0.5
        return max(0, min(100, int(score)))

    def merge(self, other: ValidationReport) -> None:
        self.issues.extend(other.issues)

    def format(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("Knowledge Validation Report")
        lines.append("=" * 60)
        lines.append(f"Errors:   {self.error_count()}")
        lines.append(f"Warnings: {self.warning_count()}")
        lines.append(f"Infos:    {self.info_count()}")
        lines.append(f"Quality Score: {self.quality_score()}/100")
        lines.append("-" * 60)
        for issue in self.issues:
            lines.append(str(issue))
        lines.append("=" * 60)
        return "\n".join(lines)
