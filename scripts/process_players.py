"""Process Cricsheet T20 JSON match files into per-player stats with venue breakdowns.

Reads all match files from data/raw/<league>/ subdirectories (IPL, BBL, CPL, PSL,
LPL, SA20, The Hundred, BPL, MLC, T20I, ILT20, NPL) and outputs
data/processed/players.json with batting, bowling, venue-fit grades, and recent
form for every player aggregated across all leagues.
"""

import glob
import json
import os
from collections import defaultdict

from venue_map import normalize_venue

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
OUT_FILE = os.path.join(OUT_DIR, "players.json")

# Wicket kinds that count as a bowler's wicket
BOWLER_WICKETS = {
    "bowled", "caught", "caught and bowled", "hit wicket",
    "lbw", "stumped", "obstructing the field",
}

# Wicket kinds that count as a batter dismissal (everything except retired hurt)
BATTER_DISMISSALS = {
    "bowled", "caught", "caught and bowled", "hit wicket",
    "lbw", "run out", "stumped", "obstructing the field", "retired out",
}


def parse_season(season_val):
    """Normalize season to a sortable string like '2017'."""
    s = str(season_val)
    # "2007/08" -> "2007", "2020/21" -> "2020"
    if "/" in s:
        return s.split("/")[0]
    return s


def format_overs(balls):
    """Format ball count as overs string, e.g. 30 balls -> '5.0'."""
    full = balls // 6
    remainder = balls % 6
    return f"{full}.{remainder}"


def discover_league_files():
    """Find all match JSON files organized by league subdirectory.

    Returns a list of (league_id, filepath) tuples sorted by league then filename.
    League ID is the subdirectory name (e.g., 'ipl', 'bbl', 't20i').
    """
    all_files = []
    if not os.path.isdir(RAW_DIR):
        return all_files
    for entry in sorted(os.listdir(RAW_DIR)):
        league_dir = os.path.join(RAW_DIR, entry)
        if not os.path.isdir(league_dir):
            continue
        league_id = entry.lower()
        league_files = sorted(glob.glob(os.path.join(league_dir, "*.json")))
        for fp in league_files:
            all_files.append((league_id, fp))
    return all_files


def process_all():
    league_files = discover_league_files()
    if not league_files:
        print("No match files found in league subdirectories under", RAW_DIR)
        return

    # Count per league for reporting
    league_counts = defaultdict(int)
    for league_id, _ in league_files:
        league_counts[league_id] += 1

    total_files = len(league_files)
    print(f"Processing {total_files} match files across {len(league_counts)} leagues ...")
    for lid in sorted(league_counts):
        print(f"  {lid}: {league_counts[lid]} files")

    # ---- Per-match data collection structures ----
    # player_teams: player -> set of team names
    player_teams = defaultdict(set)
    # player_leagues: player -> set of league IDs
    player_leagues = defaultdict(set)

    # match_meta: list of (date_str, season_str, venue, filename) for sorting
    match_meta = []

    # For each player, per (venue OR "__overall__"), per innings (match_idx, innings_idx):
    #   batting: {runs, balls, fours, sixes, dismissed}
    #   bowling: {runs, balls, wickets, extras_conceded_byes_lb}
    #
    # We store per-innings aggregates then roll up.

    # batting_innings[player][venue] = list of {runs, balls, fours, sixes, dismissed, match_idx}
    batting_innings = defaultdict(lambda: defaultdict(list))
    # bowling_innings[player][venue] = list of {runs, balls, wickets, match_idx}
    bowling_innings = defaultdict(lambda: defaultdict(list))

    # For last5 and recentSeason, we need per-match performance keyed by (date, match_idx)
    # match_batting[player] = list of (date_str, match_idx, venue, league_id, opposition, {runs, balls, dismissed, ...})
    match_batting = defaultdict(list)
    match_bowling = defaultdict(list)

    # player_team_per_match[player][match_idx] = team_name
    player_team_per_match = defaultdict(dict)

    for file_idx, (league_id, filepath) in enumerate(league_files):
        with open(filepath) as f:
            match = json.load(f)

        info = match.get("info", {})
        venue = normalize_venue(info.get("venue", "Unknown"))
        season = parse_season(info.get("season", ""))
        dates = info.get("dates", [])
        date_str = dates[0] if dates else "1900-01-01"
        teams = info.get("teams", [])
        players_by_team = info.get("players", {})

        match_meta.append((date_str, season, venue, os.path.basename(filepath), league_id))

        # Register teams and leagues for each player, and map player->team for this match
        for team, roster in players_by_team.items():
            for p in roster:
                player_teams[p].add(team)
                player_leagues[p].add(league_id)
                player_team_per_match[p][file_idx] = team

        # Process each innings
        for innings_obj in match.get("innings", []):
            batting_team = innings_obj.get("team", "")
            overs = innings_obj.get("overs", [])

            # Track per-batter stats for this innings
            inn_bat = defaultdict(lambda: {
                "runs": 0, "balls": 0, "fours": 0, "sixes": 0, "dismissed": False
            })
            # Track per-bowler stats for this innings
            inn_bowl = defaultdict(lambda: {
                "runs": 0, "balls": 0, "wickets": 0
            })
            # Track which batters appeared
            batters_seen = set()
            bowlers_seen = set()

            for over_obj in overs:
                for delivery in over_obj.get("deliveries", []):
                    batter = delivery["batter"]
                    bowler = delivery["bowler"]
                    runs_obj = delivery["runs"]
                    extras = delivery.get("extras", {})

                    batters_seen.add(batter)
                    bowlers_seen.add(bowler)

                    batter_runs = runs_obj.get("batter", 0)
                    total_runs = runs_obj.get("total", 0)
                    extras_runs = runs_obj.get("extras", 0)

                    is_wide = "wides" in extras
                    is_noball = "noballs" in extras
                    byes = extras.get("byes", 0)
                    legbyes = extras.get("legbyes", 0)

                    # Batting: count ball faced if not a wide
                    if not is_wide:
                        inn_bat[batter]["balls"] += 1

                    inn_bat[batter]["runs"] += batter_runs
                    if batter_runs == 4:
                        inn_bat[batter]["fours"] += 1
                    if batter_runs == 6:
                        inn_bat[batter]["sixes"] += 1

                    # Bowling: count ball if not a wide and not a noball
                    if not is_wide and not is_noball:
                        inn_bowl[bowler]["balls"] += 1
                    elif is_noball:
                        # No-balls don't count as legal deliveries
                        pass

                    # Bowling runs conceded: total minus byes and legbyes
                    # (byes/legbyes are extras not charged to bowler)
                    bowl_runs = total_runs - byes - legbyes
                    inn_bowl[bowler]["runs"] += bowl_runs

                    # Wickets
                    for w in delivery.get("wickets", []):
                        kind = w.get("kind", "")
                        player_out = w.get("player_out", "")

                        if kind in BATTER_DISMISSALS:
                            inn_bat[player_out]["dismissed"] = True

                        if kind in BOWLER_WICKETS:
                            inn_bowl[bowler]["wickets"] += 1

            # Store innings-level stats
            for batter in batters_seen:
                stats = inn_bat[batter]
                # Determine opposition: the other team in the match
                batter_team = player_team_per_match.get(batter, {}).get(file_idx, "")
                opposition = ""
                for t in teams:
                    if t != batter_team:
                        opposition = t
                        break
                record = {
                    "runs": stats["runs"],
                    "balls": stats["balls"],
                    "fours": stats["fours"],
                    "sixes": stats["sixes"],
                    "dismissed": stats["dismissed"],
                    "match_idx": file_idx,
                }
                batting_innings[batter][venue].append(record)
                batting_innings[batter]["__overall__"].append(record)
                match_batting[batter].append((date_str, file_idx, venue, league_id, opposition, record))

            for bowler in bowlers_seen:
                stats = inn_bowl[bowler]
                bowler_team = player_team_per_match.get(bowler, {}).get(file_idx, "")
                opposition = ""
                for t in teams:
                    if t != bowler_team:
                        opposition = t
                        break
                record = {
                    "runs": stats["runs"],
                    "balls": stats["balls"],
                    "wickets": stats["wickets"],
                    "match_idx": file_idx,
                }
                bowling_innings[bowler][venue].append(record)
                bowling_innings[bowler]["__overall__"].append(record)
                match_bowling[bowler].append((date_str, file_idx, venue, league_id, opposition, record))

    # ---- Aggregate stats ----
    print("Aggregating player stats ...")

    # Find the most recent season
    all_seasons = sorted(set(m[1] for m in match_meta))
    recent_season = all_seasons[-1] if all_seasons else ""

    # Build match_idx -> (date, season, league) mapping
    match_season = {}
    match_date = {}
    match_league = {}
    for idx, (date_str, season, venue, fname, league_id) in enumerate(match_meta):
        match_season[idx] = season
        match_date[idx] = date_str
        match_league[idx] = league_id

    def aggregate_batting(innings_list):
        """Aggregate batting stats from a list of per-innings records."""
        if not innings_list:
            return None
        total_runs = sum(i["runs"] for i in innings_list)
        total_balls = sum(i["balls"] for i in innings_list)
        total_fours = sum(i["fours"] for i in innings_list)
        total_sixes = sum(i["sixes"] for i in innings_list)
        dismissals = sum(1 for i in innings_list if i["dismissed"])
        not_outs = sum(1 for i in innings_list if not i["dismissed"])
        num_innings = len(innings_list)

        # Highest score
        best_runs = -1
        best_not_out = False
        for i in innings_list:
            if i["runs"] > best_runs or (i["runs"] == best_runs and not i["dismissed"]):
                best_runs = i["runs"]
                best_not_out = not i["dismissed"]
        highest = f"{best_runs}*" if best_not_out else str(best_runs)

        fifties = sum(1 for i in innings_list if 50 <= i["runs"] < 100)
        hundreds = sum(1 for i in innings_list if i["runs"] >= 100)

        avg = total_runs / dismissals if dismissals > 0 else float(total_runs)
        sr = (total_runs / total_balls * 100) if total_balls > 0 else 0.0

        return {
            "innings": num_innings,
            "runs": total_runs,
            "ballsFaced": total_balls,
            "average": round(avg, 2),
            "strikeRate": round(sr, 2),
            "fifties": fifties,
            "hundreds": hundreds,
            "highestScore": highest,
            "fours": total_fours,
            "sixes": total_sixes,
            "notOuts": not_outs,
        }

    def aggregate_bowling(innings_list):
        """Aggregate bowling stats from a list of per-innings records."""
        if not innings_list:
            return None
        total_runs = sum(i["runs"] for i in innings_list)
        total_balls = sum(i["balls"] for i in innings_list)
        total_wickets = sum(i["wickets"] for i in innings_list)
        num_innings = len(innings_list)

        overs_str = format_overs(total_balls)
        overs_decimal = total_balls / 6.0 if total_balls > 0 else 0.0
        economy = total_runs / overs_decimal if overs_decimal > 0 else 0.0
        avg = total_runs / total_wickets if total_wickets > 0 else 0.0
        sr = total_balls / total_wickets if total_wickets > 0 else 0.0

        # Best figures: best wickets/runs in a single innings
        best_w, best_r = 0, 999999
        for i in innings_list:
            w, r = i["wickets"], i["runs"]
            if w > best_w or (w == best_w and r < best_r):
                best_w = w
                best_r = r
        best_figures = f"{best_w}/{best_r}"

        return {
            "innings": num_innings,
            "overs": overs_str,
            "runs": total_runs,
            "wickets": total_wickets,
            "economy": round(economy, 2),
            "average": round(avg, 2) if total_wickets > 0 else 0,
            "strikeRate": round(sr, 2) if total_wickets > 0 else 0,
            "bestFigures": best_figures,
        }

    def compute_grade_batting(venue_avg, overall_avg):
        """Venue fit grade based on batting average."""
        if overall_avg == 0:
            return "N/A"
        ratio = venue_avg / overall_avg
        if ratio > 1.30:
            return "A+"
        elif ratio > 1.15:
            return "A"
        elif ratio >= 0.85:
            return "B"
        elif ratio >= 0.60:
            return "C"
        else:
            return "D"

    def compute_grade_bowling(venue_econ, overall_econ):
        """Venue fit grade based on bowling economy (inverted - lower is better)."""
        if overall_econ == 0:
            return "N/A"
        ratio = venue_econ / overall_econ
        if ratio < 0.70:
            return "A+"
        elif ratio < 0.85:
            return "A"
        elif ratio <= 1.15:
            return "B"
        elif ratio <= 1.30:
            return "C"
        else:
            return "D"

    all_players = set(batting_innings.keys()) | set(bowling_innings.keys())
    print(f"Found {len(all_players)} unique players")

    result = {}

    for player in sorted(all_players):
        entry = {
            "name": player,
            "teams": sorted(player_teams.get(player, set())),
            "leagues": sorted(player_leagues.get(player, set())),
        }

        # Overall stats
        overall_bat = aggregate_batting(batting_innings[player].get("__overall__", []))
        overall_bowl = aggregate_bowling(bowling_innings[player].get("__overall__", []))

        overall = {}
        if overall_bat:
            overall["batting"] = overall_bat
        if overall_bowl:
            overall["bowling"] = overall_bowl
        entry["overall"] = overall

        # Per-venue stats with grades
        venues = {}
        for venue_name in sorted(batting_innings[player].keys()):
            if venue_name == "__overall__":
                continue
            v_bat = aggregate_batting(batting_innings[player][venue_name])
            v_bowl = aggregate_bowling(bowling_innings[player].get(venue_name, []))

            venue_data = {}
            if v_bat:
                venue_data["batting"] = v_bat
            if v_bowl:
                venue_data["bowling"] = v_bowl

            # Compute grade
            grade = "N/A"
            bat_innings_count = len(batting_innings[player][venue_name])
            bowl_innings_count = len(bowling_innings[player].get(venue_name, []))

            if bat_innings_count >= 3 and overall_bat and v_bat:
                grade = compute_grade_batting(v_bat["average"], overall_bat["average"])
            elif bowl_innings_count >= 3 and overall_bowl and v_bowl:
                grade = compute_grade_bowling(v_bowl["economy"], overall_bowl["economy"])

            # If player has both batting and bowling with sufficient innings,
            # prefer batting grade unless they're clearly a bowler (more bowling innings overall)
            if (bat_innings_count >= 3 and bowl_innings_count >= 3
                    and overall_bat and overall_bowl and v_bat and v_bowl):
                overall_bat_inn = len(batting_innings[player]["__overall__"])
                overall_bowl_inn = len(bowling_innings[player]["__overall__"])
                if overall_bowl_inn > overall_bat_inn:
                    grade = compute_grade_bowling(v_bowl["economy"], overall_bowl["economy"])
                else:
                    grade = compute_grade_batting(v_bat["average"], overall_bat["average"])

            venue_data["grade"] = grade
            venues[venue_name] = venue_data

        # Also add venues where they only bowled (not batted)
        for venue_name in sorted(bowling_innings[player].keys()):
            if venue_name == "__overall__" or venue_name in venues:
                continue
            v_bowl = aggregate_bowling(bowling_innings[player][venue_name])
            venue_data = {}
            if v_bowl:
                venue_data["bowling"] = v_bowl
            bowl_innings_count = len(bowling_innings[player][venue_name])
            if bowl_innings_count >= 3 and overall_bowl and v_bowl:
                grade = compute_grade_bowling(v_bowl["economy"], overall_bowl["economy"])
            else:
                grade = "N/A"
            venue_data["grade"] = grade
            venues[venue_name] = venue_data

        entry["venues"] = venues

        # Last 5 matches: determine from most recent matches by date
        # Combine batting and bowling entries, sort by date desc, pick unique match_idx
        all_matches = []
        for date_str, midx, venue, lid, oppo, rec in match_batting.get(player, []):
            all_matches.append((date_str, midx, "bat", rec))
        for date_str, midx, venue, lid, oppo, rec in match_bowling.get(player, []):
            all_matches.append((date_str, midx, "bowl", rec))

        # Group by match_idx, sorted by date descending
        match_groups = defaultdict(lambda: {"bat": None, "bowl": None, "date": ""})
        for date_str, midx, role, rec in all_matches:
            match_groups[midx][role] = rec
            match_groups[midx]["date"] = date_str

        sorted_matches = sorted(match_groups.items(), key=lambda x: x[1]["date"], reverse=True)
        last5 = []
        for midx, info in sorted_matches[:5]:
            bat_rec = info["bat"]
            bowl_rec = info["bowl"]

            # Decide whether to show batting or bowling performance
            # Show batting score if they batted (and scored or faced balls)
            # Show bowling figures if they bowled
            perf_parts = []
            if bat_rec and bat_rec["balls"] > 0:
                score = str(bat_rec["runs"])
                if not bat_rec["dismissed"]:
                    score += "*"
                perf_parts.append(("bat", score))
            if bowl_rec and bowl_rec["balls"] > 0:
                fig = f"{bowl_rec['wickets']}/{bowl_rec['runs']}"
                perf_parts.append(("bowl", fig))

            # For last5, show the most relevant: if primarily a batter show batting,
            # if primarily a bowler show bowling, otherwise show batting
            if perf_parts:
                # Use overall innings counts to determine primary role
                overall_bat_inn = len(batting_innings[player].get("__overall__", []))
                overall_bowl_inn = len(bowling_innings[player].get("__overall__", []))
                has_bat = any(p[0] == "bat" for p in perf_parts)
                has_bowl = any(p[0] == "bowl" for p in perf_parts)

                if has_bat and has_bowl:
                    if overall_bowl_inn > overall_bat_inn * 1.5:
                        last5.append(next(p[1] for p in perf_parts if p[0] == "bowl"))
                    else:
                        last5.append(next(p[1] for p in perf_parts if p[0] == "bat"))
                elif has_bat:
                    last5.append(next(p[1] for p in perf_parts if p[0] == "bat"))
                elif has_bowl:
                    last5.append(next(p[1] for p in perf_parts if p[0] == "bowl"))
            elif bat_rec:
                # Batted but faced 0 balls (e.g., non-striker, never got on strike)
                score = str(bat_rec["runs"])
                if not bat_rec["dismissed"]:
                    score += "*"
                last5.append(score)

        entry["last5"] = last5

        # Recent season stats
        recent_bat = [
            rec for rec in batting_innings[player].get("__overall__", [])
            if match_season.get(rec["match_idx"]) == recent_season
        ]
        recent_bowl = [
            rec for rec in bowling_innings[player].get("__overall__", [])
            if match_season.get(rec["match_idx"]) == recent_season
        ]
        recent = {}
        if recent_bat:
            recent["batting"] = aggregate_batting(recent_bat)
        if recent_bowl:
            recent["bowling"] = aggregate_bowling(recent_bowl)
        if recent:
            entry["recentSeason"] = recent
            entry["recentSeasonYear"] = recent_season

        # ---- Time-series trend data ----

        # Build a unified per-match record with batting + bowling, sorted by date
        # Each entry: {date, match_idx, venue, league, opposition, bat_rec, bowl_rec}
        timeline_map = {}  # match_idx -> combined record
        for date_str, midx, venue, lid, oppo, rec in match_batting.get(player, []):
            if midx not in timeline_map:
                timeline_map[midx] = {
                    "date": date_str, "match_idx": midx, "venue": venue,
                    "league": lid, "opposition": oppo,
                    "bat": None, "bowl": None,
                }
            timeline_map[midx]["bat"] = rec
        for date_str, midx, venue, lid, oppo, rec in match_bowling.get(player, []):
            if midx not in timeline_map:
                timeline_map[midx] = {
                    "date": date_str, "match_idx": midx, "venue": venue,
                    "league": lid, "opposition": oppo,
                    "bat": None, "bowl": None,
                }
            timeline_map[midx]["bowl"] = rec

        # Sort by date descending (most recent first)
        timeline_sorted = sorted(
            timeline_map.values(),
            key=lambda x: (x["date"], x["match_idx"]),
            reverse=True,
        )

        # Determine primary role for trend calculation
        overall_bat_inn_count = len(batting_innings[player].get("__overall__", []))
        overall_bowl_inn_count = len(bowling_innings[player].get("__overall__", []))
        is_primary_bowler = overall_bowl_inn_count > overall_bat_inn_count * 1.5

        # --- 1. recentForm: rolling performance windows ---
        # For batters: use batting innings; for bowlers: use bowling innings
        if is_primary_bowler:
            # Use bowling entries that have actual bowling data
            bowl_timeline = [m for m in timeline_sorted if m["bowl"] and m["bowl"]["balls"] > 0]
            last10_entries = bowl_timeline[:10]
            last20_entries = bowl_timeline[:20]

            def compute_bowl_window(entries):
                if not entries:
                    return None
                total_runs = sum(e["bowl"]["runs"] for e in entries)
                total_balls = sum(e["bowl"]["balls"] for e in entries)
                total_wickets = sum(e["bowl"]["wickets"] for e in entries)
                overs_decimal = total_balls / 6.0 if total_balls > 0 else 0.0
                economy = total_runs / overs_decimal if overs_decimal > 0 else 0.0
                avg = total_runs / total_wickets if total_wickets > 0 else 0.0
                sr = total_balls / total_wickets if total_wickets > 0 else 0.0
                return {
                    "innings": len(entries),
                    "wickets": total_wickets,
                    "runsConceded": total_runs,
                    "overs": format_overs(total_balls),
                    "economy": round(economy, 2),
                    "average": round(avg, 2) if total_wickets > 0 else 0,
                    "strikeRate": round(sr, 2) if total_wickets > 0 else 0,
                }

            last10_stats = compute_bowl_window(last10_entries)
            last20_stats = compute_bowl_window(last20_entries)

            # Trend: compare economy (inverted - lower is better)
            trend = "consistent"
            if last10_stats and last20_stats and last20_stats["economy"] > 0:
                ratio = last10_stats["economy"] / last20_stats["economy"]
                if ratio < 0.80:
                    trend = "improving"  # lower economy = improving for bowlers
                elif ratio > 1.20:
                    trend = "declining"  # higher economy = declining for bowlers

            entry["recentForm"] = {
                "last10": last10_stats,
                "last20": last20_stats,
                "trend": trend,
            }
        else:
            # Use batting entries that have actual batting data
            bat_timeline = [m for m in timeline_sorted if m["bat"] and m["bat"]["balls"] > 0]
            last10_entries = bat_timeline[:10]
            last20_entries = bat_timeline[:20]

            def compute_bat_window(entries):
                if not entries:
                    return None
                total_runs = sum(e["bat"]["runs"] for e in entries)
                total_balls = sum(e["bat"]["balls"] for e in entries)
                dismissals = sum(1 for e in entries if e["bat"]["dismissed"])
                avg = total_runs / dismissals if dismissals > 0 else float(total_runs)
                sr = (total_runs / total_balls * 100) if total_balls > 0 else 0.0
                fifties = sum(1 for e in entries if 50 <= e["bat"]["runs"] < 100)
                hundreds = sum(1 for e in entries if e["bat"]["runs"] >= 100)
                return {
                    "innings": len(entries),
                    "runs": total_runs,
                    "average": round(avg, 2),
                    "strikeRate": round(sr, 2),
                    "fifties": fifties,
                    "hundreds": hundreds,
                }

            last10_stats = compute_bat_window(last10_entries)
            last20_stats = compute_bat_window(last20_entries)

            # Trend: compare last10 avg to last20 avg
            trend = "consistent"
            if last10_stats and last20_stats and last20_stats["average"] > 0:
                ratio = last10_stats["average"] / last20_stats["average"]
                if ratio > 1.20:
                    trend = "improving"
                elif ratio < 0.80:
                    trend = "declining"

            entry["recentForm"] = {
                "last10": last10_stats,
                "last20": last20_stats,
                "trend": trend,
            }

        # --- 2. formTimeline: last 30 T20 innings ---
        form_timeline = []
        for m in timeline_sorted[:30]:
            tl_entry = {
                "date": m["date"],
                "league": m["league"],
                "venue": m["venue"],
                "opposition": m["opposition"],
            }
            if m["bat"]:
                tl_entry["runs"] = m["bat"]["runs"]
                tl_entry["balls"] = m["bat"]["balls"]
                sr = (m["bat"]["runs"] / m["bat"]["balls"] * 100) if m["bat"]["balls"] > 0 else 0.0
                tl_entry["strikeRate"] = round(sr, 2)
                tl_entry["fours"] = m["bat"]["fours"]
                tl_entry["sixes"] = m["bat"]["sixes"]
                tl_entry["notOut"] = not m["bat"]["dismissed"]
            if m["bowl"] and m["bowl"]["balls"] > 0:
                overs_decimal = m["bowl"]["balls"] / 6.0
                economy = m["bowl"]["runs"] / overs_decimal if overs_decimal > 0 else 0.0
                tl_entry["wickets"] = m["bowl"]["wickets"]
                tl_entry["runsConceded"] = m["bowl"]["runs"]
                tl_entry["overs"] = format_overs(m["bowl"]["balls"])
                tl_entry["economy"] = round(economy, 2)
            form_timeline.append(tl_entry)

        entry["formTimeline"] = form_timeline

        # --- 3. seasonStats: per-season breakdown for last 3 seasons ---
        # Collect all seasons this player has data for
        player_season_bat = defaultdict(list)  # season_year -> list of bat records
        player_season_bowl = defaultdict(list)
        player_season_leagues = defaultdict(set)

        for date_str, midx, venue, lid, oppo, rec in match_batting.get(player, []):
            season_year = match_season.get(midx, "")
            if season_year:
                player_season_bat[season_year].append(rec)
                player_season_leagues[season_year].add(lid)
        for date_str, midx, venue, lid, oppo, rec in match_bowling.get(player, []):
            season_year = match_season.get(midx, "")
            if season_year:
                player_season_bowl[season_year].append(rec)
                player_season_leagues[season_year].add(lid)

        all_player_seasons = sorted(
            set(list(player_season_bat.keys()) + list(player_season_bowl.keys())),
            reverse=True,
        )
        season_stats = {}
        for season_year in all_player_seasons[:3]:
            s_entry = {"leagues": sorted(player_season_leagues.get(season_year, set()))}
            bat_recs = player_season_bat.get(season_year, [])
            bowl_recs = player_season_bowl.get(season_year, [])
            if bat_recs:
                agg = aggregate_batting(bat_recs)
                if agg:
                    s_entry["innings"] = agg["innings"]
                    s_entry["runs"] = agg["runs"]
                    s_entry["average"] = agg["average"]
                    s_entry["strikeRate"] = agg["strikeRate"]
            if bowl_recs:
                bowl_agg = aggregate_bowling(bowl_recs)
                if bowl_agg:
                    s_entry["bowlInnings"] = bowl_agg["innings"]
                    s_entry["bowlWickets"] = bowl_agg["wickets"]
                    s_entry["bowlEconomy"] = bowl_agg["economy"]
                    s_entry["bowlAverage"] = bowl_agg["average"]
            season_stats[season_year] = s_entry

        entry["seasonStats"] = season_stats

        # --- 4. rollingAverage: [date, cumulative_average] for last 30 innings ---
        # Chronological order for cumulative calculation
        if is_primary_bowler:
            # For bowlers: rolling economy over last 30 bowling innings
            bowl_chrono = [m for m in reversed(timeline_sorted) if m["bowl"] and m["bowl"]["balls"] > 0]
            # Take last 30
            bowl_chrono = bowl_chrono[-30:] if len(bowl_chrono) > 30 else bowl_chrono
            rolling = []
            cum_runs = 0
            cum_balls = 0
            for m in bowl_chrono:
                cum_runs += m["bowl"]["runs"]
                cum_balls += m["bowl"]["balls"]
                overs_dec = cum_balls / 6.0
                cum_econ = cum_runs / overs_dec if overs_dec > 0 else 0.0
                rolling.append([m["date"], round(cum_econ, 2)])
            entry["rollingAverage"] = rolling
        else:
            # For batters: rolling average over last 30 batting innings
            bat_chrono = [m for m in reversed(timeline_sorted) if m["bat"] and m["bat"]["balls"] > 0]
            # Take last 30
            bat_chrono = bat_chrono[-30:] if len(bat_chrono) > 30 else bat_chrono
            rolling = []
            cum_runs = 0
            cum_dismissals = 0
            for m in bat_chrono:
                cum_runs += m["bat"]["runs"]
                if m["bat"]["dismissed"]:
                    cum_dismissals += 1
                cum_avg = cum_runs / cum_dismissals if cum_dismissals > 0 else float(cum_runs)
                rolling.append([m["date"], round(cum_avg, 2)])
            entry["rollingAverage"] = rolling

        result[player] = entry

    # ---- Write output ----
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    file_size = os.path.getsize(OUT_FILE)
    print(f"\nWrote {OUT_FILE}")
    print(f"File size: {file_size / 1024 / 1024:.1f} MB")

    # ---- Summary ----
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total matches processed: {total_files}")
    print(f"  Per league:")
    for lid in sorted(league_counts):
        print(f"    {lid}: {league_counts[lid]}")
    print(f"Total unique players:    {len(result)}")
    print(f"Most recent season:      {recent_season}")

    # Cross-league stats
    multi_league = [(p, d) for p, d in result.items() if len(d.get("leagues", [])) >= 3]
    print(f"Players in 3+ leagues:   {len(multi_league)}")
    top_cross = sorted(multi_league, key=lambda x: len(x[1]["leagues"]), reverse=True)[:5]
    if top_cross:
        print(f"\nTop 5 Cross-League Players:")
        print(f"  {'Player':<25} {'#Leagues':>8}  Leagues")
        print(f"  {'-'*25} {'-'*8}  {'-'*30}")
        for name, d in top_cross:
            leagues_str = ", ".join(d["leagues"])
            print(f"  {name:<25} {len(d['leagues']):>8}  {leagues_str}")

    # Top 10 by runs
    players_by_runs = sorted(
        [(p, d["overall"].get("batting", {}).get("runs", 0)) for p, d in result.items()],
        key=lambda x: x[1], reverse=True
    )
    print(f"\nTop 10 Players by Runs:")
    print(f"  {'Player':<25} {'Runs':>6} {'Avg':>8} {'SR':>8} {'Inn':>5}")
    print(f"  {'-'*25} {'-'*6} {'-'*8} {'-'*8} {'-'*5}")
    for name, runs in players_by_runs[:10]:
        bat = result[name]["overall"].get("batting", {})
        print(f"  {name:<25} {runs:>6} {bat.get('average', 0):>8.2f} "
              f"{bat.get('strikeRate', 0):>8.2f} {bat.get('innings', 0):>5}")

    # Top 10 by wickets
    players_by_wickets = sorted(
        [(p, d["overall"].get("bowling", {}).get("wickets", 0)) for p, d in result.items()],
        key=lambda x: x[1], reverse=True
    )
    print(f"\nTop 10 Players by Wickets:")
    print(f"  {'Player':<25} {'Wkts':>5} {'Econ':>8} {'Avg':>8} {'Inn':>5}")
    print(f"  {'-'*25} {'-'*5} {'-'*8} {'-'*8} {'-'*5}")
    for name, wkts in players_by_wickets[:10]:
        bowl = result[name]["overall"].get("bowling", {})
        print(f"  {name:<25} {wkts:>5} {bowl.get('economy', 0):>8.2f} "
              f"{bowl.get('average', 0):>8.2f} {bowl.get('innings', 0):>5}")

    # Top 10 venues by # of players graded (non-N/A)
    venue_graded = defaultdict(int)
    for p, d in result.items():
        for v, vdata in d.get("venues", {}).items():
            if vdata.get("grade", "N/A") != "N/A":
                venue_graded[v] += 1

    top_venues = sorted(venue_graded.items(), key=lambda x: x[1], reverse=True)
    print(f"\nTop 10 Venues by Players Graded:")
    print(f"  {'Venue':<45} {'Graded':>7}")
    print(f"  {'-'*45} {'-'*7}")
    for venue, count in top_venues[:10]:
        print(f"  {venue:<45} {count:>7}")

    print(f"\n{'='*60}")
    print("Done!")


if __name__ == "__main__":
    process_all()
