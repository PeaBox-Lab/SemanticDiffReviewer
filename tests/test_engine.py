from semanticdiff import compare, Rules

def test_object_order_and_format_do_not_matter():
    assert compare({"a": 1, "b": 2}, {"b": 2, "a": 1}).equal

def test_rules():
    rules = Rules.from_dict({"ignore_paths":["/meta/*"], "case_insensitive_paths":["/name"], "unordered_paths":["/tags"], "numeric_tolerance":{"/score":0.1}})
    left = {"name":"API", "tags":["a","b"], "score":1.0, "meta":{"time":1}}
    right = {"name":"api", "tags":["b","a"], "score":1.05, "meta":{"time":2}}
    assert compare(left, right, rules).equal

def test_keyed_arrays():
    rules = Rules.from_dict({"keyed_arrays":{"/items":"id"}})
    result = compare({"items":[{"id":"a","v":1},{"id":"b","v":2}]}, {"items":[{"id":"b","v":3},{"id":"a","v":1}]}, rules)
    assert not result.equal
    assert result.differences[0].path == "/items/id=b/v"


def test_json_schema_validation():
    from semanticdiff.schema import validate_pair
    schema = {"type":"object", "required":["name"], "properties":{"name":{"type":"string"}}}
    result = validate_pair({"name":"API"}, {"name":42}, schema)
    assert not result["valid"]
    assert result["left_valid"]
    assert not result["right_valid"]
    assert result["issues"][0]["path"] == "/name"

def test_impact_and_secret_redaction():
    from semanticdiff.insights import enrich
    payload = enrich({"differences":[{"path":"/auth/api_key","kind":"changed","left":"a","right":"b"}]})
    assert payload["risk"] == "high"
    assert payload["differences"][0]["left"] == "***REDACTED***"

def test_kubernetes_preset_ignores_runtime_metadata():
    from semanticdiff.presets import get_preset
    result = compare({"metadata":{"uid":"1"},"spec":{"replicas":1}}, {"metadata":{"uid":"2"},"spec":{"replicas":1}}, get_preset("kubernetes"))
    assert result.equal


def test_policy_guardrail():
    from semanticdiff.policy import Policy, evaluate_policy
    result = compare({"service":{"name":"a"}}, {"service":{"name":"b"}})
    check = evaluate_policy(result, Policy.from_dict({"deny_changes":["/service/name"]}))
    assert not check["passed"]
    assert check["violations"][0]["rule"] == "deny_changes"

def test_sarif_and_migration():
    from semanticdiff.insights import enrich
    from semanticdiff.workflows import sarif, migration_markdown
    result=enrich(compare({'a':1},{'a':2}).to_dict(),{},[],True)
    assert sarif(result)['runs'][0]['results'][0]['ruleId']=='semanticdiff.changed'
    assert 'Migration Guide' in migration_markdown(result)

def test_project_mode(tmp_path):
    from semanticdiff.workflows import compare_project
    a,b=tmp_path/'a',tmp_path/'b'; a.mkdir(); b.mkdir()
    (a/'x.yaml').write_text('value: 1'); (b/'x.yaml').write_text('value: 2')
    out=compare_project(str(a),str(b))
    assert out['summary']['modified']==1

def test_baseline(tmp_path):
    from semanticdiff.workflows import baseline_create,baseline_check
    f=tmp_path/'a.yaml'; base=tmp_path/'base.yaml'; f.write_text('a: 1')
    baseline_create(str(f),str(base)); f.write_text('a: 2')
    assert not baseline_check(str(base),str(f))['equal']

def test_openapi_breaking_changes():
    from semanticdiff.openapi import analyze_openapi
    old={'openapi':'3.0.0','paths':{'/users':{'get':{'responses':{'200':{'description':'ok'}}}}}}
    new={'openapi':'3.0.0','paths':{}}
    out=analyze_openapi(old,new)
    assert not out['compatible']
    assert out['findings'][0]['kind']=='operation_removed'

def test_openapi_required_parameter():
    from semanticdiff.openapi import analyze_openapi
    old={'paths':{'/users':{'get':{'parameters':[],'responses':{}}}}}
    new={'paths':{'/users':{'get':{'parameters':[{'in':'query','name':'tenant','required':True,'schema':{'type':'string'}}],'responses':{}}}}}
    assert analyze_openapi(old,new)['breaking_changes']==1
