-- braindb_export.sql
-- Run (read-only) against a braindb Postgres to EXPORT the raw material for the
-- relation graph. braindb stores verified entities as `wiki` rows and atomic
-- `fact` rows; a relation candidate is any fact that co-mentions two verified
-- company wikis. The LLM then classifies each into a relation type (see facts.json).
--
--   psql "$DATABASE_URL" -f data/braindb_export.sql
--
-- Output columns: company_a | company_b | fact   (one row per co-mention)

WITH companies AS (
    SELECT e.id, coalesce(w.canonical_name, e.title) AS name
    FROM entities e
    JOIN wikis_ext w ON w.entity_id = e.id
    WHERE e.entity_type = 'wiki'
      AND length(coalesce(w.canonical_name, e.title)) >= 4
),
facts AS (
    SELECT id, content
    FROM entities
    WHERE entity_type = 'fact'
)
SELECT a.name  AS company_a,
       b.name  AS company_b,
       f.content AS fact
FROM   facts f
JOIN   companies a ON f.content ILIKE '%' || a.name || '%'
JOIN   companies b ON f.content ILIKE '%' || b.name || '%'
                  AND a.name < b.name          -- unordered pair, no self-join dup
ORDER  BY company_a, company_b;
