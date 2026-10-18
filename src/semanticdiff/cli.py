from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from .loader import load,loads
from .rules import Rules
from .engine import compare
from .schema import validate_pair
from .policy import Policy,evaluate_policy
from .insights import enrich,LEVELS
from .presets import PRESETS,get_preset,merge
from .exporters import render_csv_payload,render_json_patch,render_sarif_payload,render_pr_markdown
from .workflows import compare_git,compare_project,migration_markdown,baseline_create,baseline_check
from .openapi import analyze_openapi
from .plugins import run_plugins

def _rules(a): return merge(get_preset(getattr(a,'preset',None)),Rules.load(getattr(a,'rules',None)))
def _write(content,output=None): Path(output).write_text(content,encoding='utf-8') if output else print(content,end='' if content.endswith('\n') else '\n')
def _render(payload,fmt):
    if fmt=='json': return json.dumps(payload,indent=2,ensure_ascii=False,default=str)
    if fmt=='csv': return render_csv_payload(payload)
    if fmt=='patch': return render_json_patch(payload)
    if fmt=='sarif': return render_sarif_payload(payload)
    if fmt in {'markdown','pr'}: return render_pr_markdown(payload)
    return 'Equivalent\n' if payload.get('equal') else '\n'.join(f"[{d.get('severity','medium').upper():8}] {d['kind']:12} {d['path']} - {d.get('explanation','')}" for d in payload.get('differences',[]))+'\n'
def _common(p):
    p.add_argument('--rules'); p.add_argument('--preset',choices=sorted(PRESETS)); p.add_argument('--format',choices=['text','json','markdown','pr','csv','patch','sarif'],default='text'); p.add_argument('-o','--output')
def parser():
    p=argparse.ArgumentParser(prog='semanticdiff',description='Semantic change intelligence for JSON and YAML'); sub=p.add_subparsers(dest='command')
    c=sub.add_parser('compare'); c.add_argument('left'); c.add_argument('right'); _common(c); c.add_argument('--schema'); c.add_argument('--policy'); c.add_argument('--fail-on-diff',action='store_true'); c.add_argument('--fail-on-invalid',action='store_true'); c.add_argument('--fail-on-policy',action='store_true'); c.add_argument('--fail-level',choices=list(LEVELS)); c.add_argument('--show-secrets',action='store_true')
    g=sub.add_parser('git'); g.add_argument('path'); g.add_argument('--base',default='HEAD'); g.add_argument('--head',default='WORKTREE'); _common(g)
    d=sub.add_parser('project'); d.add_argument('left'); d.add_argument('right'); _common(d)
    m=sub.add_parser('migrate'); m.add_argument('left'); m.add_argument('right'); m.add_argument('--rules'); m.add_argument('-o','--output')
    r=sub.add_parser('rules'); r.add_argument('action',choices=['test','explain']); r.add_argument('rules_file'); r.add_argument('path',nargs='?')
    o=sub.add_parser('openapi'); o.add_argument('left'); o.add_argument('right'); o.add_argument('--format',choices=['text','json','pr'],default='text'); o.add_argument('-o','--output'); o.add_argument('--fail-on-breaking',action='store_true')
    b=sub.add_parser('baseline'); b.add_argument('action',choices=['create','check']); b.add_argument('document'); b.add_argument('target'); b.add_argument('--rules'); b.add_argument('--format',choices=['text','json','markdown','pr','sarif'],default='text'); b.add_argument('-o','--output')
    return p

def main():
    argv=sys.argv[1:]
    if argv and argv[0] not in {'compare','git','project','migrate','rules','openapi','baseline','-h','--help'}: argv=['compare']+argv
    a=parser().parse_args(argv)
    if not a.command: parser().print_help(); return
    if a.command=='compare':
        left=loads(sys.stdin.read()) if a.left=='-' else load(a.left); right=load(a.right); rules=_rules(a); result=compare(left,right,rules); out=enrich(result.to_dict(),rules.severity_paths,rules.sensitive_paths,not a.show_secrets)
        if a.schema: out['validation']=validate_pair(left,right,load(a.schema))
        plugin_results=run_plugins(left,right)
        if plugin_results: out['plugins']=plugin_results
        if a.policy: out['policy']=evaluate_policy(result,Policy.from_dict(load(a.policy)))
        _write(_render(out,a.format),a.output)
        if a.fail_on_invalid and not out.get('validation',{}).get('valid',True): raise SystemExit(2)
        if a.fail_level and any(LEVELS[x['severity']]>=LEVELS[a.fail_level] for x in out['differences']): raise SystemExit(3)
        if a.fail_on_policy and not out.get('policy',{}).get('passed',True): raise SystemExit(4)
        if a.fail_on_diff and not result.equal: raise SystemExit(1)
    elif a.command=='git': out=compare_git(a.path,a.base,a.head,_rules(a)); _write(_render(out,a.format),a.output)
    elif a.command=='project': out=compare_project(a.left,a.right,_rules(a)); _write(json.dumps(out,indent=2,ensure_ascii=False) if a.format=='json' else '\n'.join(f"{x['status']:9} {x['file']} ({x.get('risk','none')})" for x in out['files'])+'\n',a.output)
    elif a.command=='migrate':
        rules=Rules.load(a.rules); out=enrich(compare(load(a.left),load(a.right),rules).to_dict(),rules.severity_paths,rules.sensitive_paths,True); _write(migration_markdown(out),a.output)
    elif a.command=='rules':
        rules=Rules.load(a.rules_file)
        if a.action=='test': _write(json.dumps({'valid':True,'counts':{'ignore':len(rules.ignore_paths),'unordered':len(rules.unordered_paths),'case_insensitive':len(rules.case_insensitive_paths),'tolerances':len(rules.numeric_tolerance),'keyed_arrays':len(rules.keyed_arrays),'severity':len(rules.severity_paths),'sensitive':len(rules.sensitive_paths)}},indent=2))
        else:
            if not a.path: raise SystemExit('rules explain requires PATH')
            matches={'ignored':rules.ignored(a.path),'unordered':rules.unordered(a.path),'case_insensitive':rules.case_insensitive(a.path),'tolerance':rules.tolerance_for(a.path),'array_key':rules.array_key_for(a.path),'severity':[{'pattern':p,'level':v} for p,v in rules.severity_paths.items() if __import__('fnmatch').fnmatch(a.path,p)],'sensitive':[p for p in rules.sensitive_paths if __import__('fnmatch').fnmatch(a.path,p)]}; _write(json.dumps(matches,indent=2))
    elif a.command=='openapi':
        out=analyze_openapi(load(a.left),load(a.right))
        if a.format=='json': content=json.dumps(out,indent=2,ensure_ascii=False,default=str)
        elif a.format=='pr': content='## OpenAPI compatibility report\n\n'+('✅ Compatible' if out['compatible'] else f"❌ {out['breaking_changes']} breaking change(s)")+'\n\n'+'\n'.join(f"- **{x['severity'].upper()}** `{x['path']}`: {x['message']}" for x in out['findings'])+'\n'
        else: content=('Compatible\n' if out['compatible'] else f"Breaking changes: {out['breaking_changes']}\n")+'\n'.join(f"[{x['severity'].upper()}] {x['path']} - {x['message']}" for x in out['findings'])+'\n'
        _write(content,a.output)
        if a.fail_on_breaking and not out['compatible']: raise SystemExit(5)
    elif a.command=='baseline':
        if a.action=='create': baseline_create(a.document,a.target); _write(f'Baseline created: {a.target}\n')
        else: out=baseline_check(a.document,a.target,Rules.load(a.rules)); _write(_render(out,a.format),a.output)
