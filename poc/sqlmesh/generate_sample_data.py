"""Generate synthetic Cricsheet-shaped IPL matches for the SQLMesh PoC.

Real Cricsheet files have an `info` block (teams, venue, dates, season, outcome)
and an `innings` block with `overs` -> `deliveries`. We mimic that shape with
deterministic randomness so the PoC has reproducible inputs.

Writes one JSON file per match into raw/<league>/<match_id>.json.
"""
import json
import random
from pathlib import Path

random.seed(42)

OUT = Path(__file__).parent / "raw" / "ipl"
OUT.mkdir(parents=True, exist_ok=True)

VENUES = [
    ("M Chinnaswamy Stadium", "Bengaluru"),
    ("Wankhede Stadium", "Mumbai"),
    ("Eden Gardens", "Kolkata"),
    ("MA Chidambaram Stadium", "Chennai"),
    ("Narendra Modi Stadium", "Ahmedabad"),
]

TEAMS = {
    "Royal Challengers Bengaluru": ["V Kohli", "F du Plessis", "G Maxwell", "D Padikkal", "M Siraj", "Y Chahal"],
    "Mumbai Indians": ["R Sharma", "I Kishan", "S Yadav", "H Pandya", "J Bumrah", "T Boult"],
    "Kolkata Knight Riders": ["S Iyer", "N Rana", "A Russell", "S Narine", "V Chakaravarthy", "U Yadav"],
    "Chennai Super Kings": ["MS Dhoni", "R Gaikwad", "D Conway", "R Jadeja", "DJ Bravo", "D Chahar"],
    "Gujarat Titans": ["S Gill", "H Pandya", "DA Miller", "R Tewatia", "Rashid Khan", "M Shami"],
}

TEAM_LIST = list(TEAMS.keys())
WICKET_KINDS = ["bowled", "caught", "lbw", "caught and bowled", "stumped", "run out"]


def make_innings(batting_team: str, bowling_team: str, target: int | None = None) -> dict:
    """Generate a single innings of ~20 overs with semi-realistic outcomes."""
    batters = TEAMS[batting_team][:6]
    bowlers = TEAMS[bowling_team][3:]
    overs = []
    total_runs = 0
    wickets = 0
    striker_idx = 0
    non_striker_idx = 1
    next_batter_idx = 2

    for over_num in range(20):
        deliveries = []
        bowler = random.choice(bowlers)
        for ball_num in range(6):
            if wickets >= 10:
                break
            striker = batters[striker_idx]
            non_striker = batters[non_striker_idx]
            # Skewed run distribution: lots of 0/1, fewer 4/6
            runs_batter = random.choices(
                [0, 1, 2, 3, 4, 6],
                weights=[35, 30, 8, 1, 18, 8],
            )[0]
            extras = 0
            extras_kind = None
            if random.random() < 0.04:
                extras = 1
                extras_kind = random.choice(["wides", "noballs", "byes"])

            delivery = {
                "batter": striker,
                "bowler": bowler,
                "non_striker": non_striker,
                "runs": {"batter": runs_batter, "extras": extras, "total": runs_batter + extras},
            }
            if extras_kind:
                delivery["extras"] = {extras_kind: extras}

            # Wicket probability ~3.5%
            if random.random() < 0.035:
                kind = random.choice(WICKET_KINDS)
                delivery["wickets"] = [{"player_out": striker, "kind": kind}]
                wickets += 1
                if next_batter_idx < len(batters):
                    striker_idx = next_batter_idx
                    next_batter_idx += 1

            total_runs += runs_batter + extras
            deliveries.append(delivery)
            # Rotate strike on odd runs
            if runs_batter % 2 == 1:
                striker_idx, non_striker_idx = non_striker_idx, striker_idx

            if target is not None and total_runs >= target:
                break
        overs.append({"over": over_num, "deliveries": deliveries})
        if wickets >= 10 or (target is not None and total_runs >= target):
            break
        striker_idx, non_striker_idx = non_striker_idx, striker_idx

    return {"team": batting_team, "overs": overs}


def make_match(match_id: str, date: str, season: str, venue: tuple[str, str], teams: list[str]) -> dict:
    first_innings = make_innings(teams[0], teams[1])
    first_total = sum(
        d["runs"]["total"]
        for over in first_innings["overs"]
        for d in over["deliveries"]
    )
    second_innings = make_innings(teams[1], teams[0], target=first_total + 1)
    second_total = sum(
        d["runs"]["total"]
        for over in second_innings["overs"]
        for d in over["deliveries"]
    )

    winner = teams[1] if second_total > first_total else teams[0]
    return {
        "meta": {"data_version": "1.0.0", "created": date, "revision": 1},
        "info": {
            "match_type": "T20",
            "balls_per_over": 6,
            "overs": 20,
            "season": season,
            "dates": [date],
            "venue": venue[0],
            "city": venue[1],
            "teams": teams,
            "toss": {"winner": teams[0], "decision": "bat"},
            "outcome": {"winner": winner, "by": {"runs": abs(first_total - second_total)}},
        },
        "innings": [first_innings, second_innings],
    }


MATCHES = [
    ("ipl_2024_01", "2024-03-22", "2024", VENUES[0], ["Royal Challengers Bengaluru", "Chennai Super Kings"]),
    ("ipl_2024_02", "2024-03-24", "2024", VENUES[1], ["Mumbai Indians", "Kolkata Knight Riders"]),
    ("ipl_2024_03", "2024-04-01", "2024", VENUES[2], ["Kolkata Knight Riders", "Gujarat Titans"]),
    ("ipl_2024_04", "2024-04-10", "2024", VENUES[3], ["Chennai Super Kings", "Mumbai Indians"]),
    ("ipl_2024_05", "2024-04-15", "2024", VENUES[4], ["Gujarat Titans", "Royal Challengers Bengaluru"]),
    ("ipl_2025_01", "2025-03-28", "2025", VENUES[0], ["Royal Challengers Bengaluru", "Mumbai Indians"]),
    ("ipl_2025_02", "2025-04-05", "2025", VENUES[2], ["Kolkata Knight Riders", "Chennai Super Kings"]),
    ("ipl_2025_03", "2025-04-12", "2025", VENUES[4], ["Gujarat Titans", "Kolkata Knight Riders"]),
]

for match_id, date, season, venue, teams in MATCHES:
    match = make_match(match_id, date, season, venue, teams)
    out_path = OUT / f"{match_id}.json"
    out_path.write_text(json.dumps(match, indent=2))

print(f"Wrote {len(MATCHES)} matches to {OUT}")
