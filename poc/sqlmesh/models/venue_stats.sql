MODEL (
  name matchprism.venue_stats,
  kind FULL,
  description 'Per-venue aggregates: matches played, average first-innings score, average run rate.',
  audits (
    not_null(columns := (venue, matches_played)),
    unique_values(columns := (venue))
  )
);

WITH first_innings_totals AS (
  SELECT
    match_id,
    venue,
    SUM(runs_total) AS first_innings_total
  FROM matchprism.stg_deliveries
  WHERE innings_num = 1
  GROUP BY match_id, venue
),
venue_aggregates AS (
  SELECT
    venue,
    COUNT(DISTINCT match_id) AS matches_played,
    ROUND(AVG(first_innings_total), 1) AS avg_first_innings_score
  FROM first_innings_totals
  GROUP BY venue
),
run_rate AS (
  SELECT
    venue,
    ROUND(SUM(runs_total)::DOUBLE * 6.0 / NULLIF(COUNT(*), 0), 2) AS avg_run_rate,
    ROUND(SUM(CASE WHEN runs_batter = 6 THEN 1 ELSE 0 END)::DOUBLE * 100.0 / NULLIF(COUNT(*), 0), 2) AS six_pct
  FROM matchprism.stg_deliveries
  GROUP BY venue
)
SELECT
  va.venue,
  va.matches_played,
  va.avg_first_innings_score,
  rr.avg_run_rate,
  rr.six_pct
FROM venue_aggregates va
JOIN run_rate rr USING (venue)
ORDER BY va.venue
