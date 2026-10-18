# Rules reference

Rules are YAML and use JSON Pointer-style paths with shell wildcards.

```yaml
ignore_paths: [/metadata/generated_at]
unordered_paths: [/service/tags]
case_insensitive_paths: [/service/name]
numeric_tolerance:
  /metrics/error_rate: 0.01
keyed_arrays:
  /service/endpoints: id
severity_paths:
  /security/*: critical
sensitive_paths:
  - /credentials/*
```

Use `semanticdiff rules test rules.yaml` to validate and summarize a file, then `semanticdiff rules explain rules.yaml /security/tls` to inspect matching behavior.
