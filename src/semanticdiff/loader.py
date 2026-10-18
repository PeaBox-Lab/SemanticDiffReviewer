from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import yaml

class DocumentError(ValueError):
    pass

def loads(text: str, fmt: str = "auto") -> Any:
    fmt = fmt.lower()
    if fmt not in {"auto", "json", "yaml", "yml"}:
        raise DocumentError(f"Unsupported format: {fmt}")
    if fmt in {"json", "auto"}:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if fmt == "json":
                raise DocumentError("Invalid JSON")
    try:
        value = yaml.safe_load(text)
        if value is None and text.strip():
            raise DocumentError("Document resolved to null")
        return value
    except yaml.YAMLError as exc:
        raise DocumentError(f"Invalid YAML: {exc}") from exc

def load(path: str | Path, fmt: str = "auto") -> Any:
    p = Path(path)
    inferred = fmt
    if fmt == "auto" and p.suffix.lower() in {".json"}:
        inferred = "json"
    elif fmt == "auto" and p.suffix.lower() in {".yaml", ".yml"}:
        inferred = "yaml"
    return loads(p.read_text(encoding="utf-8"), inferred)
