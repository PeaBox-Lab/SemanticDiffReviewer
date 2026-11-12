from semanticdiff.rules import Rules

rules = Rules.from_dict({"ignore_paths": ["/*"]})

# Check what paths look like after escaping
from semanticdiff.engine import _child

# Test path generation with tilde and slash in keys
p1 = _child("", "key~")
print(f"child with tilde key: '{p1}'")

p2 = _child("", "key/")
print(f"child with slash key: '{p2}'")

# Check fnmatch matching
from fnmatch import fnmatch
print(f"fnmatch '/*' vs '{p1}': {fnmatch(p1, '/*')}")
print(f"fnmatch '/*' vs '{p2}': {fnmatch(p2, '/*')}")
print(f"fnmatch '/key~' vs '{p1}': {fnmatch('/key~', '/*')}")

# Now test with actual compare
from semanticdiff import compare
r = compare({"~": 1}, {"~": 1}, rules)
print(f"compare with tilde key and ignore_paths ['/*']: equal={r.equal}, ignored={r.ignored}")

# What if we have path with slash token in key?
r2 = compare({"/": 1}, {"/": 1}, rules)
print(f"compare with slash key and ignore_paths ['/*']: equal={r2.equal}, ignored={r2.ignored}")

# Check what happens with deeply nested
r3 = compare({"a": {"~": 1}}, {"a": {"~": 1}}, rules)
print(f"compare nested tilde key and ignore_paths ['/*']: equal={r3.equal}, ignored={r3.ignored}, diffs={[d.path for d in r3.differences]}")

# What about ignore_paths pattern not matching?
rules2 = Rules.from_dict({"ignore_paths": ["/ignored/*"]})
r4 = compare({"ignored": {"x": 1}}, {"ignored": {"x": 1}}, rules2)
print(f"compare with ignore ['/ignored/*']: equal={r4.equal}, ignored={r4.ignored}, diffs={[d.path for d in r4.differences]}")