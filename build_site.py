#!/usr/bin/env python3
"""Bake data/relations.json + prometheux/insights.json (+ the SQL) into a single
self-contained index.html (data inlined -> works on file:// and Vercel with zero config)."""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
rel = json.load(open(os.path.join(ROOT, "data", "relations.json"), encoding="utf-8"))
ins = json.load(open(os.path.join(ROOT, "prometheux", "insights.json"), encoding="utf-8"))
sql = open(os.path.join(ROOT, "data", "braindb_export.sql"), encoding="utf-8").read()

DATA = {
    "nodes": rel["nodes"],
    "relations": rel["relations"],
    "exposed": ins["exposed"],
    "centrality": ins["centrality"],
    "indirect": ins["indirect"],
    "headline": ins["headline"],
    "project": ins.get("project", ""),
    "sql": sql,
}

TPL = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>FinSights — explainable relationship intelligence (Prometheux)</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
:root{--bg:#0b0e14;--panel:#11161f;--line:#222b38;--txt:#e8edf3;--mut:#8b97a7;--px:#3fb950}
*{box-sizing:border-box}body{margin:0;font-family:"Segoe UI",system-ui,Arial,sans-serif;background:var(--bg);color:var(--txt)}
header{padding:14px 20px;background:linear-gradient(90deg,#11161f,#0b0e14);border-bottom:1px solid var(--line);display:flex;align-items:center;gap:14px;flex-wrap:wrap}
header h1{margin:0;font-size:20px;font-weight:800}header .tag{color:var(--mut);font-size:13px}
.badge{background:#0f2a1b;color:var(--px);border:1px solid #1f6f44;border-radius:20px;padding:3px 11px;font-size:12px;font-weight:700}
.pipe{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:9px 20px;background:#0e131b;border-bottom:1px solid var(--line);font-size:12px;color:var(--mut)}
.pipe b{color:var(--txt)}.pipe .step{background:#11161f;border:1px solid var(--line);border-radius:8px;padding:5px 10px}
.pipe .arr{color:var(--px)}
details{margin-left:auto}summary{cursor:pointer;color:var(--px)}
pre{background:#0b0e14;border:1px solid var(--line);border-radius:8px;padding:10px;font-size:11px;overflow:auto;max-width:560px;color:#9ad}
#wrap{display:flex;height:calc(100vh - 112px)}#net{flex:1}
#side{width:350px;background:var(--panel);border-left:1px solid var(--line);padding:14px;overflow:auto;font-size:13px}
h3{margin:14px 0 8px;font-size:12px;color:var(--mut);text-transform:uppercase;letter-spacing:1px}
#insight{background:#10261b;border:1px solid #1f6f44;border-radius:8px;padding:11px;font-size:12px;line-height:1.5}
#insight b{color:var(--px)}
.ctl{margin:5px 0}.sw{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:middle}
.card{background:#0e131b;border:1px solid var(--line);border-radius:7px;padding:9px 11px;margin:7px 0}
.tag2{display:inline-block;font-size:10px;padding:1px 7px;border-radius:20px;margin-left:5px}
.fact{color:var(--mut);font-style:italic;margin-top:6px;font-size:12px}
footer{padding:7px 20px;font-size:11px;color:var(--mut);background:var(--panel);border-top:1px solid var(--line)}
a{color:var(--px)}
</style></head><body>
<header>
  <h1>FinSights</h1><span class="tag">who's connected to whom, who's exposed to what — and the proof.</span>
  <span class="badge">⬢ reasoning by Prometheux</span>
</header>
<div class="pipe">
  <span class="step"><b>braindb</b> wikis+facts</span><span class="arr">→</span>
  <span class="step"><b>SQL</b> export</span><span class="arr">→</span>
  <span class="step"><b>LLM</b> classify</span><span class="arr">→</span>
  <span class="step" style="border-color:#1f6f44;color:var(--px)"><b>Prometheux</b> reason</span><span class="arr">→</span>
  <span class="step">this dashboard</span>
  <details><summary>view the braindb SQL export</summary><pre>__SQL__</pre></details>
</div>
<div id="wrap"><div id="net"></div>
<div id="side">
  <h3>⬢ Prometheux insights</h3><div id="insight"></div>
  <h3>Layers</h3>
  <div class="ctl"><label><input type="checkbox" id="ind" checked> Prometheux indirect links (dashed)</label></div>
  <div class="ctl"><label><input type="checkbox" id="exp"> highlight AI-datacenter exposure</label></div>
  <h3>Relation types</h3><div id="filters"></div>
  <h3>Details</h3><div id="info">Click a node or an edge.</div>
</div></div>
<footer>Data: braindb export (news + value-investing wikis) → LLM → Prometheux (Vadalog). Live project on
<a href="https://platform.prometheux.ai" target="_blank">platform.prometheux.ai</a> · __PROJECT__ · node size = PageRank centrality.</footer>
<script>
const DATA = __DATA__;
const SECTOR={Tech:"#4f8cff",Semis:"#00bcd4",Energy:"#ff9800",Pharma:"#4caf50",Space:"#9c27b0",Finance:"#e3b341",Materials:"#c9a227",Theme:"#8b949e"};
const ETYPE={supplies:"#db6d28",invests_in:"#8957e5",partners_with:"#2ea043",competes_with:"#e5534b"};
const C=DATA.centrality||{}, expReason={}; DATA.exposed.forEach(([n,r])=>{if(!expReason[n])expReason[n]=r;});
const lbl=id=>(DATA.nodes.find(n=>n.id===id)||{}).label||id.replace(/_/g," ");

const nodes=new vis.DataSet(DATA.nodes.map(n=>({
  id:n.id,label:n.label||n.id.replace(/_/g," "),
  color:{background:SECTOR[n.sector]||"#888",border:SECTOR[n.sector]||"#888"},
  font:{color:"#fff",size:13},shape:"dot",size:14+(C[n.id]||0.02)*150,
  _sector:n.sector,_exp:expReason[n.id]||null
})));
const dEdges=DATA.relations.map((r,i)=>({id:"d"+i,from:r.from,to:r.to,etype:r.type,fact:r.fact,mag:r.magnitude,
  arrows:"to",color:{color:ETYPE[r.type],highlight:ETYPE[r.type]},width:Math.max(1.2,(r.magnitude||4)/2),
  title:r.type+" · mag "+(r.magnitude||"")}));
const iEdges=DATA.indirect.map((p,i)=>({id:"i"+i,from:p[0],to:p[1],kind:"ind",dashes:true,color:{color:"#5b6675"},width:0.7}));
const edges=new vis.DataSet([]);
const net=new vis.Network(document.getElementById("net"),{nodes,edges},
  {physics:{stabilization:true,barnesHut:{springLength:150,gravitationalConstant:-6000}},interaction:{hover:true}});

const active=new Set(Object.keys(ETYPE)), show={ind:true,exp:false};
function refresh(){
  const es=dEdges.filter(e=>active.has(e.etype)).slice();
  if(show.ind) es.push(...iEdges);
  edges.clear(); edges.add(es);
  nodes.update(DATA.nodes.map(n=>{
    const exposed=!!expReason[n.id];
    const dim=show.exp&&!exposed;
    const glow=show.exp&&exposed;
    return {id:n.id,opacity:dim?0.25:1,
      borderWidth:glow?4:1,
      color:{background:SECTOR[n.sector]||"#888",border:glow?(expReason[n.id]==="via supply chain"?"#ff7b72":"#f0a500"):(SECTOR[n.sector]||"#888")},
      shadow:glow?{enabled:true,color:expReason[n.id]==="via supply chain"?"#ff7b72":"#f0a500",size:24,x:0,y:0}:false};
  }));
}
document.getElementById("ind").onchange=e=>{show.ind=e.target.checked;refresh();};
document.getElementById("exp").onchange=e=>{show.exp=e.target.checked;refresh();};
const fdiv=document.getElementById("filters");
Object.keys(ETYPE).forEach(t=>fdiv.innerHTML+=`<div class="ctl"><label><input type="checkbox" id="f_${t}" checked> <span class="sw" style="background:${ETYPE[t]}"></span>${t}</label></div>`);
Object.keys(ETYPE).forEach(t=>document.getElementById("f_"+t).onchange=e=>{e.target.checked?active.add(t):active.delete(t);refresh();});

// insights panel
const topC=Object.entries(C).sort((a,b)=>b[1]-a[1]).slice(0,3).map(([k,v])=>`${lbl(k)} (${v})`).join(", ");
const chainExp=DATA.exposed.filter(([n,r])=>r==="via supply chain").map(([n])=>lbl(n));
document.getElementById("insight").innerHTML=`
  <b>${DATA.indirect.length} indirect connections</b> derived (transitive — in no single fact).<br><br>
  <b>${DATA.exposed.length} entities exposed</b> to the AI-datacenter buildout. Most striking (via supply chain): <b>${chainExp.map(x=>x).join(", ")}</b>.<br><br>
  <b>Most central</b> (PageRank): ${topC}.<br><br>
  🔥 ${DATA.headline}`;

const info=document.getElementById("info");
net.on("click",p=>{
  if(p.edges.length&&!p.nodes.length){const id=p.edges[0];const d=dEdges.find(e=>e.id===id);
    if(d) info.innerHTML=`<b>${lbl(d.from)} → ${lbl(d.to)}</b> <span class="tag2" style="background:${ETYPE[d.etype]}">${d.etype}</span><div class="fact">"${d.fact}"</div>`;
    else info.innerHTML=`<b>indirect link</b> <span class="tag2" style="background:#3fb950">Prometheux-derived</span><br>connected only through a chain — in no single fact.`;
  } else if(p.nodes.length){const n=p.nodes[0];
    const dl=dEdges.filter(e=>e.from===n||e.to===n).map(e=>`• ${e.from===n?"→ "+lbl(e.to):"← "+lbl(e.from)} (${e.etype})`);
    const ex=expReason[n]?`<br><span style="color:#3fb950">AI-exposed:</span> ${expReason[n]}`:"";
    info.innerHTML=`<b>${lbl(n)}</b>${ex}<br>${dl.join("<br>")||"(no direct relations)"}`;}
});
refresh();
</script></body></html>"""

html = (TPL.replace("__DATA__", json.dumps(DATA))
            .replace("__SQL__", DATA["sql"].replace("<", "&lt;").replace(">", "&gt;"))
            .replace("__PROJECT__", "project " + DATA["project"]))
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
print("wrote index.html  (%d KB)" % (len(html) // 1024))
