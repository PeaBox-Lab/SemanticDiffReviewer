from __future__ import annotations
from dataclasses import dataclass, field, asdict
from fnmatch import fnmatch
from typing import Any

@dataclass(slots=True)
class Policy:
    deny_changes: list[str] = field(default_factory=list)
    deny_removals: list[str] = field(default_factory=list)
    deny_additions: list[str] = field(default_factory=list)
    max_changes: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Policy":
        data = data or {}
        return cls(list(data.get("deny_changes", [])), list(data.get("deny_removals", [])), list(data.get("deny_additions", [])), data.get("max_changes"))

@dataclass(slots=True)
class PolicyViolation:
    path: str
    kind: str
    rule: str
    message: str
    def to_dict(self): return asdict(self)

def evaluate_policy(result, policy: Policy) -> dict[str, Any]:
    violations: list[PolicyViolation] = []
    for d in result.differences:
        checks = [(policy.deny_changes, "deny_changes", {"changed", "type_changed"}), (policy.deny_removals, "deny_removals", {"removed"}), (policy.deny_additions, "deny_additions", {"added"})]
        for patterns, rule, kinds in checks:
            if d.kind in kinds:
                for pattern in patterns:
                    if fnmatch(d.path, pattern):
                        violations.append(PolicyViolation(d.path, d.kind, rule, f"{d.kind} is prohibited by {pattern}")); break
    if policy.max_changes is not None and len(result.differences) > int(policy.max_changes):
        violations.append(PolicyViolation("/", "limit", "max_changes", f"{len(result.differences)} differences exceed limit {policy.max_changes}"))
    return {"passed": not violations, "violations": [v.to_dict() for v in violations]}
