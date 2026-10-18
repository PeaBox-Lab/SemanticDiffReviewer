# SemanticDiff

> Understand what changed. Know what matters.

SemanticDiff is a local-first semantic change intelligence and governance toolkit for JSON, YAML, configuration repositories, and OpenAPI contracts. It compares parsed structures rather than lines, validates both documents against JSON Schema, classifies operational risk, redacts likely secrets, enforces path-based policies, detects drift, and produces reports designed for developers and CI/CD.

## Why SemanticDiff

A text diff marks formatting, key order, and array movement as noise. SemanticDiff understands objects, scalar types, keyed collections, tolerances, ignored paths, and domain presets. The result is a review that focuses on behavioral impact.

## Capabilities

- JSON ↔ JSON, YAML ↔ YAML, and JSON ↔ YAML
- JSON Schema validation
- Policy guardrails and severity gates
- Git revision and working-tree comparison
- Recursive project/directory comparison
- OpenAPI breaking-change checks
- Baseline and configuration-drift detection
- Migration guide generation
- Secret redaction and sensitive-path rules
- JSON, CSV, JSON Patch, Markdown PR, HTML, and SARIF output
- CLI, Python API, responsive local web UI, Docker, and reusable GitHub Action
- Plugin discovery through `semanticdiff.plugins` entry points

## Quick start

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
semanticdiff examples/left.yaml examples/right.json --rules examples/rules.yaml
```

Launch the local UI:

```bash
semanticdiff-ui
```

Open `http://127.0.0.1:8765`.

## Common workflows

### Full governed comparison

```bash
semanticdiff compare old.yaml new.yaml \
  --rules rules.yaml \
  --schema schema.json \
  --policy policy.yaml \
  --fail-on-invalid \
  --fail-on-policy \
  --fail-level high \
  --format pr \
  --output semanticdiff-report.md
```

### Git-aware review

```bash
semanticdiff git config/app.yaml --base main --head WORKTREE --format pr
```

### Compare configuration trees

```bash
semanticdiff project ./approved ./candidate --format json -o project-report.json
```

### OpenAPI compatibility

```bash
semanticdiff openapi openapi-v1.yaml openapi-v2.yaml --fail-on-breaking --format pr
```

Checks currently include removed operations, required parameters, parameter type changes, removed responses, and removed security requirements.

### Drift detection

```bash
semanticdiff baseline create production.yaml production.baseline.yaml
semanticdiff baseline check production.baseline.yaml production.yaml --format pr
```

### Migration guide and SARIF

```bash
semanticdiff migrate old.yaml new.yaml -o MIGRATION.md
semanticdiff compare old.yaml new.yaml --format sarif -o semanticdiff.sarif
```

## Rules

```yaml
ignore_paths:
  - /metadata/generated_at
unordered_paths:
  - /service/tags
case_insensitive_paths:
  - /service/name
numeric_tolerance:
  /metrics/error_rate: 0.01
keyed_arrays:
  /service/endpoints: id
severity_paths:
  /security/*: critical
sensitive_paths:
  - /credentials/*
```

Diagnose rules:

```bash
semanticdiff rules test rules.yaml
semanticdiff rules explain rules.yaml /security/tls
```

See `docs/RULES.md` for the complete model.

## GitHub Action

```yaml
name: Configuration policy
on: [pull_request]
permissions:
  contents: read
jobs:
  semanticdiff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: OWNER/semanticdiff@v3
        with:
          left: config/approved.yaml
          right: config/app.yaml
          rules: config/rules.yaml
          schema: schemas/app.schema.json
          policy: policies/app-policy.yaml
          fail-level: high
```

Replace `OWNER` after publishing. The repository also includes CI, CodeQL, Docker, policy-gate, release, and package-publishing workflows.

## Docker

```bash
docker compose up --build
```

The supplied image runs as a non-root user. Compose applies a read-only root filesystem, temporary `/tmp`, a health check, and `no-new-privileges`.

## Python API

```python
from semanticdiff import Rules, compare
from semanticdiff.loader import load

result = compare(
    load("old.yaml"),
    load("new.yaml"),
    Rules.load("rules.yaml"),
)
print(result.to_dict())
```

## Exit codes

- `0`: command completed without an enabled gate failing
- `1`: semantic differences found with `--fail-on-diff`
- `2`: schema validation failed
- `3`: configured severity threshold reached
- `4`: policy guardrail failed
- `5`: OpenAPI breaking change detected

## Repository map

```text
src/semanticdiff/     Core engine, governance, workflows, UI and analyzers
examples/             Documents, schema, rules and policy
.github/workflows/    CI, security, release, Docker and policy examples
docs/                 Architecture and rules reference
tests/                Automated test suite
action.yml            Reusable composite GitHub Action
Dockerfile             Hardened container image
```

## Quality and security

The project includes pytest coverage gates, Ruff, mypy, package builds, CodeQL, Dependabot, pre-commit hooks, non-root Docker execution, safe YAML loading, HTML escaping, and secret redaction. Before exposing the web service beyond localhost, add authentication, TLS, request-size limits, and process-level resource limits through your chosen reverse proxy.

## Contributing

Read `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and `SUPPORT.md`. Bug and feature issue forms plus a pull-request template are included.

## License

MIT. See `LICENSE`.
