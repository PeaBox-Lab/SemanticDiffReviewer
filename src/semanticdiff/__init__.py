"""SemanticDiff public API."""
from .engine import DiffEntry, DiffResult, compare
from .rules import Rules

__all__ = ["DiffEntry", "DiffResult", "Rules", "compare"]
__version__ = "3.0.0"
