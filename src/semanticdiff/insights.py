from __future__ import annotations
from typing import Any
from fnmatch import fnmatch
import re

SECRET_PATTERN = re.compile(r"(secret|password|passwd|token|api[-_]?key|private[-_]?key|connection[-_]?string|credential)", re.I)
LEVELS = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

def is_sensitive(path: str, extra: list[str] | None = None) -> bool:
    return bool(SECRET_PATTERN.search(path)) or any(fnmatch(path, p) for p in (extra or []))

def severity_for(path: str, kind: str, custom: dict[str, str] | None = None) -> str:
    for pattern, level in (custom or {}).items():
        if fnmatch(path, pattern):
            return level
    lower = path.lower()
    if any(x in lower for x in ("/security", "/auth", "/permissions", "/roles", "/network", "/firewall")):
        return "critical" if kind in {"removed", "type_changed"} else "high"
    if any(x in lower for x in ("/version", "/image", "/endpoint", "/url", "/host", "/port", "/replicas")):
        return "high" if kind in {"removed", "type_changed"} else "medium"
    return "medium" if kind in {"removed", "type_changed"} else "low"

def explain(path: str, kind: str, left: Any, right: Any) -> str:
    name = path.rsplit("/", 1)[-1].replace("~1", "/").replace("~0", "~") or "root"
    if kind == "added": return f"{name} was added. Consumers that reject unknown fields may need review."
    if kind == "removed": return f"{name} was removed. Existing consumers may rely on it."
    if kind == "type_changed": return f"{name} changed data type, which can break parsers and integrations."
    return f"{name} changed from {left!r} to {right!r}."

def enrich(payload: dict[str, Any], severity_paths: dict[str, str] | None = None,
           sensitive_paths: list[str] | None = None, redact: bool = True) -> dict[str, Any]:
    counts = {k: 0 for k in LEVELS}
    for item in payload.get("differences", []):
        item["severity"] = severity_for(item["path"], item["kind"], severity_paths)
        item["explanation"] = explain(item["path"], item["kind"], item.get("left"), item.get("right"))
        item["sensitive"] = is_sensitive(item["path"], sensitive_paths)
        counts[item["severity"]] += 1
        if redact and item["sensitive"]:
            item["left"] = item["right"] = "***REDACTED***"
    payload["impact"] = counts
    payload["risk"] = max((x["severity"] for x in payload.get("differences", [])), key=LEVELS.get, default="info")
    return payload
