from __future__ import annotations
from typing import Any

HTTP_METHODS={"get","put","post","delete","options","head","patch","trace"}

def _ops(spec:dict[str,Any])->dict[tuple[str,str],dict[str,Any]]:
    out={}
    for path,item in (spec.get("paths") or {}).items():
        if isinstance(item,dict):
            for method,operation in item.items():
                if method.lower() in HTTP_METHODS and isinstance(operation,dict): out[(path,method.lower())]=operation
    return out

def _schema_type(schema:Any)->Any:
    return schema.get("type") if isinstance(schema,dict) else None

def analyze_openapi(old:dict[str,Any],new:dict[str,Any])->dict[str,Any]:
    findings=[]; a,b=_ops(old),_ops(new)
    def add(path,kind,severity,message,breaking=True): findings.append({"path":path,"kind":kind,"severity":severity,"breaking":breaking,"message":message})
    for path,method in sorted(a.keys()-b.keys()): add(f"{method.upper()} {path}","operation_removed","critical","API operation was removed")
    for path,method in sorted(b.keys()-a.keys()): add(f"{method.upper()} {path}","operation_added","info","API operation was added",False)
    for key in sorted(a.keys()&b.keys()):
        left,right=a[key],b[key]; label=f"{key[1].upper()} {key[0]}"
        lp={(p.get('in'),p.get('name')):p for p in left.get('parameters',[]) if isinstance(p,dict)}; rp={(p.get('in'),p.get('name')):p for p in right.get('parameters',[]) if isinstance(p,dict)}
        for param in sorted(lp.keys()-rp.keys(),key=str): add(f"{label} parameter {param[0]}:{param[1]}","parameter_removed","high","Request parameter was removed")
        for param in sorted(rp.keys()-lp.keys(),key=str):
            required=bool(rp[param].get('required')); add(f"{label} parameter {param[0]}:{param[1]}","required_parameter_added" if required else "parameter_added","high" if required else "info","Required request parameter was added" if required else "Optional request parameter was added",required)
        for param in sorted(lp.keys()&rp.keys(),key=str):
            if not lp[param].get('required') and rp[param].get('required'): add(f"{label} parameter {param[0]}:{param[1]}","parameter_became_required","high","Optional parameter became required")
            lt,rt=_schema_type(lp[param].get('schema')), _schema_type(rp[param].get('schema'))
            if lt and rt and lt!=rt: add(f"{label} parameter {param[0]}:{param[1]}","parameter_type_changed","critical",f"Parameter type changed from {lt} to {rt}")
        lresp=set((left.get('responses') or {}).keys()); rresp=set((right.get('responses') or {}).keys())
        for status in sorted(lresp-rresp): add(f"{label} response {status}","response_removed","high",f"Response status {status} was removed")
        old_security=left.get('security',old.get('security')); new_security=right.get('security',new.get('security'))
        if old_security and not new_security: add(label,"security_removed","critical","Security requirement was removed")
    counts={s:sum(f['severity']==s for f in findings) for s in ('critical','high','medium','low','info')}
    return {"compatible":not any(f['breaking'] for f in findings),"breaking_changes":sum(f['breaking'] for f in findings),"summary":counts,"findings":findings}
