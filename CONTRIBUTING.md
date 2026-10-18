# Contributing to SemanticDiff

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
pytest
```

## Pull requests
Keep changes focused, add tests for behavior, document CLI changes, and preserve backward compatibility unless the release is explicitly major. Run `ruff check src tests`, `mypy src/semanticdiff --ignore-missing-imports`, and `pytest` before opening the PR.

## Plugins
Publish an entry point in the `semanticdiff.plugins` group. Plugins implement `name`, `supports(left, right)`, and `analyze(left, right)`. Plugin failures are isolated so the core comparison remains available.

## Security
Never open a public issue containing production configuration, credentials, tokens, private endpoints, or employee/customer data. Follow `SECURITY.md` for private reporting.
