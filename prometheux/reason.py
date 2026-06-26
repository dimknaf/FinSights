#!/usr/bin/env python3
"""FinSights — Prometheux reasoning over the braindb relation export.

Loads data/relations.json, runs the Vadalog program (prometheux/rules.vada) on Prometheux,
and writes prometheux/insights.json (indirect connections + AI-datacenter exposure + PageRank).

Credentials come from the ENVIRONMENT ONLY (copy .env.example -> prometheux/.env). No secrets here.

    pip install prometheux_chain
    cp prometheux/.env.example prometheux/.env   # then fill it in
    python prometheux/reason.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _load_env():
    p = os.path.join(HERE, ".env")
    if os.path.isfile(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main():
    _load_env()
    tok, url = os.environ.get("PMTX_TOKEN"), os.environ.get("JARVISPY_URL")
    if not tok or not url:
        sys.exit("Set PMTX_TOKEN and JARVISPY_URL (copy prometheux/.env.example -> prometheux/.env). No keys are committed.")

    import prometheux_chain as px
    px.config.set("PMTX_TOKEN", tok)
    px.config.set("JARVISPY_URL", url)

    data = json.load(open(os.path.join(ROOT, "data", "relations.json"), encoding="utf-8"))
    rels = data["relations"]
    rules = open(os.path.join(HERE, "rules.vada"), encoding="utf-8").read()
    q = lambda s: '"' + s + '"'
    program = "\n".join(f'relation({q(r["from"])},{q(r["to"])},{q(r["type"])}).' for r in rels) + "\n" + rules

    proj = px.save_project(project_name="FinSights")

    def run(name):
        px.save_concept(project_id=proj, definition=program, concept_name=name,
                        output_predicate=name, force_overwrite=True)
        px.run_concept(project_id=proj, concept_name=name, persist_outputs=True)
        return px.fetch_results(project_id=proj, output_predicate=name, page_size=1000).get("results", {}).get("facts", [])

    connected = run("connected")
    exposed = run("ai_exposed")

    pr = {}
    try:
        run("edge")  # materialize the edge predicate so graph-analytics can read it
        r = px.run_graph_analytics(project_id=proj, output_predicate="edge",
                                   column_roles={"source": 0, "target": 1}, function="pagerank")
        for n in (r or {}).get("nodes", []):
            pr[n["id"]] = round(float(n.get("analytics", {}).get("score", 0)), 4)
    except Exception as e:
        print("pagerank skipped:", str(e)[:120])

    direct = {(r["from"], r["to"]) for r in rels}
    direct |= {(b, a) for a, b in list(direct)}
    indirect = sorted({tuple(sorted((a, b))) for a, b in connected if a < b and (a, b) not in direct})

    out = {
        "project": proj,
        "platform": "https://platform.prometheux.ai",
        "nodes": data["nodes"],
        "relations": rels,
        "indirect": [list(p) for p in indirect],
        "exposed": sorted([[w, how] for w, how in exposed]),
        "centrality": pr,
        "headline": "A West Texas gas field and Smart Sand (a value stock) are both exposed to the AI-datacenter buildout — derived by Prometheux, with the chain.",
    }
    json.dump(out, open(os.path.join(HERE, "insights.json"), "w", encoding="utf-8"), indent=2)
    print(f"wrote prometheux/insights.json | indirect={len(indirect)} exposed={len(exposed)} centrality={len(pr)} project={proj}")


if __name__ == "__main__":
    main()
