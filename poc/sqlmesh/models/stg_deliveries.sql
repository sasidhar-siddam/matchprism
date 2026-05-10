MODEL (
  name matchprism.stg_deliveries,
  kind FULL,
  description 'One row per delivery (ball). Explodes innings -> overs -> deliveries from the raw JSON payload.',
  audits (
    not_null(columns := (match_id, innings_num, over_num, ball_num, batter, bowler))
  )
);

WITH innings AS (
  SELECT
    match_id,
    match_date,
    season,
    venue,
    CAST(je.key AS INTEGER) + 1 AS innings_num,
    je.value AS innings_obj
  FROM matchprism.raw_matches m,
       json_each(CAST(m.innings_json AS JSON)) je
),
overs AS (
  SELECT
    match_id,
    match_date,
    season,
    venue,
    innings_num,
    json_extract_string(innings_obj, '$.team') AS batting_team,
    CAST(json_extract(over_je.value, '$.over') AS INTEGER) AS over_num,
    over_je.value AS over_obj
  FROM innings,
       json_each(json_extract(innings_obj, '$.overs')) over_je
),
deliveries AS (
  SELECT
    match_id,
    match_date,
    season,
    venue,
    innings_num,
    batting_team,
    over_num,
    CAST(d_je.key AS INTEGER) AS ball_num,
    d_je.value AS d_obj
  FROM overs,
       json_each(json_extract(over_obj, '$.deliveries')) d_je
)
SELECT
  match_id,
  match_date,
  season,
  venue,
  innings_num,
  batting_team,
  over_num,
  ball_num,
  json_extract_string(d_obj, '$.batter') AS batter,
  json_extract_string(d_obj, '$.bowler') AS bowler,
  json_extract_string(d_obj, '$.non_striker') AS non_striker,
  CAST(json_extract(d_obj, '$.runs.batter') AS INTEGER) AS runs_batter,
  CAST(json_extract(d_obj, '$.runs.extras') AS INTEGER) AS runs_extras,
  CAST(json_extract(d_obj, '$.runs.total') AS INTEGER) AS runs_total,
  json_extract_string(d_obj, '$.wickets[0].player_out') AS player_out,
  json_extract_string(d_obj, '$.wickets[0].kind') AS wicket_kind
FROM deliveries
