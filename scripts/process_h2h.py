"""Process Cricsheet JSON files from ALL leagues into head-to-head statistics."""

import json
import os
import glob
from collections import defaultdict

from venue_map import normalize_venue

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
OUT_FILE = os.path.join(OUT_DIR, "h2h.json")

# ---------------------------------------------------------------------------
# League detection
# ---------------------------------------------------------------------------

# Map subdirectory names to display league names
LEAGUE_DISPLAY = {
    "ipl": "IPL",
    "bbl": "BBL",
    "psl": "PSL",
    "cpl": "CPL",
    "sa20": "SA20",
    "the_hundred": "The Hundred",
    "lpl": "LPL",
    "bpl": "BPL",
    "ilt20": "ILT20",
    "mlc": "MLC",
    "npl": "NPL",
    "t20i": "T20I",
}

# ---------------------------------------------------------------------------
# Team name normalization (per-league)
# ---------------------------------------------------------------------------

# IPL: map old/alternate names to current canonical names
IPL_TEAM_NAME_MAP = {
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Delhi Daredevils": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
    # Defunct IPL teams mapped to themselves (included, not filtered)
    # "Deccan Chargers", "Kochi Tuskers Kerala", etc. keep their names
}

# CPL: franchise renames over the years
CPL_TEAM_NAME_MAP = {
    "Trinidad & Tobago Red Steel": "Trinbago Knight Riders",
    "St Lucia Zouks": "St Lucia Kings",
    "St Lucia Stars": "St Lucia Kings",
    "Barbados Tridents": "Barbados Royals",
    "Antigua Hawksbills": "Antigua and Barbuda Falcons",
}

# BPL: franchise renames (consolidate city-based teams where clear lineage)
BPL_TEAM_NAME_MAP = {
    "Chittagong Vikings": "Chattogram Challengers",
    "Chittagong Kings": "Chattogram Challengers",
    "Chattogram Royals": "Chattogram Challengers",
    "Barisal Bulls": "Fortune Barishal",
    "Barisal Burners": "Fortune Barishal",
    "Dhaka Dynamites": "Dhaka Capitals",
    "Dhaka Gladiators": "Dhaka Capitals",
    "Dhaka Platoon": "Dhaka Capitals",
    "Durdanto Dhaka": "Dhaka Capitals",
    "Minister Group Dhaka": "Dhaka Capitals",
    "Dhaka Dominators": "Dhaka Capitals",
    "Durbar Rajshahi": "Rajshahi Royals",
    "Duronto Rajshahi": "Rajshahi Royals",
    "Rajshahi Kings": "Rajshahi Royals",
    "Rajshahi Warriors": "Rajshahi Royals",
    "Sylhet Royals": "Sylhet Strikers",
    "Sylhet Sixers": "Sylhet Strikers",
    "Sylhet Super Stars": "Sylhet Strikers",
    "Sylhet Sunrisers": "Sylhet Strikers",
    "Sylhet Thunder": "Sylhet Strikers",
    "Sylhet Titans": "Sylhet Strikers",
    "Khulna Royal Bengals": "Khulna Tigers",
    "Khulna Titans": "Khulna Tigers",
    "Rangpur Rangers": "Rangpur Riders",
    "Cumilla Warriors": "Comilla Victorians",
}

# LPL: franchise renames across seasons
LPL_TEAM_NAME_MAP = {
    "Kandy Tuskers": "Kandy Falcons",
    "Kandy Warriors": "Kandy Falcons",
    "B-Love Kandy": "Kandy Falcons",
    "Dambulla Viiking": "Dambulla Aura",
    "Dambulla Giants": "Dambulla Aura",
    "Dambulla Sixers": "Dambulla Aura",
    "Jaffna Stallions": "Jaffna Kings",
    "Colombo Kings": "Colombo Strikers",
    "Colombo Stars": "Colombo Strikers",
    "Galle Gladiators": "Galle Marvels",
    "Galle Titans": "Galle Marvels",
}

# ILT20: minor name variant
ILT20_TEAM_NAME_MAP = {
    "Sharjah Warriors": "Sharjah Warriorz",
}

# NPL: minor name variant
NPL_TEAM_NAME_MAP = {
    "Kathmandu Gorkhas": "Kathmandu Gurkhas",
}

# Consolidated per-league normalization maps
LEAGUE_TEAM_NAME_MAPS = {
    "ipl": IPL_TEAM_NAME_MAP,
    "cpl": CPL_TEAM_NAME_MAP,
    "bpl": BPL_TEAM_NAME_MAP,
    "lpl": LPL_TEAM_NAME_MAP,
    "ilt20": ILT20_TEAM_NAME_MAP,
    "npl": NPL_TEAM_NAME_MAP,
}


def normalize_team(name, league=None):
    """Return the canonical name for a team within its league.

    Always returns a name (never None) -- all teams are included.
    """
    if league and league in LEAGUE_TEAM_NAME_MAPS:
        name = LEAGUE_TEAM_NAME_MAPS[league].get(name, name)
    return name


# ---------------------------------------------------------------------------
# Innings score calculation
# ---------------------------------------------------------------------------


def compute_innings_score(innings_data):
    """Compute total runs and wickets from an innings object.

    Returns (total_runs, wickets) tuple.
    """
    total_runs = 0
    wickets = 0
    for over in innings_data.get("overs", []):
        for delivery in over.get("deliveries", []):
            total_runs += delivery["runs"]["total"]
            if "wickets" in delivery:
                wickets += len(delivery["wickets"])
    return total_runs, wickets


def format_score(runs, wickets):
    """Format as 'RUNS/WICKETS', e.g. '187/2'."""
    return f"{runs}/{wickets}"


# ---------------------------------------------------------------------------
# Margin formatting
# ---------------------------------------------------------------------------


def format_margin(outcome):
    """Return a human-readable margin string like 'won by 35 runs'."""
    by = outcome.get("by", {})
    if "runs" in by:
        return f"won by {by['runs']} runs"
    if "wickets" in by:
        return f"won by {by['wickets']} wickets"
    return ""


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------


def make_pair_key(t1, t2):
    """Return an alphabetically sorted pair key."""
    a, b = sorted([t1, t2])
    return f"{a} vs {b}"


def discover_match_files():
    """Find all match JSON files across all league subdirectories.

    Returns list of (filepath, league_code) tuples.
    """
    match_files = []

    # Iterate through subdirectories of RAW_DIR
    if not os.path.isdir(RAW_DIR):
        print(f"Warning: {RAW_DIR} does not exist")
        return match_files

    for entry in sorted(os.listdir(RAW_DIR)):
        subdir = os.path.join(RAW_DIR, entry)
        if not os.path.isdir(subdir):
            continue

        league_code = entry.lower()
        files = sorted(glob.glob(os.path.join(subdir, "*.json")))
        for fp in files:
            match_files.append((fp, league_code))

    return match_files


def process_all_matches():
    match_files = discover_match_files()
    print(f"Found {len(match_files)} total match files across all leagues")

    # Count per league
    league_counts = defaultdict(int)
    for _, lc in match_files:
        league_counts[lc] += 1
    for lc in sorted(league_counts):
        display = LEAGUE_DISPLAY.get(lc, lc.upper())
        print(f"  {display}: {league_counts[lc]} files")

    # Accumulator: pair_key -> stats dict
    h2h = {}

    skipped_no_result = 0
    processed = 0
    processed_by_league = defaultdict(int)

    for filepath, league_code in match_files:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        info = data.get("info", {})
        teams_raw = info.get("teams", [])
        if len(teams_raw) != 2:
            continue

        league_display = LEAGUE_DISPLAY.get(league_code, league_code.upper())

        # Normalize team names (league-specific)
        t1 = normalize_team(teams_raw[0], league_code)
        t2 = normalize_team(teams_raw[1], league_code)

        outcome = info.get("outcome", {})
        venue = normalize_venue(info.get("venue", "Unknown"))
        date_str = info.get("dates", [""])[0]

        pair_key = make_pair_key(t1, t2)
        team1 = sorted([t1, t2])[0]
        team2 = sorted([t1, t2])[1]

        # Initialize pair if needed
        if pair_key not in h2h:
            h2h[pair_key] = {
                "team1": team1,
                "team2": team2,
                "team1Wins": 0,
                "team2Wins": 0,
                "ties": 0,
                "totalMatches": 0,
                "totalScoreSum": 0,
                "totalInningsCount": 0,
                "leagues": [],
                "byVenue": {},
                "recentMatches": [],
            }

        rec = h2h[pair_key]
        rec["totalMatches"] += 1

        # Track which leagues this rivalry spans
        if league_display not in rec["leagues"]:
            rec["leagues"].append(league_display)

        # Initialize venue stats if needed
        if venue not in rec["byVenue"]:
            rec["byVenue"][venue] = {
                "team1Wins": 0,
                "team2Wins": 0,
                "totalMatches": 0,
            }
        rec["byVenue"][venue]["totalMatches"] += 1

        # Determine winner
        is_no_result = outcome.get("result") == "no result"
        is_tie = outcome.get("result") == "tie"
        winner_raw = outcome.get("winner")

        if is_no_result:
            rec["ties"] += 1
            skipped_no_result += 1
        elif is_tie:
            # Ties with super over: the eliminator wins for H2H purposes.
            eliminator = outcome.get("eliminator")
            if eliminator:
                winner = normalize_team(eliminator, league_code)
                if winner == team1:
                    rec["team1Wins"] += 1
                    rec["byVenue"][venue]["team1Wins"] += 1
                elif winner == team2:
                    rec["team2Wins"] += 1
                    rec["byVenue"][venue]["team2Wins"] += 1
                else:
                    rec["ties"] += 1
            else:
                rec["ties"] += 1
        elif winner_raw:
            winner = normalize_team(winner_raw, league_code)
            if winner == team1:
                rec["team1Wins"] += 1
                rec["byVenue"][venue]["team1Wins"] += 1
            elif winner == team2:
                rec["team2Wins"] += 1
                rec["byVenue"][venue]["team2Wins"] += 1
            else:
                # Should not happen
                rec["ties"] += 1
        else:
            rec["ties"] += 1

        # Compute innings scores (only first 2 innings, ignoring super overs)
        innings = data.get("innings", [])
        scores_by_team = {}
        for inn_idx, inn in enumerate(innings[:2]):
            inn_team_raw = inn.get("team", "")
            inn_team = normalize_team(inn_team_raw, league_code)
            if inn_team is None:
                continue
            runs, wickets = compute_innings_score(inn)
            scores_by_team[inn_team] = (runs, wickets)
            rec["totalScoreSum"] += runs
            rec["totalInningsCount"] += 1

        # Build recent match entry
        team1_score_tuple = scores_by_team.get(team1, (0, 0))
        team2_score_tuple = scores_by_team.get(team2, (0, 0))

        margin = ""
        match_winner = ""
        if is_no_result:
            match_winner = "No Result"
            margin = "no result"
        elif is_tie:
            eliminator = outcome.get("eliminator")
            if eliminator:
                match_winner = normalize_team(eliminator, league_code) or ""
                margin = "won by super over"
            else:
                match_winner = "Tie"
                margin = "tie"
        elif winner_raw:
            match_winner = normalize_team(winner_raw, league_code) or ""
            margin = format_margin(outcome)
            method = outcome.get("method")
            if method:
                margin += f" ({method})"

        recent_entry = {
            "date": date_str,
            "venue": venue,
            "league": league_display,
            "team1Score": format_score(*team1_score_tuple),
            "team2Score": format_score(*team2_score_tuple),
            "winner": match_winner,
            "margin": margin,
        }
        rec["recentMatches"].append(recent_entry)

        processed += 1
        processed_by_league[league_display] += 1

    print(f"\nProcessed {processed} matches total")
    for league in sorted(processed_by_league):
        print(f"  {league}: {processed_by_league[league]} matches")
    print(f"Found {skipped_no_result} no-result matches")

    # Post-process: compute avgScore, trim recentMatches to last 5
    for pair_key, rec in h2h.items():
        # Average score per innings across all H2H matches
        if rec["totalInningsCount"] > 0:
            rec["avgScore"] = round(
                rec["totalScoreSum"] / rec["totalInningsCount"], 1
            )
        else:
            rec["avgScore"] = 0

        # Remove internal accumulators
        del rec["totalScoreSum"]
        del rec["totalInningsCount"]

        # Sort leagues alphabetically for consistency
        rec["leagues"].sort()

        # Sort recent matches by date descending, keep last 5
        rec["recentMatches"].sort(key=lambda m: m["date"], reverse=True)
        rec["recentMatches"] = rec["recentMatches"][:5]

    return h2h


def print_summary(h2h):
    """Print summary: total pairs, total matches, top 10, sample T20I."""
    if not h2h:
        print("No H2H data to summarize.")
        return

    total_matches = sum(r["totalMatches"] for r in h2h.values())

    print(f"\n{'='*60}")
    print(f"H2H Summary")
    print(f"{'='*60}")
    print(f"Total rivalry pairs: {len(h2h)}")
    print(f"Total matches processed: {total_matches}")

    # Top 10 rivalries by match count
    sorted_by_matches = sorted(
        h2h.values(), key=lambda r: r["totalMatches"], reverse=True
    )
    print(f"\nTop 10 rivalries by match count:")
    for i, rec in enumerate(sorted_by_matches[:10], 1):
        leagues_str = ", ".join(rec["leagues"])
        print(
            f"  {i:2d}. {rec['team1']} vs {rec['team2']}"
            f" — {rec['totalMatches']} matches"
            f" ({rec['team1Wins']}-{rec['team2Wins']}"
            f", {rec['ties']} ties/NR)"
            f" [{leagues_str}]"
        )

    # Sample T20I rivalry
    t20i_pairs = [
        r for r in h2h.values() if "T20I" in r.get("leagues", [])
    ]
    if t20i_pairs:
        # Try to find a specific well-known rivalry
        sample = None
        for r in t20i_pairs:
            names = {r["team1"], r["team2"]}
            if "India" in names and "Australia" in names:
                sample = r
                break
        # If India vs Australia not found, pick the most-played T20I rivalry
        if not sample:
            sample = max(t20i_pairs, key=lambda r: r["totalMatches"])

        print(
            f"\nSample T20I rivalry: {sample['team1']} vs {sample['team2']}"
        )
        print(
            f"  {sample['totalMatches']} matches"
            f" ({sample['team1Wins']}-{sample['team2Wins']}"
            f", {sample['ties']} ties/NR)"
        )
        print(f"  Average innings score: {sample['avgScore']}")
        if sample["recentMatches"]:
            latest = sample["recentMatches"][0]
            print(
                f"  Most recent: {latest['date']} at {latest['venue']}"
                f" — {latest['winner']} {latest['margin']}"
            )

    # Most one-sided (highest win ratio for dominant team, min 5 matches)
    def one_sided_score(rec):
        total_decisive = rec["team1Wins"] + rec["team2Wins"]
        if total_decisive == 0:
            return 0
        dominant = max(rec["team1Wins"], rec["team2Wins"])
        return dominant / total_decisive

    eligible = [r for r in h2h.values() if r["totalMatches"] >= 5]
    if eligible:
        most_onesided = max(eligible, key=one_sided_score)
        dominant_team = (
            most_onesided["team1"]
            if most_onesided["team1Wins"] >= most_onesided["team2Wins"]
            else most_onesided["team2"]
        )
        dominant_wins = max(
            most_onesided["team1Wins"], most_onesided["team2Wins"]
        )
        other_wins = min(
            most_onesided["team1Wins"], most_onesided["team2Wins"]
        )
        print(
            f"\nMost one-sided rivalry (min 5 matches): "
            f"{most_onesided['team1']} vs {most_onesided['team2']}"
        )
        leagues_str = ", ".join(most_onesided["leagues"])
        print(
            f"  {dominant_team} leads {dominant_wins}-{other_wins} "
            f"({one_sided_score(most_onesided)*100:.0f}% win rate)"
            f" [{leagues_str}]"
        )

    # Highest average scoring
    highest_avg = max(h2h.values(), key=lambda r: r["avgScore"])
    print(
        f"\nHighest average scoring rivalry: "
        f"{highest_avg['team1']} vs {highest_avg['team2']}"
    )
    print(f"  Average innings score: {highest_avg['avgScore']}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    h2h = process_all_matches()

    # Sort by key for consistent output
    h2h_sorted = dict(sorted(h2h.items()))

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(h2h_sorted, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {OUT_FILE} ({os.path.getsize(OUT_FILE) / 1024:.1f} KB)")

    print_summary(h2h_sorted)


if __name__ == "__main__":
    main()
