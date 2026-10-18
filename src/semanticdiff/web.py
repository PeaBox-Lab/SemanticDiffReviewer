from __future__ import annotations
from pathlib import Path
import json, yaml
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, Response
from .loader import loads
from .rules import Rules
from .engine import compare
from .schema import validate_pair
from .insights import enrich
from .presets import get_preset, merge
from .exporters import render_markdown, render_html
app=FastAPI(title="SemanticDiff Studio",version="2.0.0")
TEMPLATE=(Path(__file__).parent/"templates"/"index.html").read_text(encoding="utf-8")
@app.get("/",response_class=HTMLResponse)
def index(): return TEMPLATE
@app.get("/health")
def health(): return {"status":"ok","version":"2.0.0"}
def build(left,right,rules="",schema="",preset=""):
    l,r=loads(left),loads(right); rr=merge(get_preset(preset or None),Rules.from_dict(yaml.safe_load(rules) if rules.strip() else {})); payload=enrich(compare(l,r,rr).to_dict(),rr.severity_paths,rr.sensitive_paths,True); payload["validation"]=validate_pair(l,r,loads(schema)) if schema.strip() else None; return payload
@app.post("/api/compare")
def api_compare(left:str=Form(...),right:str=Form(...),rules:str=Form(""),schema:str=Form(""),preset:str=Form("")): return build(left,right,rules,schema,preset)
@app.post("/export/{fmt}")
def export(fmt:str,left:str=Form(...),right:str=Form(...),rules:str=Form(""),schema:str=Form(""),preset:str=Form("")):
    payload=build(left,right,rules,schema,preset)
    if fmt=="json": content=json.dumps(payload,indent=2,ensure_ascii=False); media="application/json"; ext="json"
    elif fmt=="markdown":
        lines=["# SemanticDiff Studio Report","",f"**Overall risk:** {payload['risk']}",""]+[f"- **{d['severity']}** `{d['path']}`: {d['explanation']}" for d in payload['differences']]; content="\n".join(lines); media="text/markdown"; ext="md"
    elif fmt=="html": content="<html><body><h1>SemanticDiff Studio Report</h1><pre>"+json.dumps(payload,indent=2).replace("&","&amp;").replace("<","&lt;")+"</pre></body></html>"; media="text/html"; ext="html"
    else:return Response("Unsupported",status_code=400)
    return Response(content,media_type=media,headers={"Content-Disposition":f"attachment; filename=semanticdiff.{ext}"})
def main():
    import uvicorn; uvicorn.run("semanticdiff.web:app",host="127.0.0.1",port=8765)
