from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
from typing import Any
import yaml
from .loader import load, loads
from .engine import compare
from .rules import Rules
from .insights import enrich

SUPPORTED={'.json','.yaml','.yml'}

def payload(left:Any,right:Any,rules:Rules|None=None)->dict[str,Any]:
    rules=rules or Rules(); return enrich(compare(left,right,rules).to_dict(),rules.severity_paths,rules.sensitive_paths,True)

def git_document(path:str, revision:str)->Any:
    proc=subprocess.run(['git','show',f'{revision}:{path}'],text=True,capture_output=True)
    if proc.returncode: raise ValueError(proc.stderr.strip() or f'Unable to read {path} at {revision}')
    return loads(proc.stdout, 'json' if path.endswith('.json') else 'yaml')

def compare_git(path:str,base:str,head:str='WORKTREE',rules:Rules|None=None)->dict[str,Any]:
    left=git_document(path,base); right=load(path) if head=='WORKTREE' else git_document(path,head)
    out=payload(left,right,rules); out['source']={'mode':'git','path':path,'base':base,'head':head}; return out

def compare_project(left_dir:str,right_dir:str,rules:Rules|None=None)->dict[str,Any]:
    a,b=Path(left_dir),Path(right_dir)
    files=sorted({p.relative_to(a) for p in a.rglob('*') if p.suffix.lower() in SUPPORTED}|{p.relative_to(b) for p in b.rglob('*') if p.suffix.lower() in SUPPORTED})
    reports=[]
    for rel in files:
        lp,rp=a/rel,b/rel
        if not lp.exists(): reports.append({'file':str(rel),'status':'added','risk':'medium','differences':[]}); continue
        if not rp.exists(): reports.append({'file':str(rel),'status':'removed','risk':'high','differences':[]}); continue
        try:
            report=payload(load(lp),load(rp),rules); report.update(file=str(rel),status='unchanged' if report['equal'] else 'modified'); reports.append(report)
        except Exception as exc: reports.append({'file':str(rel),'status':'error','risk':'high','error':str(exc),'differences':[]})
    counts={k:sum(x['status']==k for x in reports) for k in ('unchanged','modified','added','removed','error')}
    risk_order={'none':0,'low':1,'medium':2,'high':3,'critical':4}
    overall=max((x.get('risk','none') for x in reports),key=lambda x:risk_order.get(x,0),default='none')
    return {'mode':'project','left':str(a),'right':str(b),'summary':counts,'risk':overall,'files':reports}

def migration_markdown(data:dict[str,Any])->str:
    lines=['# SemanticDiff Migration Guide','',f"**Overall risk:** {data.get('risk','none').upper()}",'']
    if not data.get('differences'): return '\n'.join(lines+['No migration actions are required.',''])
    for i,d in enumerate(data['differences'],1):
        action={'added':'Confirm consumers tolerate the new field.','removed':'Remove or replace references to this field.','type_changed':'Update parsers, validators, and dependent code for the new type.','changed':'Review dependent behavior and update expected values.'}.get(d['kind'],'Review this change.')
        lines += [f"## {i}. `{d['path']}`",'',f"- **Severity:** {d.get('severity','medium')}",f"- **Change:** {d['kind']}",f"- **Why:** {d.get('explanation','Structured value changed.')}",f"- **Action:** {action}",'',f"Old: `{json.dumps(d.get('left'),ensure_ascii=False,default=str)}`",f"New: `{json.dumps(d.get('right'),ensure_ascii=False,default=str)}`",'']
    return '\n'.join(lines)

def sarif(data:dict[str,Any])->dict[str,Any]:
    results=[]
    level={'critical':'error','high':'error','medium':'warning','low':'note','info':'note'}
    for d in data.get('differences',[]):
        sev=d.get('severity','medium'); results.append({'ruleId':f"semanticdiff.{d['kind']}",'level':level.get(sev,'warning'),'message':{'text':f"{d.get('explanation','Change detected')} at {d['path']}"},'locations':[{'physicalLocation':{'artifactLocation':{'uri':'structured-document'},'region':{'startLine':1}}}],'properties':{'path':d['path'],'severity':sev,'left':d.get('left'),'right':d.get('right')}})
    return {'version':'2.1.0','$schema':'https://json.schemastore.org/sarif-2.1.0.json','runs':[{'tool':{'driver':{'name':'SemanticDiff','version':'2.1.0','informationUri':'https://github.com/'}},'results':results}]}

def baseline_create(document:str,output:str)->dict[str,Any]:
    raw=Path(document).read_bytes(); record={'version':1,'source':document,'sha256':hashlib.sha256(raw).hexdigest(),'document':load(document)}; Path(output).write_text(yaml.safe_dump(record,sort_keys=False),encoding='utf-8'); return record

def baseline_check(baseline:str,current:str,rules:Rules|None=None)->dict[str,Any]:
    saved=yaml.safe_load(Path(baseline).read_text(encoding='utf-8')); out=payload(saved['document'],load(current),rules); out['baseline']={'file':baseline,'source':saved.get('source'),'sha256':saved.get('sha256')}; return out
