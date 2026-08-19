-- Run via transform.py or:
--   duckdb data/geneva.duckdb < scripts/validate.sql

CREATE OR REPLACE VIEW v_volume_v1 AS
SELECT
  f.freq,
  f.year,
  f.quarter,
  t.segment_v1,
  f.n,
  f.value_chf,
  f.value_chf / NULLIF(f.n, 0) AS avg_ticket_chf
FROM fact_volume f
JOIN dim_type t USING (type_id)
WHERE t.segment_v1 IS NOT NULL
  AND t.is_ensemble = 1;

CREATE OR REPLACE VIEW v_check_q_vs_year AS
SELECT
  q.year,
  q.type_id,
  q.n_q,
  y.n_y,
  q.n_q - y.n_y AS n_gap
FROM (
  SELECT year, type_id, SUM(n) AS n_q
  FROM fact_volume
  WHERE freq = 'Q' AND source = 'T_05_05_1_1_01'
  GROUP BY 1, 2
) q
JOIN (
  SELECT year, type_id, n AS n_y
  FROM fact_volume
  WHERE freq = 'Y' AND source = 'T_05_05_1_2_01'
) y USING (year, type_id);

CREATE OR REPLACE VIEW v_price_map_ppe AS
SELECT
  p.year,
  g.geo_id,
  g.bfs_id,
  g.name_ocstat,
  g.has_polygon,
  p.median AS median_chf_m2,
  p.n
FROM fact_price p
JOIN dim_geo g USING (geo_id)
WHERE p.source = 'T_05_05_1_4_03'
  AND p.market = 'libre'
  AND p.condition = 'existing'
  AND g.grain = 'commune';

-- Join quality: named communes must hit dim_geo. Autres stay unmatched on purpose.
CREATE OR REPLACE VIEW v_join_geo AS
SELECT
  p.source,
  COUNT(*) AS n_rows,
  SUM(CASE WHEN p.geo_id IS NOT NULL THEN 1 ELSE 0 END) AS n_mapped,
  SUM(CASE WHEN p.geo_label LIKE 'Autres%' THEN 1 ELSE 0 END) AS n_residual,
  SUM(CASE WHEN p.geo_id IS NULL AND (p.geo_label IS NULL OR p.geo_label NOT LIKE 'Autres%') THEN 1 ELSE 0 END) AS n_unmatched
FROM fact_price p
GROUP BY 1;
