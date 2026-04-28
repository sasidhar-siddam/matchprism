#!/usr/bin/env python3
"""
process_venues.py - Process Cricsheet JSON match files into venue statistics.

Reads all JSON match files from data/raw/<league>/ subdirectories and produces
a comprehensive venue stats JSON at data/processed/venues.json.

Supports all T20 leagues: IPL, BBL, CPL, PSL, LPL, SA20, The Hundred,
BPL, MLC, T20I, ILT20, NPL, and any future leagues added as subdirectories.

Uses only Python stdlib. No external dependencies.
"""

import json
import os
import sys
from collections import defaultdict

from venue_map import normalize_venue

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "venues.json")

# City normalization: Map venue canonical name -> preferred city name
# (for venues where city data is missing or inconsistent)
# NOTE: Keys here must match canonical names from venue_map.normalize_venue()
VENUE_CITY_OVERRIDE = {
    "Dubai International Cricket Stadium": "Dubai",
    "Sharjah Cricket Stadium": "Sharjah",
    "Sheikh Zayed Stadium": "Abu Dhabi",
    "M Chinnaswamy Stadium": "Bengaluru",
    "Arun Jaitley Stadium": "Delhi",
    "Mullanpur Stadium": "Chandigarh",
    "IS Bindra Stadium": "Chandigarh",
    "HPCA Stadium": "Dharamsala",
    "MCA Stadium": "Pune",
    "DY Patil Stadium": "Mumbai",
    "Ekana Cricket Stadium": "Lucknow",
    "Narendra Modi Stadium": "Ahmedabad",
    "VCA Stadium": "Nagpur",
    "ACA-VDCA Stadium": "Visakhapatnam",
}

# Wicket kinds that are attributed to the bowler (non-runout, non-retired)
BOWLER_WICKET_KINDS = {
    "bowled", "caught", "caught and bowled", "lbw", "stumped", "hit wicket"
}

# Recent seasons for avg1stInningsRecent calculation
RECENT_SEASONS = {"2024", "2025"}


def get_season(info):
    """Extract a comparable season string from match info.

    Seasons can be like '2017', '2007/08', '2009/10', '2020/21'.
    We normalize to the starting year for comparison, and also return
    the raw season string for recent-season filtering.
    """
    season = info.get("season")
    if season is None:
        # Fallback to dates
        dates = info.get("dates", [])
        if dates:
            return dates[0][:4]
        return None
    return str(season)


def season_to_year(season_str):
    """Convert season string to the primary year as int.

    '2017' -> 2017, '2007/08' -> 2007, '2020/21' -> 2020
    """
    if season_str is None:
        return None
    return int(season_str.split("/")[0])


def is_recent_season(season_str):
    """Check if the season is 2024 or 2025."""
    if season_str is None:
        return False
    year = season_to_year(season_str)
    return year in (2024, 2025)


def compute_phase_boundaries(total_overs, balls_per_over):
    """Compute phase over-number boundaries based on match format.

    Standard T20 (20 overs, 6 balls/over):
      powerplay: overs 0-5, middle: overs 6-14, death: overs 15-19

    The Hundred (20 overs, 5 balls/over in Cricsheet format):
      powerplay: overs 0-5 (25 balls), middle: overs 6-14, death: overs 15-19

    For non-standard overs (e.g., 50-over matches accidentally included):
      Scale phase boundaries proportionally.

    Returns (powerplay_end, middle_end, max_over_index, min_complete_balls).
      powerplay_end: last over index in powerplay (inclusive)
      middle_end: last over index in middle overs (inclusive)
      max_over_index: last over index (0-based), e.g., 19 for 20-over match
      min_complete_balls: minimum legal deliveries to consider innings complete
    """
    if total_overs is None or total_overs <= 0:
        total_overs = 20  # default T20

    if total_overs == 20:
        # Standard T20 / The Hundred in Cricsheet format
        return 5, 14, 19, total_overs * balls_per_over - 1
    else:
        # Scale proportionally for non-standard formats
        pp_end = max(0, round(total_overs * 0.3) - 1)     # ~30% powerplay
        mid_end = max(pp_end + 1, round(total_overs * 0.75) - 1)  # ~75% middle end
        max_over = total_overs - 1
        min_balls = total_overs * balls_per_over - 1
        return pp_end, mid_end, max_over, min_balls


def compute_innings_stats(innings_obj, total_overs=20, balls_per_over=6):
    """Compute stats from a single innings object.

    Args:
        innings_obj: The innings data from a Cricsheet match file.
        total_overs: Number of overs in the match (from info.overs).
        balls_per_over: Balls per over (from info.balls_per_over).

    Returns a dict with:
      total_runs, total_wickets, total_balls, total_overs_bowled,
      fours, sixes, bowler_wickets,
      powerplay_runs, middle_runs, death_runs,
      powerplay_balls, middle_balls, death_balls,
      is_complete (True if 10 wickets fell or full overs bowled)
    """
    pp_end, mid_end, max_over_idx, min_complete_balls = compute_phase_boundaries(
        total_overs, balls_per_over
    )

    stats = {
        "total_runs": 0,
        "total_wickets": 0,
        "total_balls": 0,  # legal deliveries
        "fours": 0,
        "sixes": 0,
        "bowler_wickets": 0,
        "powerplay_runs": 0,
        "middle_runs": 0,
        "death_runs": 0,
        "powerplay_balls": 0,
        "middle_balls": 0,
        "death_balls": 0,
        "is_complete": False,
        "overs_list": [],  # list of over numbers seen
    }

    overs = innings_obj.get("overs", [])
    max_over_num = -1

    for over_obj in overs:
        # Skip super over innings (handled at caller level)
        over_num = over_obj.get("over", 0)
        max_over_num = max(max_over_num, over_num)

        for delivery in over_obj.get("deliveries", []):
            runs = delivery.get("runs", {})
            total_runs = runs.get("total", 0)
            batter_runs = runs.get("batter", 0)
            extras = delivery.get("extras", {})

            stats["total_runs"] += total_runs

            # Determine if this is a legal delivery (not a wide or no-ball)
            is_wide = "wides" in extras
            is_noball = "noballs" in extras
            is_legal = not is_wide and not is_noball

            if is_legal:
                stats["total_balls"] += 1
            elif is_noball:
                # No-balls count as a ball faced for batting stats in some
                # contexts but NOT a legal delivery for over counting.
                # However, the batter can still hit boundaries off no-balls.
                pass

            # Boundaries: count batter runs == 4 or == 6
            if batter_runs == 4:
                stats["fours"] += 1
            elif batter_runs == 6:
                stats["sixes"] += 1

            # Wickets
            wickets = delivery.get("wickets", [])
            for w in wickets:
                stats["total_wickets"] += 1
                if w.get("kind") in BOWLER_WICKET_KINDS:
                    stats["bowler_wickets"] += 1

            # Phase breakdown using computed boundaries
            if over_num <= pp_end:
                stats["powerplay_runs"] += total_runs
                if is_legal:
                    stats["powerplay_balls"] += 1
            elif over_num <= mid_end:
                stats["middle_runs"] += total_runs
                if is_legal:
                    stats["middle_balls"] += 1
            else:
                stats["death_runs"] += total_runs
                if is_legal:
                    stats["death_balls"] += 1

    # Determine if innings is complete (for lowestTotal calculation)
    # Complete = all out (10 wickets) or full overs bowled
    if stats["total_wickets"] >= 10:
        stats["is_complete"] = True
    elif max_over_num >= max_over_idx and stats["total_balls"] >= min_complete_balls:
        stats["is_complete"] = True

    return stats


def process_matches():
    """Process all match files across all league subdirectories and return venue statistics."""

    if not os.path.isdir(RAW_DIR):
        print(f"ERROR: Raw data directory not found: {RAW_DIR}")
        sys.exit(1)

    # Discover all league subdirectories
    league_dirs = []
    for entry in sorted(os.listdir(RAW_DIR)):
        entry_path = os.path.join(RAW_DIR, entry)
        if os.path.isdir(entry_path):
            league_dirs.append((entry, entry_path))

    if not league_dirs:
        print(f"ERROR: No league subdirectories found in {RAW_DIR}")
        sys.exit(1)

    # Build list of (league_id, filepath) tuples
    all_files = []
    for league_id, league_path in league_dirs:
        files = [
            (league_id, os.path.join(league_path, f))
            for f in os.listdir(league_path)
            if f.endswith(".json")
        ]
        files.sort(key=lambda x: x[1])
        all_files.extend(files)
        print(f"  {league_id:<15} {len(files):>5} match files")

    total_files = len(all_files)
    print(f"\nTotal: {total_files} match files across {len(league_dirs)} leagues")

    # Per-venue accumulators
    venues = defaultdict(lambda: {
        "name": "",
        "city": "",
        "total_matches": 0,
        "leagues": set(),                  # set of league IDs
        "matches_by_league": defaultdict(int),  # league -> match count
        "first_innings_totals": [],
        "second_innings_totals": [],
        "first_innings_totals_recent": [],  # 2024, 2025
        "chase_wins": 0,      # matches won by team batting 2nd
        "total_decided": 0,   # matches with a winner
        "toss_bat_first": 0,
        "toss_bowl_first": 0,
        "toss_bat_win": 0,    # toss winner chose bat AND won match
        "toss_bat_total": 0,  # toss winner chose bat
        "toss_bowl_win": 0,   # toss winner chose bowl AND won match
        "toss_bowl_total": 0,
        "total_wickets": 0,
        "total_innings": 0,
        "total_runs": 0,
        "total_balls": 0,
        "total_fours": 0,
        "total_sixes": 0,
        "powerplay_runs": 0,
        "powerplay_innings": 0,
        "middle_runs": 0,
        "middle_innings": 0,
        "death_runs": 0,
        "death_innings": 0,
        "highest_total": 0,
        "lowest_total": 99999,
        "lowest_total_set": False,
        # Time-series: per-match records for trend/timeline calculations
        "match_records": [],   # list of dicts, one per match
    })

    skipped = 0
    processed = 0
    league_processed = defaultdict(int)

    for idx, (league_id, filepath) in enumerate(all_files):
        filename = os.path.basename(filepath)

        if (idx + 1) % 500 == 0 or idx == 0:
            print(f"  Processing file {idx + 1}/{total_files}...")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                match = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  WARNING: Could not read {league_id}/{filename}: {e}")
            skipped += 1
            continue

        info = match.get("info", {})
        innings_data = match.get("innings", [])

        # Basic validation
        raw_venue = info.get("venue")
        if not raw_venue:
            skipped += 1
            continue

        venue = normalize_venue(raw_venue)
        city = info.get("city", "")
        outcome = info.get("outcome", {})
        toss = info.get("toss", {})
        teams = info.get("teams", [])
        season_str = get_season(info)

        # Match format parameters (handles The Hundred and other formats)
        balls_per_over = info.get("balls_per_over", 6)
        total_overs = info.get("overs", 20)

        # Determine city (use override if available or missing)
        if venue in VENUE_CITY_OVERRIDE:
            city = VENUE_CITY_OVERRIDE[venue]
        elif not city:
            city = "Unknown"

        v = venues[venue]
        v["name"] = venue
        v["city"] = city
        v["total_matches"] += 1
        v["leagues"].add(league_id)
        v["matches_by_league"][league_id] += 1

        # --- Toss stats ---
        toss_decision = toss.get("decision", "")
        toss_winner = toss.get("winner", "")

        if toss_decision in ("bat",):
            v["toss_bat_first"] += 1
        elif toss_decision in ("field",):
            v["toss_bowl_first"] += 1

        # --- Outcome / chase / toss-win stats ---
        match_winner = outcome.get("winner")
        has_result = match_winner is not None

        if has_result:
            v["total_decided"] += 1

            # Determine which team batted first vs second
            # The first entry in innings_data is the team batting first
            batting_first = None
            batting_second = None
            if len(innings_data) >= 2:
                batting_first = innings_data[0].get("team")
                batting_second = innings_data[1].get("team")

            # Chase win: team batting second won
            if batting_second and match_winner == batting_second:
                v["chase_wins"] += 1

            # Toss winner performance
            if toss_winner and toss_decision:
                if toss_decision == "bat":
                    v["toss_bat_total"] += 1
                    if match_winner == toss_winner:
                        v["toss_bat_win"] += 1
                elif toss_decision == "field":
                    v["toss_bowl_total"] += 1
                    if match_winner == toss_winner:
                        v["toss_bowl_win"] += 1

        # --- Innings-level stats ---
        # Only process the main 2 innings (skip super overs)
        main_innings = []
        for inn in innings_data:
            if inn.get("super_over"):
                continue
            main_innings.append(inn)

        # Collect per-innings stats for both aggregate and match-record use
        innings_stats_list = []
        for inn_idx, inn in enumerate(main_innings[:2]):
            istats = compute_innings_stats(inn, total_overs, balls_per_over)

            total = istats["total_runs"]
            innings_stats_list.append(istats)

            # Track 1st/2nd innings totals
            if inn_idx == 0:
                v["first_innings_totals"].append(total)
                if is_recent_season(season_str):
                    v["first_innings_totals_recent"].append(total)
            elif inn_idx == 1:
                v["second_innings_totals"].append(total)

            # Aggregate stats
            v["total_innings"] += 1
            v["total_wickets"] += istats["total_wickets"]
            v["total_runs"] += istats["total_runs"]
            v["total_balls"] += istats["total_balls"]
            v["total_fours"] += istats["fours"]
            v["total_sixes"] += istats["sixes"]

            # Phase stats - only count if innings had deliveries in that phase
            if istats["powerplay_balls"] > 0:
                v["powerplay_runs"] += istats["powerplay_runs"]
                v["powerplay_innings"] += 1
            if istats["middle_balls"] > 0:
                v["middle_runs"] += istats["middle_runs"]
                v["middle_innings"] += 1
            if istats["death_balls"] > 0:
                v["death_runs"] += istats["death_runs"]
                v["death_innings"] += 1

            # Highest total
            if total > v["highest_total"]:
                v["highest_total"] = total

            # Lowest total (only completed innings)
            if istats["is_complete"] and total < v["lowest_total"]:
                v["lowest_total"] = total
                v["lowest_total_set"] = True

        # --- Build per-match record for time-series data ---
        match_date = ""
        dates = info.get("dates", [])
        if dates:
            match_date = dates[0]

        match_record = {
            "date": match_date,
            "league": league_id,
            "season": season_str,
        }

        # First innings data
        if len(innings_stats_list) >= 1:
            ist0 = innings_stats_list[0]
            match_record["firstInningsTotal"] = ist0["total_runs"]
            if ist0["total_balls"] > 0:
                match_record["firstInningsRR"] = round(
                    ist0["total_runs"] / (ist0["total_balls"] / 6), 2
                )
            else:
                match_record["firstInningsRR"] = 0
            match_record["firstInningsSixes"] = ist0["sixes"]
            match_record["firstInningsPP"] = ist0["powerplay_runs"]
            match_record["firstInningsMiddle"] = ist0["middle_runs"]
            match_record["firstInningsDeath"] = ist0["death_runs"]

        # Second innings data
        if len(innings_stats_list) >= 2:
            ist1 = innings_stats_list[1]
            match_record["secondInningsTotal"] = ist1["total_runs"]
            if ist1["total_balls"] > 0:
                match_record["secondInningsRR"] = round(
                    ist1["total_runs"] / (ist1["total_balls"] / 6), 2
                )
            else:
                match_record["secondInningsRR"] = 0
            match_record["secondInningsSixes"] = ist1["sixes"]
            match_record["secondInningsPP"] = ist1["powerplay_runs"]
            match_record["secondInningsMiddle"] = ist1["middle_runs"]
            match_record["secondInningsDeath"] = ist1["death_runs"]

        # Winner determination (batting_first or chasing)
        batting_first_team = None
        if len(main_innings) >= 1:
            batting_first_team = main_innings[0].get("team")

        if has_result and batting_first_team:
            if match_winner == batting_first_team:
                match_record["winner"] = "batting_first"
            else:
                match_record["winner"] = "chasing"
        else:
            match_record["winner"] = None

        v["match_records"].append(match_record)

        processed += 1
        league_processed[league_id] += 1

    print(f"\n  Processed {processed} matches, skipped {skipped}")
    print(f"  Per-league breakdown:")
    for lid in sorted(league_processed):
        print(f"    {lid:<15} {league_processed[lid]:>5} matches")

    return venues


def generate_verdict(stats):
    """Generate a one-line verdict string summarizing the venue character."""
    parts = []

    avg1st = stats.get("avg1stInnings", 0)
    chase_pct = stats.get("chaseWinPct", 50)
    powerplay = stats.get("powerplayAvg", 0)
    rr = stats.get("venueRunRate", 0)
    sixes = stats.get("sixesPerInnings", 0)

    # Scoring character
    if avg1st >= 185:
        parts.append("High-scoring ground")
    elif avg1st >= 170:
        parts.append("Good batting surface")
    elif avg1st >= 155:
        parts.append("Balanced track")
    elif avg1st > 0:
        parts.append("Bowler-friendly venue")

    # Chase/defend character
    if chase_pct >= 60:
        parts.append("strongly favors chasing teams")
    elif chase_pct >= 55:
        parts.append("slight advantage to chasing sides")
    elif chase_pct <= 40:
        parts.append("defending teams dominate")
    elif chase_pct <= 45:
        parts.append("slight advantage to defending sides")
    else:
        parts.append("evenly split between batting first and chasing")

    # Boundary character
    if sixes >= 5:
        parts.append("with plenty of sixes")
    elif rr >= 9.0:
        parts.append("with quick scoring")

    if not parts:
        return "Insufficient data for verdict"

    # Capitalize first part, join with commas
    verdict = parts[0]
    if len(parts) > 1:
        verdict += ", " + ", ".join(parts[1:])
    verdict += "."

    return verdict


def compute_time_series(match_records, overall_avg_1st, overall_run_rate,
                        overall_chase_pct, overall_sixes_per_inn,
                        overall_pp_avg, overall_mid_avg, overall_death_avg):
    """Compute time-series trend data from per-venue match records.

    Returns a dict with: recentForm, scoringTimeline, seasonComparison,
    phaseProgression.
    """
    # Sort by date ascending for chronological processing
    sorted_records = sorted(match_records, key=lambda r: r.get("date", ""))

    # --- scoringTimeline: last 30 matches, most recent first ---
    scoring_timeline = []
    for rec in reversed(sorted_records[-30:]):
        entry = {
            "date": rec.get("date", ""),
            "league": rec.get("league", ""),
        }
        if "firstInningsTotal" in rec:
            entry["firstInningsTotal"] = rec["firstInningsTotal"]
        else:
            entry["firstInningsTotal"] = None
        if "secondInningsTotal" in rec:
            entry["secondInningsTotal"] = rec["secondInningsTotal"]
        else:
            entry["secondInningsTotal"] = None
        if "firstInningsRR" in rec:
            entry["firstInningsRR"] = rec["firstInningsRR"]
        else:
            entry["firstInningsRR"] = None
        entry["winner"] = rec.get("winner")
        scoring_timeline.append(entry)

    # --- recentForm: rolling stats from last 10 and last 20 matches ---
    def compute_rolling_stats(records):
        """Compute avg1stInnings, avgRunRate, chaseWinPct, avgSixes from a list of match records."""
        if not records:
            return None
        first_totals = [r["firstInningsTotal"] for r in records if "firstInningsTotal" in r]
        avg_1st = round(sum(first_totals) / len(first_totals), 1) if first_totals else 0

        # Run rate: average of both innings run rates
        rr_vals = []
        for r in records:
            if "firstInningsRR" in r and r["firstInningsRR"]:
                rr_vals.append(r["firstInningsRR"])
            if "secondInningsRR" in r and r["secondInningsRR"]:
                rr_vals.append(r["secondInningsRR"])
        avg_rr = round(sum(rr_vals) / len(rr_vals), 2) if rr_vals else 0

        # Chase win %
        decided = [r for r in records if r.get("winner") is not None]
        chase_wins = sum(1 for r in decided if r["winner"] == "chasing")
        chase_pct = round((chase_wins / len(decided)) * 100) if decided else 0

        # Average sixes per innings
        sixes_vals = []
        for r in records:
            if "firstInningsSixes" in r:
                sixes_vals.append(r["firstInningsSixes"])
            if "secondInningsSixes" in r:
                sixes_vals.append(r["secondInningsSixes"])
        avg_sixes = round(sum(sixes_vals) / len(sixes_vals), 1) if sixes_vals else 0

        return {
            "avg1stInnings": avg_1st,
            "avgRunRate": avg_rr,
            "chaseWinPct": chase_pct,
            "avgSixes": avg_sixes,
        }

    last10 = sorted_records[-10:] if len(sorted_records) >= 10 else sorted_records[:]
    last20 = sorted_records[-20:] if len(sorted_records) >= 20 else sorted_records[:]

    last10_stats = compute_rolling_stats(last10)
    last20_stats = compute_rolling_stats(last20)

    # Determine trend by comparing last10 avg1stInnings to overall
    trend = "stable"
    if last10_stats and overall_avg_1st and overall_avg_1st > 0:
        ratio = last10_stats["avg1stInnings"] / overall_avg_1st
        if ratio > 1.10:
            trend = "scoring_up"
        elif ratio < 0.90:
            trend = "scoring_down"

    recent_form = {
        "last10": last10_stats,
        "last20": last20_stats,
        "trend": trend,
    }

    # --- seasonComparison: last 2 seasons vs overall ---
    # Find the two most recent seasons
    season_records = defaultdict(list)
    for rec in sorted_records:
        s = rec.get("season")
        if s:
            year = int(str(s).split("/")[0])
            season_records[year].append(rec)

    all_years = sorted(season_records.keys())
    last_two_years = all_years[-2:] if len(all_years) >= 2 else all_years

    season_comparison = {}
    for year in last_two_years:
        recs = season_records[year]
        stats = compute_rolling_stats(recs)
        if stats:
            season_comparison[str(year)] = {
                "matches": len(recs),
                "avg1stInnings": stats["avg1stInnings"],
                "avgRunRate": stats["avgRunRate"],
                "chaseWinPct": stats["chaseWinPct"],
            }

    # --- phaseProgression: overall vs recent 20, with trend ---
    def compute_phase_avgs(records):
        """Compute average powerplay, middle, death scores from match records."""
        pp_vals = []
        mid_vals = []
        death_vals = []
        for r in records:
            # Collect from both innings
            for prefix in ("firstInnings", "secondInnings"):
                pp_key = prefix + "PP"
                mid_key = prefix + "Middle"
                death_key = prefix + "Death"
                if pp_key in r:
                    pp_vals.append(r[pp_key])
                if mid_key in r:
                    mid_vals.append(r[mid_key])
                if death_key in r:
                    death_vals.append(r[death_key])
        pp_avg = round(sum(pp_vals) / len(pp_vals), 1) if pp_vals else 0
        mid_avg = round(sum(mid_vals) / len(mid_vals), 1) if mid_vals else 0
        death_avg = round(sum(death_vals) / len(death_vals), 1) if death_vals else 0
        return {"powerplay": pp_avg, "middle": mid_avg, "death": death_avg}

    overall_phases = compute_phase_avgs(sorted_records)
    recent20_phases = compute_phase_avgs(last20)

    phase_trend = {}
    for phase in ("powerplay", "middle", "death"):
        diff = round(recent20_phases[phase] - overall_phases[phase], 1)
        phase_trend[phase] = f"+{diff}" if diff >= 0 else str(diff)

    phase_progression = {
        "overall": overall_phases,
        "recent20": recent20_phases,
        "trend": phase_trend,
    }

    return {
        "recentForm": recent_form,
        "scoringTimeline": scoring_timeline,
        "seasonComparison": season_comparison,
        "phaseProgression": phase_progression,
    }


def build_output(venues):
    """Convert raw accumulators into the final output format."""
    output = {}

    for venue_name, v in venues.items():
        total_matches = v["total_matches"]
        if total_matches == 0:
            continue

        stats = {
            "name": v["name"],
            "city": v["city"],
            "totalMatches": total_matches,
            "leagues": sorted(v["leagues"]),
            "matchesByLeague": dict(sorted(v["matches_by_league"].items())),
        }

        # Average 1st innings
        if v["first_innings_totals"]:
            stats["avg1stInnings"] = round(
                sum(v["first_innings_totals"]) / len(v["first_innings_totals"]), 1
            )
        else:
            stats["avg1stInnings"] = 0

        # Average 2nd innings
        if v["second_innings_totals"]:
            stats["avg2ndInnings"] = round(
                sum(v["second_innings_totals"]) / len(v["second_innings_totals"]), 1
            )
        else:
            stats["avg2ndInnings"] = 0

        # Average 1st innings recent (2024, 2025)
        if v["first_innings_totals_recent"]:
            stats["avg1stInningsRecent"] = round(
                sum(v["first_innings_totals_recent"])
                / len(v["first_innings_totals_recent"]),
                1,
            )
        else:
            stats["avg1stInningsRecent"] = None

        # Chase win %
        if v["total_decided"] > 0:
            stats["chaseWinPct"] = round(
                (v["chase_wins"] / v["total_decided"]) * 100
            )
        else:
            stats["chaseWinPct"] = 0

        # Toss decision %
        total_tosses = v["toss_bat_first"] + v["toss_bowl_first"]
        if total_tosses > 0:
            stats["tossBatFirstPct"] = round(
                (v["toss_bat_first"] / total_tosses) * 100
            )
            stats["tossBowlFirstPct"] = round(
                (v["toss_bowl_first"] / total_tosses) * 100
            )
        else:
            stats["tossBatFirstPct"] = 0
            stats["tossBowlFirstPct"] = 0

        # Toss winner win % by decision
        if v["toss_bat_total"] > 0:
            stats["tossWinBatPct"] = round(
                (v["toss_bat_win"] / v["toss_bat_total"]) * 100
            )
        else:
            stats["tossWinBatPct"] = None

        if v["toss_bowl_total"] > 0:
            stats["tossWinBowlPct"] = round(
                (v["toss_bowl_win"] / v["toss_bowl_total"]) * 100
            )
        else:
            stats["tossWinBowlPct"] = None

        # Phase averages
        if v["powerplay_innings"] > 0:
            stats["powerplayAvg"] = round(
                v["powerplay_runs"] / v["powerplay_innings"], 1
            )
        else:
            stats["powerplayAvg"] = 0

        if v["middle_innings"] > 0:
            stats["middleOversAvg"] = round(
                v["middle_runs"] / v["middle_innings"], 1
            )
        else:
            stats["middleOversAvg"] = 0

        if v["death_innings"] > 0:
            stats["deathOversAvg"] = round(
                v["death_runs"] / v["death_innings"], 1
            )
        else:
            stats["deathOversAvg"] = 0

        # Highest / lowest totals
        stats["highestTotal"] = v["highest_total"]
        if v["lowest_total_set"]:
            stats["lowestTotal"] = v["lowest_total"]
        else:
            stats["lowestTotal"] = None

        # Average wickets per innings
        if v["total_innings"] > 0:
            stats["avgWicketsPerInnings"] = round(
                v["total_wickets"] / v["total_innings"], 1
            )
        else:
            stats["avgWicketsPerInnings"] = 0

        # Venue run rate (total runs / total overs bowled)
        if v["total_balls"] > 0:
            total_overs = v["total_balls"] / 6
            stats["venueRunRate"] = round(v["total_runs"] / total_overs, 2)
        else:
            stats["venueRunRate"] = 0

        # Boundaries per innings
        if v["total_innings"] > 0:
            total_boundaries = v["total_fours"] + v["total_sixes"]
            stats["boundariesPerInnings"] = round(
                total_boundaries / v["total_innings"], 1
            )
            stats["sixesPerInnings"] = round(
                v["total_sixes"] / v["total_innings"], 1
            )
            stats["foursPerInnings"] = round(
                v["total_fours"] / v["total_innings"], 1
            )
        else:
            stats["boundariesPerInnings"] = 0
            stats["sixesPerInnings"] = 0
            stats["foursPerInnings"] = 0

        # Verdict
        stats["verdict"] = generate_verdict(stats)

        # Physical venue characteristics (constant, not match-day variable)
        VENUE_PHYSICAL = {
            "M Chinnaswamy Stadium": {"altitude_m": 920, "boundary_avg_m": 60},
            "Wankhede Stadium": {"altitude_m": 14, "boundary_avg_m": 65},
            "Eden Gardens": {"altitude_m": 9, "boundary_avg_m": 68},
            "MA Chidambaram Stadium": {"altitude_m": 6, "boundary_avg_m": 62},
            "Rajiv Gandhi International Stadium": {"altitude_m": 542, "boundary_avg_m": 64},
            "Arun Jaitley Stadium": {"altitude_m": 216, "boundary_avg_m": 63},
            "Sawai Mansingh Stadium": {"altitude_m": 431, "boundary_avg_m": 66},
            "IS Bindra Stadium": {"altitude_m": 316, "boundary_avg_m": 65},
            "Narendra Modi Stadium": {"altitude_m": 53, "boundary_avg_m": 76},
            "Ekana Cricket Stadium": {"altitude_m": 123, "boundary_avg_m": 70},
            "HPCA Stadium": {"altitude_m": 1457, "boundary_avg_m": 58},
            "MCA Stadium": {"altitude_m": 562, "boundary_avg_m": 68},
            "DY Patil Stadium": {"altitude_m": 10, "boundary_avg_m": 67},
            "Dubai International Cricket Stadium": {"altitude_m": 5, "boundary_avg_m": 75},
            "Sharjah Cricket Stadium": {"altitude_m": 5, "boundary_avg_m": 62},
            "Sheikh Zayed Stadium": {"altitude_m": 5, "boundary_avg_m": 72},
            "SuperSport Park": {"altitude_m": 1340, "boundary_avg_m": 70},
            "Newlands": {"altitude_m": 15, "boundary_avg_m": 68},
            "Mullanpur Stadium": {"altitude_m": 316, "boundary_avg_m": 65},
        }
        phys = VENUE_PHYSICAL.get(venue_name, {})
        if phys:
            stats["altitude_m"] = phys["altitude_m"]
            stats["boundary_avg_m"] = phys["boundary_avg_m"]
            # Compute constant altitude effect on ball travel
            alt = phys["altitude_m"]
            travel_bonus = round((alt / 300) * 1.5, 1)
            stats["altitudeEffect"] = {
                "ball_travel_bonus_pct": travel_bonus,
                "impact": "High" if travel_bonus > 5 else ("Moderate" if travel_bonus > 2 else "Low"),
            }

        # --- Time-series trend data ---
        if v["match_records"]:
            ts = compute_time_series(
                v["match_records"],
                overall_avg_1st=stats["avg1stInnings"],
                overall_run_rate=stats["venueRunRate"],
                overall_chase_pct=stats["chaseWinPct"],
                overall_sixes_per_inn=stats["sixesPerInnings"],
                overall_pp_avg=stats["powerplayAvg"],
                overall_mid_avg=stats["middleOversAvg"],
                overall_death_avg=stats["deathOversAvg"],
            )
            stats["recentForm"] = ts["recentForm"]
            stats["scoringTimeline"] = ts["scoringTimeline"]
            stats["seasonComparison"] = ts["seasonComparison"]
            stats["phaseProgression"] = ts["phaseProgression"]

        output[venue_name] = stats

    return output


def main():
    print("=" * 60)
    print("MatchPrism - Venue Statistics Processor")
    print("=" * 60)

    venues = process_matches()
    output = build_output(venues)

    # Sort by totalMatches descending for readability
    sorted_output = dict(
        sorted(output.items(), key=lambda x: x[1]["totalMatches"], reverse=True)
    )

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted_output, f, indent=2, ensure_ascii=False)

    # Compute summary totals
    total_matches = sum(s["totalMatches"] for s in sorted_output.values())
    all_leagues = set()
    for s in sorted_output.values():
        all_leagues.update(s["leagues"])

    print(f"\nOutput written to {OUTPUT_FILE}")
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total matches processed: {total_matches}")
    print(f"Total venues: {len(sorted_output)}")
    print(f"Leagues: {', '.join(sorted(all_leagues))}")
    print(f"\nTop 20 venues by match count:")
    print(f"\n{'Venue':<50} {'Matches':>7}  {'Avg 1st':>7}  {'Chase%':>6}  {'RR':>5}  {'Leagues'}")
    print("-" * 115)
    for i, (name, stats) in enumerate(sorted_output.items()):
        if i >= 20:
            break
        avg1st = stats["avg1stInnings"]
        chase = stats["chaseWinPct"]
        rr = stats["venueRunRate"]
        leagues = ",".join(stats["leagues"])
        print(
            f"{name:<50} {stats['totalMatches']:>7}  "
            f"{avg1st:>7.1f}  {chase:>5}%  {rr:>5.2f}  {leagues}"
        )

    # Top insights
    print(f"\n{'=' * 60}")
    print("TOP INSIGHTS")
    print(f"{'=' * 60}")

    # Only venues with 10+ matches for meaningful stats
    sig_venues = {k: v for k, v in sorted_output.items() if v["totalMatches"] >= 10}

    if sig_venues:
        highest_scoring = max(sig_venues.items(), key=lambda x: x[1]["avg1stInnings"])
        print(f"Highest scoring (10+ matches): {highest_scoring[0]} "
              f"(avg 1st innings: {highest_scoring[1]['avg1stInnings']})")

        lowest_scoring = min(sig_venues.items(), key=lambda x: x[1]["avg1stInnings"])
        print(f"Lowest scoring (10+ matches):  {lowest_scoring[0]} "
              f"(avg 1st innings: {lowest_scoring[1]['avg1stInnings']})")

        best_chase = max(sig_venues.items(), key=lambda x: x[1]["chaseWinPct"])
        print(f"Best for chasing (10+ matches): {best_chase[0]} "
              f"(chase win: {best_chase[1]['chaseWinPct']}%)")

        best_defend = min(sig_venues.items(), key=lambda x: x[1]["chaseWinPct"])
        print(f"Best for defending (10+ matches): {best_defend[0]} "
              f"(chase win: {best_defend[1]['chaseWinPct']}%)")

        most_sixes = max(sig_venues.items(), key=lambda x: x[1]["sixesPerInnings"])
        print(f"Most sixes (10+ matches): {most_sixes[0]} "
              f"({most_sixes[1]['sixesPerInnings']} per innings)")

    print()


if __name__ == "__main__":
    main()
