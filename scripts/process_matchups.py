"""
Process ball-by-ball data to compute player-vs-player and player-vs-team matchups.

For every batter-bowler pair that has faced each other:
  - Runs scored, balls faced, dismissals, strike rate, boundaries

For every batter-vs-team:
  - Innings, runs, average, SR, dismissals

For every bowler-vs-team:
  - Innings, overs, wickets, runs conceded, economy, average
"""

import json
import os
from collections import defaultdict

from venue_map import normalize_venue

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

# Team name normalization (same as h2h)
TEAM_NORMALIZE = {
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Delhi Daredevils": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
    "Rising Pune Supergiant": "Rising Pune Supergiant",
    "Rising Pune Supergiants": "Rising Pune Supergiant",
}


def normalize_team(name):
    return TEAM_NORMALIZE.get(name, name)


def process_all():
    # batter_vs_bowler[batter][bowler] = {runs, balls, dismissals, fours, sixes, dots}
    bvb = defaultdict(lambda: defaultdict(lambda: {
        "runs": 0, "balls": 0, "dismissals": 0,
        "fours": 0, "sixes": 0, "dots": 0,
        "matches": set(), "last_date": "",
    }))

    # batter_vs_team[batter][team] = {innings, runs, balls, dismissals, fours, sixes, matches}
    bvt = defaultdict(lambda: defaultdict(lambda: {
        "innings": 0, "runs": 0, "balls": 0, "dismissals": 0,
        "fours": 0, "sixes": 0, "matches": 0, "last_date": "",
        "scores": [],  # list of (date, runs, balls, not_out)
    }))

    # bowler_vs_team[bowler][team] = {innings, balls, runs, wickets, matches}
    bovt = defaultdict(lambda: defaultdict(lambda: {
        "innings": 0, "balls": 0, "runs_conceded": 0, "wickets": 0,
        "matches": 0, "last_date": "", "fours_conceded": 0, "sixes_conceded": 0,
        "figures": [],  # list of (date, wickets, runs, overs)
    }))

    processed = 0
    for league in os.listdir(RAW_DIR):
        league_dir = os.path.join(RAW_DIR, league)
        if not os.path.isdir(league_dir):
            continue
        for fname in os.listdir(league_dir):
            if not fname.endswith(".json"):
                continue
            with open(os.path.join(league_dir, fname)) as f:
                match = json.load(f)

            info = match.get("info", {})
            teams = info.get("teams", [])
            dates = info.get("dates", [])
            if not dates or len(teams) != 2:
                continue
            date = dates[0]
            match_id = fname

            # Track per-innings batter/bowler stats for per-match aggregation
            for inn_idx, innings in enumerate(match.get("innings", [])):
                if inn_idx >= 2:
                    break  # skip super overs

                batting_team = normalize_team(innings.get("team", ""))
                bowling_team = normalize_team(
                    teams[1] if batting_team == normalize_team(teams[0]) else teams[0]
                )

                # Track per-innings totals for batter_vs_team and bowler_vs_team
                batter_innings = defaultdict(lambda: {
                    "runs": 0, "balls": 0, "out": False, "fours": 0, "sixes": 0
                })
                bowler_innings = defaultdict(lambda: {
                    "balls": 0, "runs": 0, "wickets": 0, "fours": 0, "sixes": 0
                })

                for over in innings.get("overs", []):
                    for delivery in over.get("deliveries", []):
                        batter = delivery.get("batter", "")
                        bowler = delivery.get("bowler", "")
                        bat_runs = delivery["runs"]["batter"]
                        total_runs = delivery["runs"]["total"]
                        extras = delivery.get("extras", {})
                        is_wide = "wides" in extras
                        is_noball = "noballs" in extras
                        byes = extras.get("byes", 0) + extras.get("legbyes", 0)

                        # Batter vs Bowler (exclude wides — batter didn't face)
                        if not is_wide:
                            rec = bvb[batter][bowler]
                            rec["runs"] += bat_runs
                            rec["balls"] += 1
                            rec["matches"].add(match_id)
                            if bat_runs == 0:
                                rec["dots"] += 1
                            if bat_runs == 4:
                                rec["fours"] += 1
                            if bat_runs == 6:
                                rec["sixes"] += 1
                            if date > rec["last_date"]:
                                rec["last_date"] = date

                        # Batter per-innings tracking
                        if not is_wide:
                            bi = batter_innings[batter]
                            bi["runs"] += bat_runs
                            bi["balls"] += 1
                            if bat_runs == 4:
                                bi["fours"] += 1
                            if bat_runs == 6:
                                bi["sixes"] += 1

                        # Bowler per-innings tracking
                        bowler_runs = total_runs - byes
                        if not is_wide and not is_noball:
                            bowler_innings[bowler]["balls"] += 1
                        elif is_noball:
                            pass  # no-ball doesn't count as legal delivery
                        bowler_innings[bowler]["runs"] += bowler_runs
                        if bat_runs == 4:
                            bowler_innings[bowler]["fours"] += 1
                        if bat_runs == 6:
                            bowler_innings[bowler]["sixes"] += 1

                        # Wickets
                        for wicket in delivery.get("wickets", []):
                            kind = wicket.get("kind", "")
                            player_out = wicket.get("player_out", "")

                            # Batter dismissal (bvb)
                            if not is_wide and kind != "run out" and kind != "retired hurt":
                                bvb[player_out][bowler]["dismissals"] += 1

                            # Batter innings tracking
                            if player_out in batter_innings:
                                batter_innings[player_out]["out"] = True

                            # Bowler wicket (exclude run outs)
                            if kind not in ("run out", "retired hurt", "retired out", "obstructing the field"):
                                bowler_innings[bowler]["wickets"] += 1

                # Aggregate batter_vs_team
                for batter, bi in batter_innings.items():
                    if bi["balls"] == 0:
                        continue
                    rec = bvt[batter][bowling_team]
                    rec["innings"] += 1
                    rec["runs"] += bi["runs"]
                    rec["balls"] += bi["balls"]
                    rec["fours"] += bi["fours"]
                    rec["sixes"] += bi["sixes"]
                    rec["matches"] += 1
                    if bi["out"]:
                        rec["dismissals"] += 1
                    if date > rec["last_date"]:
                        rec["last_date"] = date
                    rec["scores"].append((date, bi["runs"], bi["balls"], not bi["out"]))

                # Aggregate bowler_vs_team
                for bowler, bo in bowler_innings.items():
                    if bo["balls"] == 0 and bo["runs"] == 0:
                        continue
                    rec = bovt[bowler][batting_team]
                    rec["innings"] += 1
                    rec["balls"] += bo["balls"]
                    rec["runs_conceded"] += bo["runs"]
                    rec["wickets"] += bo["wickets"]
                    rec["matches"] += 1
                    rec["fours_conceded"] += bo["fours"]
                    rec["sixes_conceded"] += bo["sixes"]
                    if date > rec["last_date"]:
                        rec["last_date"] = date
                    overs = f"{bo['balls']//6}.{bo['balls']%6}"
                    rec["figures"].append((date, bo["wickets"], bo["runs"], overs))

            processed += 1
            if processed % 1000 == 0:
                print(f"  Processed {processed} matches...")

    print(f"  Processed {processed} total matches")
    return bvb, bvt, bovt


def build_output(bvb, bvt, bovt):
    """Build JSON-serializable output."""

    # Batter vs Bowler — only keep matchups with 6+ balls
    matchups = {}
    for batter, bowlers in bvb.items():
        for bowler, stats in bowlers.items():
            if stats["balls"] < 6:
                continue
            key = f"{batter} vs {bowler}"
            sr = round(stats["runs"] / stats["balls"] * 100, 1) if stats["balls"] else 0
            avg = round(stats["runs"] / stats["dismissals"], 1) if stats["dismissals"] else stats["runs"]
            dot_pct = round(stats["dots"] / stats["balls"] * 100, 1) if stats["balls"] else 0
            matchups[key] = {
                "batter": batter,
                "bowler": bowler,
                "balls": stats["balls"],
                "runs": stats["runs"],
                "dismissals": stats["dismissals"],
                "average": avg,
                "strikeRate": sr,
                "fours": stats["fours"],
                "sixes": stats["sixes"],
                "dotBallPct": dot_pct,
                "matches": len(stats["matches"]),
                "lastPlayed": stats["last_date"],
            }

    # Batter vs Team — only keep 3+ innings
    batter_vs_team = {}
    for batter, teams in bvt.items():
        player_teams = {}
        for team, stats in teams.items():
            if stats["innings"] < 3:
                continue
            avg = round(stats["runs"] / stats["dismissals"], 1) if stats["dismissals"] else stats["runs"]
            sr = round(stats["runs"] / stats["balls"] * 100, 1) if stats["balls"] else 0
            # Last 5 scores
            scores_sorted = sorted(stats["scores"], reverse=True)[:5]
            last5 = []
            for d, r, b, no in scores_sorted:
                last5.append(f"{r}{'*' if no else ''}")

            player_teams[team] = {
                "innings": stats["innings"],
                "runs": stats["runs"],
                "average": avg,
                "strikeRate": sr,
                "dismissals": stats["dismissals"],
                "fours": stats["fours"],
                "sixes": stats["sixes"],
                "last5": last5,
                "lastPlayed": stats["last_date"],
            }
        if player_teams:
            batter_vs_team[batter] = player_teams

    # Bowler vs Team — only keep 3+ innings
    bowler_vs_team = {}
    for bowler, teams in bovt.items():
        player_teams = {}
        for team, stats in teams.items():
            if stats["innings"] < 3:
                continue
            overs = stats["balls"] / 6
            econ = round(stats["runs_conceded"] / overs, 2) if overs else 0
            avg = round(stats["runs_conceded"] / stats["wickets"], 1) if stats["wickets"] else 0
            sr = round(stats["balls"] / stats["wickets"], 1) if stats["wickets"] else 0
            # Last 5 figures
            figs_sorted = sorted(stats["figures"], reverse=True)[:5]
            last5 = [f"{w}/{r}" for d, w, r, o in figs_sorted]

            player_teams[team] = {
                "innings": stats["innings"],
                "overs": round(overs, 1),
                "wickets": stats["wickets"],
                "runsConceded": stats["runs_conceded"],
                "economy": econ,
                "average": avg,
                "strikeRate": sr,
                "foursConceded": stats["fours_conceded"],
                "sixesConceded": stats["sixes_conceded"],
                "last5": last5,
                "lastPlayed": stats["last_date"],
            }
        if player_teams:
            bowler_vs_team[bowler] = player_teams

    return matchups, batter_vs_team, bowler_vs_team


def main():
    print("=" * 60)
    print("MatchPrism - Matchup Intelligence Processor")
    print("=" * 60)

    bvb, bvt, bovt = process_all()
    matchups, bat_vs_team, bowl_vs_team = build_output(bvb, bvt, bovt)

    os.makedirs(PROCESSED_DIR, exist_ok=True)

    with open(os.path.join(PROCESSED_DIR, "matchups.json"), "w") as f:
        json.dump(matchups, f)
    with open(os.path.join(PROCESSED_DIR, "batter_vs_team.json"), "w") as f:
        json.dump(bat_vs_team, f)
    with open(os.path.join(PROCESSED_DIR, "bowler_vs_team.json"), "w") as f:
        json.dump(bowl_vs_team, f)

    print(f"\nResults:")
    print(f"  Batter vs Bowler matchups (6+ balls): {len(matchups):,}")
    print(f"  Batters with team matchups: {len(bat_vs_team):,}")
    print(f"  Bowlers with team matchups: {len(bowl_vs_team):,}")

    # Sample matchups
    print(f"\n{'='*60}")
    print("SAMPLE MATCHUPS")
    print(f"{'='*60}")

    # Kohli vs top bowlers
    kohli_matchups = [(k, v) for k, v in matchups.items() if k.startswith("V Kohli vs")]
    kohli_matchups.sort(key=lambda x: x[1]["balls"], reverse=True)
    print("\nV Kohli vs Top Bowlers:")
    for key, m in kohli_matchups[:10]:
        bowler = m["bowler"]
        print(f"  vs {bowler:25s}  {m['balls']:3d} balls  {m['runs']:3d} runs  SR {m['strikeRate']:5.1f}  dismissed {m['dismissals']}x  avg {m['average']}")

    # Kohli vs teams
    if "V Kohli" in bat_vs_team:
        print("\nV Kohli vs Teams:")
        for team, s in sorted(bat_vs_team["V Kohli"].items(), key=lambda x: x[1]["innings"], reverse=True)[:8]:
            print(f"  vs {team:35s}  {s['innings']:2d} inn  {s['runs']:4d} runs  avg {s['average']:5.1f}  SR {s['strikeRate']:5.1f}  last5: {s['last5']}")

    # Bumrah vs teams
    if "JJ Bumrah" in bowl_vs_team:
        print("\nJJ Bumrah vs Teams:")
        for team, s in sorted(bowl_vs_team["JJ Bumrah"].items(), key=lambda x: x[1]["innings"], reverse=True)[:8]:
            print(f"  vs {team:35s}  {s['innings']:2d} inn  {s['wickets']:2d} wkts  econ {s['economy']:4.1f}  last5: {s['last5']}")

    # Top dominance matchups (min 30 balls)
    print(f"\nMost Dominant Batter Matchups (30+ balls, highest SR):")
    big_matchups = [(k, v) for k, v in matchups.items() if v["balls"] >= 30]
    big_matchups.sort(key=lambda x: x[1]["strikeRate"], reverse=True)
    for key, m in big_matchups[:5]:
        print(f"  {m['batter']:20s} vs {m['bowler']:20s}  {m['balls']} balls  {m['runs']} runs  SR {m['strikeRate']}  ({m['dismissals']} dismissals)")

    print(f"\nMost Dominant Bowler Matchups (30+ balls, most dismissals):")
    big_matchups.sort(key=lambda x: x[1]["dismissals"], reverse=True)
    for key, m in big_matchups[:5]:
        print(f"  {m['bowler']:20s} vs {m['batter']:20s}  {m['balls']} balls  {m['dismissals']} dismissals  avg {m['average']}  dot% {m['dotBallPct']}%")


if __name__ == "__main__":
    main()
