from __future__ import annotations
from .rules import Rules

PRESETS = {
    "strict": {},
    "api": {
        "ignore_paths": ["/info/version", "/servers/*/description"],
        "unordered_paths": ["/tags", "/required"],
        "keyed_arrays": {"/servers": "url", "/tags": "name"},
    },
    "kubernetes": {
        "ignore_paths": ["/metadata/creationTimestamp", "/metadata/resourceVersion", "/metadata/uid", "/metadata/managedFields", "/status"],
        "keyed_arrays": {"/spec/template/spec/containers": "name", "/spec/template/spec/initContainers": "name", "/spec/template/spec/containers/*/env": "name"},
    },
    "package": {
        "ignore_paths": ["/lockfileVersion"],
        "unordered_paths": ["/keywords"],
    },
    "human-friendly": {
        "ignore_paths": ["*/updated_at", "*/updatedAt", "*/timestamp", "*/generated_at"],
        "case_insensitive_paths": ["*/name", "*/title"],
    },
}

def get_preset(name: str | None) -> Rules:
    if not name: return Rules()
    if name not in PRESETS: raise ValueError(f"Unknown preset: {name}. Choose: {', '.join(PRESETS)}")
    return Rules.from_dict(PRESETS[name])

def merge(base: Rules, override: Rules) -> Rules:
    return Rules(
        ignore_paths=base.ignore_paths + override.ignore_paths,
        unordered_paths=base.unordered_paths + override.unordered_paths,
        case_insensitive_paths=base.case_insensitive_paths + override.case_insensitive_paths,
        numeric_tolerance={**base.numeric_tolerance, **override.numeric_tolerance},
        keyed_arrays={**base.keyed_arrays, **override.keyed_arrays},
        severity_paths={**base.severity_paths, **override.severity_paths},
        sensitive_paths=base.sensitive_paths + override.sensitive_paths,
    )
