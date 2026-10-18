"""SemanticDiff public API."""
from .engine import compare, DiffResult, DiffEntry
from .rules import Rules

__all__ = ["compare", "DiffResult", "DiffEntry", "Rules"]
__version__ = "3.0.0"
