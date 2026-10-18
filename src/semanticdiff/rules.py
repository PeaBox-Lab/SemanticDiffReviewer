from __future__ import annotations
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any
import yaml

@dataclass(slots=True)
class Rules:
    ignore_paths: list[str] = field(default_factory=list)
    unordered_paths: list[str] = field(default_factory=list)
    case_insensitive_paths: list[str] = field(default_factory=list)
    numeric_tolerance: dict[str, float] = field(default_factory=dict)
    keyed_arrays: dict[str, str] = field(default_factory=dict)
    severity_paths: dict[str, str] = field(default_factory=dict)
    sensitive_paths: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Rules":
        data = data or {}
        return cls(
            ignore_paths=list(data.get("ignore_paths", [])),
            unordered_paths=list(data.get("unordered_paths", [])),
            case_insensitive_paths=list(data.get("case_insensitive_paths", [])),
            numeric_tolerance={str(k): float(v) for k, v in data.get("numeric_tolerance", {}).items()},
            keyed_arrays={str(k): str(v) for k, v in data.get("keyed_arrays", {}).items()},
            severity_paths={str(k): str(v) for k, v in data.get("severity_paths", {}).items()},
            sensitive_paths=list(data.get("sensitive_paths", [])),
        )

    @classmethod
    def load(cls, path: str | Path | None) -> "Rules":
        if not path:
            return cls()
        return cls.from_dict(yaml.safe_load(Path(path).read_text(encoding="utf-8")))

    @staticmethod
    def _matches(path: str, patterns: list[str]) -> bool:
        return any(fnmatch(path, pattern) for pattern in patterns)

    def ignored(self, path: str) -> bool:
        return self._matches(path, self.ignore_paths)

    def unordered(self, path: str) -> bool:
        return self._matches(path, self.unordered_paths)

    def case_insensitive(self, path: str) -> bool:
        return self._matches(path, self.case_insensitive_paths)

    def tolerance_for(self, path: str) -> float | None:
        for pattern, tolerance in self.numeric_tolerance.items():
            if fnmatch(path, pattern):
                return tolerance
        return None

    def array_key_for(self, path: str) -> str | None:
        for pattern, key in self.keyed_arrays.items():
            if fnmatch(path, pattern):
                return key
        return None
