# FinSights

**Explainable relationship intelligence for markets — powered by [Prometheux](https://www.prometheux.ai/).**

> Who's connected to whom, who's exposed to what — and the proof.

FinSights turns a flat stream of company facts into a *reasoned, explainable* map. A side project
(**braindb**) ingests news/filings into verified company entities + facts; one **SQL** query exports
them; an **LLM** classifies each co‑mention into a clean relation (`supplies` / `invests_in` /
`partners_with` / `competes_with`); then **Prometheux** does what SQL and LLMs can't — recursive,
*explainable* reasoning that derives the **indirect connections** and **risk exposure** across the
network.

It discovers, *with a proof chain*, that a **West Texas gas field** and a value stock (**Smart Sand**)
are both exposed to the **AI‑datacenter capex boom** — three hops away.

## Pipeline

```
braindb (wikis + facts)  →  SQL export  →  LLM classify  →  Prometheux reason  →  dashboard
   memory / extraction     data/*.sql     data/*.json      prometheux/*         index.html
```

## What's here

| Path | What |
|---|---|
| `index.html` | Static dashboard (vis-network). Open it, or deploy to Vercel. |
| `data/braindb_export.sql` | The read-only SQL that exports the relation material from braindb. |
| `data/facts.json` | Source facts → the LLM transform (could be run live). |
| `data/relations.json` | LLM-classified company relations (4 lean types). |
| `prometheux/rules.vada` | The Vadalog: `connected` (indirect) + `ai_exposed` (recursive). |
| `prometheux/reason.py` | Runs the rules on Prometheux → writes `prometheux/insights.json`. |
| `prometheux/insights.json` | Prometheux output the dashboard renders. |

## Run the reasoning yourself

```bash
pip install prometheux_chain
cp prometheux/.env.example prometheux/.env   # add your Prometheux token (never commit it)
python prometheux/reason.py                   # regenerates prometheux/insights.json
python build_site.py                          # bakes data+insights into index.html
```

## Deploy (Vercel)

Static site, zero config — `index.html` at the root:

```bash
vercel --prod
```

## Why Prometheux (not just SQL)

A map of *direct* deals is plain SQL. **Prometheux earns its place on the recursive, signed,
explainable layer**: it derives that a gas field is exposed to AI capex *3 hops away* — and shows
the chain. SQL can't express that with a proof; an LLM can't do it reliably. That derived,
auditable layer (the dashed links + the exposure highlight + PageRank centrality) is Prometheux.
