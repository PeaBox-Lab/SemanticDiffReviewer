from pathlib import Path

p = Path("src/semanticdiff/templates/index.html")
content = p.read_text(encoding="utf-8")
idx = content.find("<script>")
new_script = '''<script>
const $ = s => document.querySelector(s);
const fields = () => ({left:$('left').value, right:$('right').value, rules:$('rules').value, schema:$('schema').value, preset:$('preset').value});
let current = null;

function esc(s){return String(s).replace(/[&<>']/g,c=>({"&":"&","<":"<",">":">","":"",":":""}[c]));}

function sevClass(s){return {"critical":"sev-critical","high":"sev-high","medium":"sev-medium","low":"sev-low","info":"sev-info"}[s]||""}
function riskClass(r){return {"critical":"risk-critical","high":"risk-high","medium":"risk-medium","low":"risk-low","info":"risk-info"}[r]||"risk-info"}

async function compareDocs(){
  const btn = document.querySelector("button[onclick=compareDocs()]");
  const orig = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = "<svg style=\"width:16px;height:16px;animation:spin 1s linear infinite\" viewBox=\"0 0 24 24\"><circle cx=\"12\" cy=\"12\" r=\"10\" stroke=\"currentColor\" fill=\"none\" stroke-width=\"3\" stroke-dasharray=\"30 30\" stroke-linecap=\"round\"/></svg>Comparing…";
  const style = document.createElement("style"); style.textContent = "@keyframes spin{to{transform:rotate(360deg)}}"; document.head.appendChild(style);
  try{
    const f = new FormData(); Object.entries(fields()).forEach(([k,v])=>f.append(k,v));
    const r = await fetch("/api/compare",{method:"POST",body:f});
    if(!r.ok){ $('rows').textContent = await r.text(); toast("Comparison failed","bad"); return }
    current = await r.json(); render();
  }catch(e){ toast("Network error","bad"); }
  finally{ btn.disabled = false; btn.innerHTML = orig; style.remove(); }
}

function render(){
  if(!current){ $('stats').innerHTML=""; $('summary').innerHTML=""; return }
  const s = current.summary;
  $('stats').innerHTML = '<div class="stat"><b>'+s.added+'</b><span>Added</span></div><div class="stat"><b>'+s.removed+'</b><span>Removed</span></div><div class="stat"><b>'+s.changed+'</b><span>Changed</span></div><div class="stat"><b>'+s.type_changed+'</b><span>Type</span></div><div class="stat"><b>'+s.ignored+'</b><span>Ignored</span></div>';
  const risk = current.risk || "info";
  $('summary').innerHTML = '<span class="equal-pill '+(current.equal?"eq":"neq")+'">'+(current.equal?"✓ Equivalent":"≠ Different")+'</span><span class="risk '+riskClass(risk)+'">'+risk+'</span>';
  renderRows();
}

function renderRows(){
  const el = $('rows');
  if(!current){ el.innerHTML=""; return }
  const q = $('search').value.toLowerCase();
  const sev = $('severity').value;
  const ds = current.differences.filter(d=>(!sev||d.severity===sev)&&(!q||(d.path+' '+d.explanation).toLowerCase().includes(q)));
  if(!ds.length){ el.innerHTML = '<div style="padding:40px;text-align:center;color:var(--muted)">No differences'+(q?" matching filter":"")+(sev?" of "+sev+" severity":"")+'</div>'; return; }
  el.innerHTML = '<table><thead><tr><th style="width:35%">Path & explanation</th><th style="width:12%">Change</th><th style="width:10%">Impact</th><th>Values</th></tr></thead><tbody>'+ds.map(d=>'<tr><td><code class="path">'+esc(d.path)+'</code><div class="expl">'+esc(d.explanation)+'</div></td><td>'+d.kind+'</td><td class="'+sevClass(d.severity)+'">'+(d.severity||"—")+'</td><td><pre>Before: '+esc(JSON.stringify(d.left,null,2))+'</pre><pre>After: '+esc(JSON.stringify(d.right,null,2))+'</pre></td></tr>').join("")+'</tbody></table>';
}

function readFile(e,id){
  const f = e.target.files[0]; if(!f) return;
  const r = new FileReader(); r.onload = () => { $('+id+').value = r.result; }; r.readAsText(f);
  e.target.value = "";
}

function swap(){ const x = $('left').value; $('left').value = $('right').value; $('right').value = x; }
function clearAll(){ $('left').value = $('right').value = $('schema').value = ""; current = null; $('rows').innerHTML = $('stats').innerHTML = $('summary').innerHTML = ""; }
function sample(){
  $('left').value = "service:\n  name: API\n  replicas: 2\n  token: old-secret\n  tags: [stable, public]";
  $('right').value = "service:\n  name: api\n  replicas: 4\n  token: new-secret\n  tags: [public, stable]";
  $('preset').value = "human-friendly";
  compareDocs();
}
async function download(fmt){
  const f = new FormData(); Object.entries(fields()).forEach(([k,v])=>f.append(k,v));
  const r = await fetch("/export/"+fmt,{method:"POST",body:f});
  if(!r.ok){ toast("Export failed","bad"); return }
  const b = await r.blob(); const a = document.createElement("a");
  a.href = URL.createObjectURL(b); a.download = "semanticdiff."+((fmt==="markdown")?"md":fmt); a.click();
  toast((fmt.toUpperCase()+" report downloaded"),"good");
}
function toast(msg,type="good"){ const t=$('toast'); t.textContent=msg; t.className="toast "+type+" show"; setTimeout(()=>t.classList.remove("show"),2800); }
function openHelp(){ $('help').showModal(); }
function closeHelp(){ $('help').close(); }
document.addEventListener("keydown",e=>{
  if((e.ctrlKey||e.metaKey)&&e.key==="Enter"){ e.preventDefault(); compareDocs(); }
  else if(!e.ctrlKey&&!e.metaKey&&!e.target.matches("textarea,input,select")){
    if(e.key==="s"||e.key==="S") swap();
    else if(e.key==="m"||e.key==="M") sample();
    else if(e.key==="c"||e.key==="C") clearAll();
    else if(e.key==="?") openHelp();
  }
});
["left","right"].forEach(id=>{
  const drop = $('drop'+id.toUpperCase()[0]); const ta = $(''+id);
  ["dragenter","dragover"].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault(); drop.classList.add("dragging");}));
  ["dragleave","drop"].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault(); drop.classList.remove("dragging");}));
  drop.addEventListener("drop",e=>{ const f=e.dataTransfer.files[0]; if(f){ const r=new FileReader(); r.onload=()=>ta.value=r.result; r.readAsText(f); } });
});
$('preset').addEventListener("change",compareDocs);
</script>
</body>
</html>
'''
new_content = content[:idx] + new_script
p.write_text(new_content, encoding="utf-8")
print("OK")
