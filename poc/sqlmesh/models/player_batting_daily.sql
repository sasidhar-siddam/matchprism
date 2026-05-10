MODEL (
  name matchprism.player_batting_daily,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column match_date,
    batch_size 30
  ),
  start '2024-01-01',
  cron '@daily',
  description 'Per-batter, per-match-date batting stats. Incremental by match_date so a new match only triggers a partial rebuild.',
  audits (
    not_null(columns := (batter, match_date))
  )
);

SELECT
  batter,
  match_date,
  COUNT(*) AS balls_faced,
  SUM(runs_batter) AS runs,
  SUM(CASE WHEN player_out = batter THEN 1 ELSE 0 END) AS dismissals,
  ROUND(SUM(runs_batter)::DOUBLE * 100.0 / NULLIF(COUNT(*), 0), 2) AS strike_rate,
  SUM(CASE WHEN runs_batter = 4 THEN 1 ELSE 0 END) AS fours,
  SUM(CASE WHEN runs_batter = 6 THEN 1 ELSE 0 END) AS sixes
FROM matchprism.stg_deliveries
WHERE match_date BETWEEN @start_date AND @end_date
  AND batter IS NOT NULL
GROUP BY batter, match_date
