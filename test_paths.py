from semanticdiff.engine import compare
from semanticdiff.rules import Rules

# Test path escaping with special characters
rules = Rules.from_dict({"ignore_paths": ["/*"]})
left = {"~": 1, "/": 2, "foo": {"~": 3}}
right = {"~": 1, "/": 2, "foo": {"~": 3}}
result = compare(left, right, rules)
print("Result with ignore_paths ['/*']:", result.equal)
print("Ignored count:", result.ignored)
print("Differences:", result.differences)

# More tests
rules2 = Rules.from_dict({"ignore_paths": ["/foo/*"]})
result2 = compare({"foo": {"~": 1}}, {"foo": {"~": 1}}, rules2)
print("Result with ignore_paths ['/foo/*']:", result2.equal)
print("Ignored count:", result2.ignored)