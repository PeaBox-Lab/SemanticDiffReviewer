from semanticdiff import compare, Rules, DiffResult
from semanticdiff.insights import enrich

# Test 1: type_changed detection
print("=== Test 1: type_changed ===")
r = compare({"a": "hello"}, {"a": 42})
print(f"equal={r.equal}, diffs={[(d.kind, d.path) for d in r.differences]}")

# Test 2: tolerance
print("\n=== Test 2: tolerance ===")
rules = Rules.from_dict({"numeric_tolerance": {"/price": 0.5}})
r = compare({"price": 10.0}, {"price": 10.6}, rules)
print(f"equal={r.equal}, summary={r.summary}")

# Test 3: case insensitive
print("\n=== Test 3: case_insensitive ===")
rules = Rules.from_dict({"case_insensitive_paths": ["/name"]})
r = compare({"name": "ABC"}, {"name": "abc"}, rules)
print(f"equal={r.equal}")

# Test 4: unordered arrays
print("\n=== Test 4: unordered arrays ===")
rules = Rules.from_dict({"unordered_paths": ["/tags"]})
r = compare({"tags": ["a", "b"]}, {"tags": ["b", "a"]}, rules)
print(f"equal={r.equal}, diffs={[(d.kind, d.path) for d in r.differences]}")

# Test 5: keyed arrays
print("\n=== Test 5: keyed arrays ===")
rules = Rules.from_dict({"keyed_arrays": {"/items": "id"}})
r = compare({"items": [{"id": "a", "v": 1}]}, {"items": [{"id": "b", "v": 2}]}, rules)
print(f"equal={r.equal}, diffs={[(d.kind, d.path, d.message) for d in r.differences]}")

# Test 6: JSON schema validation
print("\n=== Test 6: JSON schema ===")
from semanticdiff.schema import validate_pair
schema = {"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}}}
r = validate_pair({"name": "API"}, {"name": 42}, schema)
print(f"valid={r['valid']}, left_valid={r['left_valid']}, right_valid={r['right_valid']}")

# Test 7: enrich with redaction
print("\n=== Test 7: enrich with redaction ===")
payload = enrich({"differences": [{"path": "/auth/api_key", "kind": "changed", "left": "secret123", "right": "secret456"}]})
print(f"risk={payload['risk']}, left={payload['differences'][0]['left']}, right={payload['differences'][0]['right']}")

# Test 8: policy guardrail
print("\n=== Test 8: policy ===")
from semanticdiff.policy import Policy, evaluate_policy
result = compare({"service": {"name": "a"}}, {"service": {"name": "b"}})
check = evaluate_policy(result, Policy.from_dict({"deny_changes": ["/service/name"]}))
print(f"passed={check['passed']}, violations={check['violations']}")

# Test 9: OpenAPI analysis
print("\n=== Test 9: OpenAPI ===")
from semanticdiff.openapi import analyze_openapi
old = {"openapi": "3.0.0", "paths": {"/users": {"get": {"responses": {"200": {"description": "ok"}}}}}}
new = {"openapi": "3.0.0", "paths": {}}
out = analyze_openapi(old, new)
print(f"compatible={out['compatible']}, findings={[f['kind'] for f in out['findings']]}")

# Test 10: baseline
print("\n=== Test 10: baseline ===")
from semanticdiff.workflows import baseline_create, baseline_check
import tempfile, os
tmp = tempfile.mkdtemp()
f = os.path.join(tmp, "a.yaml"); base = os.path.join(tmp, "base.yaml")
with open(f, "w") as fh: fh.write("a: 1")
baseline_create(f, base)
with open(f, "w") as fh: fh.write("a: 2")
result = baseline_check(base, f)
print(f"equal={result['equal']}, risk={result.get('risk')}")

print("\n=== All basic tests done ===")