MODEL (
  name matchprism.stg_matches,
  kind FULL,
  description 'One row per match with clean column names. Drops the raw JSON payload.',
  audits (
    not_null(columns := (match_id, match_date, venue)),
    unique_values(columns := (match_id))
  )
);

SELECT
  match_id,
  match_date,
  season,
  venue,
  city,
  team_home,
  team_away,
  winner,
  win_margin_runs,
  CASE WHEN winner = team_home THEN team_away ELSE team_home END AS loser
FROM matchprism.raw_matches
