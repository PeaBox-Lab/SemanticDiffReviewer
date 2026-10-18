from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import json
from .rules import Rules

MISSING = object()

@dataclass(slots=True)
class DiffEntry:
    path: str
    kind: str
    left: Any = None
    right: Any = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(slots=True)
class DiffResult:
    equal: bool
    differences: list[DiffEntry]
    ignored: int = 0

    @property
    def summary(self) -> dict[str, int]:
        out = {"added": 0, "removed": 0, "changed": 0, "type_changed": 0, "ignored": self.ignored}
        for item in self.differences:
            out[item.kind] = out.get(item.kind, 0) + 1
        return out

    def to_dict(self) -> dict[str, Any]:
        return {"equal": self.equal, "summary": self.summary, "differences": [d.to_dict() for d in self.differences]}

def _child(path: str, token: str | int) -> str:
    escaped = str(token).replace("~", "~0").replace("/", "~1")
    return f"{path}/{escaped}" if path else f"/{escaped}"

def _stable(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

def _scalar_equal(left: Any, right: Any, path: str, rules: Rules) -> bool:
    if isinstance(left, (int, float)) and not isinstance(left, bool) and isinstance(right, (int, float)) and not isinstance(right, bool):
        tol = rules.tolerance_for(path)
        return abs(float(left) - float(right)) <= tol if tol is not None else left == right
    if isinstance(left, str) and isinstance(right, str) and rules.case_insensitive(path):
        return left.casefold() == right.casefold()
    return left == right

def compare(left: Any, right: Any, rules: Rules | None = None) -> DiffResult:
    rules = rules or Rules()
    diffs: list[DiffEntry] = []
    ignored = 0

    def walk(a: Any, b: Any, path: str) -> None:
        nonlocal ignored
        if rules.ignored(path):
            ignored += 1
            return
        if type(a) is not type(b) and not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
            diffs.append(DiffEntry(path or "/", "type_changed", a, b, f"{type(a).__name__} -> {type(b).__name__}"))
            return
        if isinstance(a, dict) and isinstance(b, dict):
            for key in sorted(a.keys() - b.keys(), key=str):
                p = _child(path, key)
                if rules.ignored(p): ignored += 1
                else: diffs.append(DiffEntry(p, "removed", a[key], None, "Key removed"))
            for key in sorted(b.keys() - a.keys(), key=str):
                p = _child(path, key)
                if rules.ignored(p): ignored += 1
                else: diffs.append(DiffEntry(p, "added", None, b[key], "Key added"))
            for key in sorted(a.keys() & b.keys(), key=str):
                walk(a[key], b[key], _child(path, key))
            return
        if isinstance(a, list) and isinstance(b, list):
            key = rules.array_key_for(path)
            if key:
                amap = {str(x.get(key)): x for x in a if isinstance(x, dict) and key in x}
                bmap = {str(x.get(key)): x for x in b if isinstance(x, dict) and key in x}
                if len(amap) != len(a) or len(bmap) != len(b):
                    diffs.append(DiffEntry(path or "/", "changed", a, b, f"Keyed array requires unique object key '{key}'"))
                    return
                for item_key in sorted(amap.keys() | bmap.keys()):
                    p = _child(path, f"{key}={item_key}")
                    if item_key not in bmap: diffs.append(DiffEntry(p, "removed", amap[item_key], None, "Array item removed"))
                    elif item_key not in amap: diffs.append(DiffEntry(p, "added", None, bmap[item_key], "Array item added"))
                    else: walk(amap[item_key], bmap[item_key], p)
                return
            if rules.unordered(path):
                if sorted(map(_stable, a)) != sorted(map(_stable, b)):
                    diffs.append(DiffEntry(path or "/", "changed", a, b, "Unordered array contents differ"))
                return
            common = min(len(a), len(b))
            for i in range(common): walk(a[i], b[i], _child(path, i))
            for i in range(common, len(a)): diffs.append(DiffEntry(_child(path, i), "removed", a[i], None, "Array item removed"))
            for i in range(common, len(b)): diffs.append(DiffEntry(_child(path, i), "added", None, b[i], "Array item added"))
            return
        if not _scalar_equal(a, b, path, rules):
            diffs.append(DiffEntry(path or "/", "changed", a, b, "Value changed"))

    walk(left, right, "")
    return DiffResult(not diffs, diffs, ignored)
