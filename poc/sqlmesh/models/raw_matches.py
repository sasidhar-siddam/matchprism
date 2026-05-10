"""Raw matches: read Cricsheet-shaped JSON and produce one row per match.

This is the only Python model in the project. Everything downstream is SQL.
In production this layer would be replaced by an ingestion tool (Airbyte,
Fivetran, custom Python) that lands data in Snowflake; SQLMesh would start at
the staging layer.
"""
import json
from pathlib import Path
from datetime import datetime
import typing as t

import pandas as pd
from sqlmesh import ExecutionContext, model
from sqlmesh.core.model import ModelKindName


@model(
    "matchprism.raw_matches",
    kind=ModelKindName.FULL.value,
    columns={
        "match_id": "VARCHAR",
        "match_date": "DATE",
        "season": "VARCHAR",
        "venue": "VARCHAR",
        "city": "VARCHAR",
        "team_home": "VARCHAR",
        "team_away": "VARCHAR",
        "winner": "VARCHAR",
        "win_margin_runs": "INTEGER",
        "innings_json": "VARCHAR",
    },
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> pd.DataFrame:
    raw_dir = Path(__file__).resolve().parent.parent / "raw" / "ipl"
    rows = []
    for path in sorted(raw_dir.glob("*.json")):
        data = json.loads(path.read_text())
        info = data["info"]
        outcome = info.get("outcome", {})
        rows.append(
            {
                "match_id": path.stem,
                "match_date": info["dates"][0],
                "season": str(info.get("season", "")),
                "venue": info.get("venue", ""),
                "city": info.get("city", ""),
                "team_home": info["teams"][0],
                "team_away": info["teams"][1],
                "winner": outcome.get("winner"),
                "win_margin_runs": outcome.get("by", {}).get("runs"),
                "innings_json": json.dumps(data["innings"]),
            }
        )
    return pd.DataFrame(rows)
