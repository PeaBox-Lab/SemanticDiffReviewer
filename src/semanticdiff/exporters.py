from __future__ import annotations
from html import escape
import json
from .engine import DiffResult

def render_json(result: DiffResult) -> str:
    return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)

def render_markdown(result: DiffResult) -> str:
    s = result.summary
    lines = ["# SemanticDiff Report", "", f"**Status:** {'Equivalent' if result.equal else 'Different'}", "", f"Added: {s['added']} | Removed: {s['removed']} | Changed: {s['changed']} | Type changed: {s['type_changed']} | Ignored: {s['ignored']}", "", "| Path | Change | Left | Right |", "|---|---|---|---|"]
    for d in result.differences:
        left = json.dumps(d.left, ensure_ascii=False).replace("|", "\\|")
        right = json.dumps(d.right, ensure_ascii=False).replace("|", "\\|")
        lines.append(f"| `{d.path}` | {d.kind} | `{left}` | `{right}` |")
    return "\n".join(lines) + "\n"

def render_html(result: DiffResult) -> str:
    rows = "".join(f"<tr><td><code>{escape(d.path)}</code></td><td><span class='{escape(d.kind)}'>{escape(d.kind)}</span></td><td><pre>{escape(json.dumps(d.left, ensure_ascii=False, indent=2))}</pre></td><td><pre>{escape(json.dumps(d.right, ensure_ascii=False, indent=2))}</pre></td></tr>" for d in result.differences)
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>SemanticDiff Report</title><style>body{{font:14px system-ui;margin:32px;color:#172033}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #d8deea;padding:10px;text-align:left;vertical-align:top}}th{{background:#f2f5fa}}pre{{white-space:pre-wrap;max-width:520px}}span{{padding:3px 7px;border-radius:10px;background:#eee}}.added{{background:#d9fbe5}}.removed{{background:#ffe0e0}}.changed,.type_changed{{background:#fff1c7}}</style></head><body><h1>SemanticDiff Report</h1><p><strong>{'Equivalent' if result.equal else 'Different'}</strong></p><pre>{escape(json.dumps(result.summary, indent=2))}</pre><table><thead><tr><th>Path</th><th>Change</th><th>Left</th><th>Right</th></tr></thead><tbody>{rows}</tbody></table></body></html>'''

def render_csv_payload(payload: dict) -> str:
    import csv, io
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=["path", "kind", "severity", "message", "explanation", "left", "right"])
    writer.writeheader()
    for item in payload.get("differences", []):
        row = {k: item.get(k) for k in writer.fieldnames}
        row["left"] = json.dumps(row["left"], ensure_ascii=False)
        row["right"] = json.dumps(row["right"], ensure_ascii=False)
        writer.writerow(row)
    return out.getvalue()

def render_json_patch(payload: dict) -> str:
    ops = []
    for d in payload.get("differences", []):
        if d["kind"] == "added": ops.append({"op": "add", "path": d["path"], "value": d.get("right")})
        elif d["kind"] == "removed": ops.append({"op": "remove", "path": d["path"]})
        elif d["kind"] in {"changed", "type_changed"}: ops.append({"op": "replace", "path": d["path"], "value": d.get("right")})
    return json.dumps(ops, indent=2, ensure_ascii=False)

def render_sarif_payload(payload: dict) -> str:
    from .workflows import sarif
    return json.dumps(sarif(payload), indent=2, ensure_ascii=False)

def render_pr_markdown(payload: dict) -> str:
    icons={'critical':'🔴','high':'🟠','medium':'🟡','low':'🔵','info':'⚪'}
    counts={k:0 for k in icons}
    for d in payload.get('differences',[]): counts[d.get('severity','medium')]=counts.get(d.get('severity','medium'),0)+1
    lines=['## SemanticDiff report','',f"**Overall risk:** {payload.get('risk','none').upper()}",'', ' | '.join(f"{icons[k]} {k}: {v}" for k,v in counts.items()),'']
    if not payload.get('differences'): return '\n'.join(lines+['✅ No semantic differences found.',''])
    lines += ['| Severity | Path | Change | Explanation |','|---|---|---|---|']
    for d in payload['differences'][:100]: lines.append(f"| {icons.get(d.get('severity'),'⚪')} {d.get('severity')} | `{d['path']}` | {d['kind']} | {d.get('explanation','')} |")
    if len(payload['differences'])>100: lines += ['',f"_Showing 100 of {len(payload['differences'])} changes._"]
    return '\n'.join(lines)+'\n'
