# Architecture

SemanticDiff separates parsing, structural comparison, interpretation, validation, governance, and presentation.

1. `loader.py` safely parses JSON/YAML.
2. `engine.py` recursively compares typed structures.
3. `rules.py` alters equality semantics by path.
4. `insights.py` classifies severity and redacts sensitive data.
5. `schema.py` validates both sides against JSON Schema.
6. `policy.py` enforces protected paths and change budgets.
7. `openapi.py` detects API compatibility risks.
8. `workflows.py` adds Git, project, baseline, migration, PR, and SARIF workflows.
9. `plugins.py` discovers optional analyzers through Python entry points.
10. CLI, web UI, Docker, and GitHub Actions are delivery surfaces around the same core.
