from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
from jsonschema import validators
from jsonschema.exceptions import SchemaError

@dataclass(slots=True)
class SchemaIssue:
    document: str
    path: str
    schema_path: str
    validator: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def _pointer(parts: list[Any]) -> str:
    if not parts:
        return "/"
    return "/" + "/".join(str(p).replace("~", "~0").replace("/", "~1") for p in parts)

def validate_document(instance: Any, schema: Any, document: str = "document") -> list[SchemaIssue]:
    validator_cls = validators.validator_for(schema)
    try:
        validator_cls.check_schema(schema)
    except SchemaError as exc:
        raise ValueError(f"Invalid JSON Schema: {exc.message}") from exc
    validator = validator_cls(schema)
    issues = []
    for error in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path)):
        issues.append(SchemaIssue(
            document=document,
            path=_pointer(list(error.absolute_path)),
            schema_path=_pointer(list(error.absolute_schema_path)),
            validator=str(error.validator),
            message=error.message,
        ))
    return issues

def validate_pair(left: Any, right: Any, schema: Any) -> dict[str, Any]:
    left_issues = validate_document(left, schema, "left")
    right_issues = validate_document(right, schema, "right")
    return {
        "valid": not left_issues and not right_issues,
        "left_valid": not left_issues,
        "right_valid": not right_issues,
        "issues": [x.to_dict() for x in left_issues + right_issues],
    }
