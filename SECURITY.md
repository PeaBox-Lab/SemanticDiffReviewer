# Security Policy

## Reporting
Please report suspected vulnerabilities privately through the repository's security reporting channel rather than a public issue.

## Security posture
SemanticDiff parses untrusted JSON/YAML with safe YAML loading, escapes generated HTML content, binds the development UI locally by default, and the supplied container runs as a non-root user. Treat schemas, rules, policies, and compared documents as untrusted input and apply normal resource limits when exposing the service beyond a trusted workstation.
