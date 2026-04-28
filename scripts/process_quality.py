"""
Quality Intelligence — Venue-adjusted + Opposition-quality-adjusted stats.

Instead of crude league tiers, this measures quality the right way:

1. VENUE-ADJUSTED: Compare every performance to the venue baseline.
   - Bumrah econ 7.0 at Chinnaswamy (venue RR 8.74) = -20% = ELITE
   - Bumrah econ 7.0 at Chepauk (venue RR 7.8) = -10% = GOOD

2. OPPOSITION QUALITY: Based on actual career stats of opponents faced.
   - Dismissing batters who average 35+ = high-quality wickets
   - Scoring at 150 SR against bowlers with econ < 7.0 = high-quality runs

3. VENUE FIT GRADE (improved): Uses venue-adjusted stats, not raw stats.
"""

import json
import os
from collections import defaultdict

from venue_map import normalize_venue

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")


def load_existing():
    """Load pre-computed data."""
    with open(os.path.join(PROCESSED_DIR, "venues.json")) as f:
        venues = json.load(f)
    with open(os.path.join(PROCESSED_DIR, "players.json")) as f:
        players = json.load(f)
    with open(os.path.join(PROCESSED_DIR, "matchups.json")) as f:
        matchups = json.load(f)
    return venues, players, matchups


def compute_venue_adjusted(players, venues):
    """
    For each player at each venue, compute how they performed
    RELATIVE to that venue's baseline.
    """
    output = {}

    for player_name, player in players.items():
        venue_adj = {}
        for venue_name, vs in player.get("venues", {}).items():
            venue_data = venues.get(venue_name, {})
            venue_rr = venue_data.get("venueRunRate", 0)
            venue_avg_score = venue_data.get("avg1stInnings", 0)
            venue_avg_wickets = venue_data.get("avgWicketsPerInnings", 0)

            # Batting: compare SR to venue run rate
            bat = vs.get("batting", {})
            if bat.get("innings", 0) >= 3 and bat.get("strikeRate", 0) > 0 and venue_rr > 0:
                # Expected SR at this venue (venue RR * 100 / 6)
                venue_sr = venue_rr * 100 / 6
                sr_vs_venue = round((bat["strikeRate"] / venue_sr - 1) * 100, 1)
                # Expected average: venue avg total / avg wickets per innings
                venue_bat_avg = venue_avg_score / venue_avg_wickets if venue_avg_wickets > 0 else 30
                avg_vs_venue = round((bat["average"] / venue_bat_avg - 1) * 100, 1)
            else:
                sr_vs_venue = None
                avg_vs_venue = None

            # Bowling: compare economy to venue run rate
            bowl = vs.get("bowling", {})
            if bowl.get("innings", 0) >= 3 and bowl.get("economy", 0) > 0 and venue_rr > 0:
                econ_vs_venue = round((bowl["economy"] / venue_rr - 1) * 100, 1)
            else:
                econ_vs_venue = None

            # Rating
            def rate_pct(pct, inverted=False):
                if pct is None:
                    return None
                p = -pct if inverted else pct
                if p > 15:
                    return "Elite"
                elif p > 5:
                    return "Good"
                elif p > -5:
                    return "Average"
                elif p > -15:
                    return "Below Average"
                else:
                    return "Poor"

            entry = {}
            if sr_vs_venue is not None:
                entry["batting"] = {
                    "srVsVenue": sr_vs_venue,
                    "avgVsVenue": avg_vs_venue,
                    "rating": rate_pct(sr_vs_venue),
                }
            if econ_vs_venue is not None:
                entry["bowling"] = {
                    "econVsVenue": econ_vs_venue,
                    "rating": rate_pct(econ_vs_venue, inverted=True),
                }

            if entry:
                venue_adj[venue_name] = entry

        if venue_adj:
            output[player_name] = venue_adj

    return output


def compute_opposition_quality(players, matchups):
    """
    For each player, compute the average quality of opposition they've faced.

    For batters: avg career economy of bowlers they've scored against
    For bowlers: avg career batting avg of batters they've dismissed
    """
    output = {}

    # Pre-compute bowler qualities and batter qualities
    bowler_quality = {}  # bowler -> career economy
    batter_quality = {}  # batter -> career batting avg

    for name, p in players.items():
        ov = p.get("overall", {})
        bat = ov.get("batting", {})
        bowl = ov.get("bowling", {})
        if bat.get("innings", 0) >= 10 and bat.get("average", 0) > 5:
            batter_quality[name] = bat["average"]
        if bowl.get("innings", 0) >= 10 and bowl.get("economy", 0) > 0:
            bowler_quality[name] = bowl["economy"]

    # For each player, compute opposition quality from matchups
    batter_opp = defaultdict(lambda: {"total_bowler_econ": 0, "balls_vs_quality": 0,
                                       "runs_vs_quality_bowlers": 0, "balls_vs_quality_bowlers": 0,
                                       "dismissals_by_quality": 0})
    bowler_opp = defaultdict(lambda: {"total_batter_avg": 0, "dismissals_quality": 0,
                                       "runs_vs_quality_batters": 0, "balls_vs_quality_batters": 0})

    for key, m in matchups.items():
        batter = m["batter"]
        bowler = m["bowler"]
        balls = m["balls"]
        runs = m["runs"]
        dismissals = m["dismissals"]

        # Batter facing a quality bowler (econ < 8.0, 10+ career innings)
        if bowler in bowler_quality:
            be = batter_opp[batter]
            be["total_bowler_econ"] += bowler_quality[bowler] * balls
            be["balls_vs_quality"] += balls
            if bowler_quality[bowler] < 8.0:  # good bowler threshold
                be["runs_vs_quality_bowlers"] += runs
                be["balls_vs_quality_bowlers"] += balls
                be["dismissals_by_quality"] += dismissals

        # Bowler dismissing quality batters (avg > 25)
        if batter in batter_quality and dismissals > 0:
            bo = bowler_opp[bowler]
            bo["total_batter_avg"] += batter_quality[batter] * dismissals
            bo["dismissals_quality"] += dismissals
            if batter_quality[batter] > 25:  # quality batter threshold
                bo["runs_vs_quality_batters"] += runs
                bo["balls_vs_quality_batters"] += balls

    # Build per-player opposition quality scores
    for player_name in set(list(batter_opp.keys()) + list(bowler_opp.keys())):
        entry = {"name": player_name}

        # Batting opposition quality
        be = batter_opp.get(player_name)
        if be and be["balls_vs_quality"] > 50:
            avg_bowler_econ = round(be["total_bowler_econ"] / be["balls_vs_quality"], 2)
            entry["battingOpposition"] = {
                "avgBowlerEconomy": avg_bowler_econ,
                "qualityLabel": "Tough" if avg_bowler_econ < 7.5 else ("Medium" if avg_bowler_econ < 8.5 else "Easy"),
            }
            # Stats vs quality bowlers specifically (econ < 8.0)
            if be["balls_vs_quality_bowlers"] > 30:
                sr_vs_quality = round(be["runs_vs_quality_bowlers"] / be["balls_vs_quality_bowlers"] * 100, 1)
                avg_vs_quality = round(be["runs_vs_quality_bowlers"] / max(be["dismissals_by_quality"], 1), 1)
                entry["vsQualityBowlers"] = {
                    "balls": be["balls_vs_quality_bowlers"],
                    "runs": be["runs_vs_quality_bowlers"],
                    "strikeRate": sr_vs_quality,
                    "average": avg_vs_quality,
                    "dismissals": be["dismissals_by_quality"],
                }

        # Bowling opposition quality
        bo = bowler_opp.get(player_name)
        if bo and bo["dismissals_quality"] > 10:
            avg_batter_avg = round(bo["total_batter_avg"] / bo["dismissals_quality"], 1)
            entry["bowlingOpposition"] = {
                "avgDismissedBatterAvg": avg_batter_avg,
                "qualityLabel": "Elite Scalps" if avg_batter_avg > 28 else ("Good Scalps" if avg_batter_avg > 22 else "Weak Scalps"),
                "qualityDismissals": bo["dismissals_quality"],
            }
            if bo["balls_vs_quality_batters"] > 30:
                econ_vs_quality = round(bo["runs_vs_quality_batters"] / (bo["balls_vs_quality_batters"] / 6), 2)
                entry["vsQualityBatters"] = {
                    "balls": bo["balls_vs_quality_batters"],
                    "runsConceded": bo["runs_vs_quality_batters"],
                    "economy": econ_vs_quality,
                }

        if len(entry) > 1:  # has more than just name
            output[player_name] = entry

    return output


def main():
    print("=" * 60)
    print("MatchPrism - Quality Intelligence Processor")
    print("=" * 60)

    venues, players, matchups = load_existing()
    print(f"Loaded: {len(venues)} venues, {len(players)} players, {len(matchups)} matchups")

    print("\nComputing venue-adjusted stats...")
    venue_adj = compute_venue_adjusted(players, venues)
    print(f"  Players with venue adjustments: {len(venue_adj):,}")

    print("Computing opposition quality...")
    opp_quality = compute_opposition_quality(players, matchups)
    print(f"  Players with opposition data: {len(opp_quality):,}")

    # Combine into single output
    output = {
        "venueAdjusted": venue_adj,
        "oppositionQuality": opp_quality,
    }

    outpath = os.path.join(PROCESSED_DIR, "quality_stats.json")
    with open(outpath, "w") as f:
        json.dump(output, f)

    fsize = os.path.getsize(outpath)
    print(f"\nSaved to {outpath} ({fsize/1024/1024:.1f} MB)")

    # ── Samples ──
    print(f"\n{'='*60}")
    print("VENUE-ADJUSTED BOWLING (select bowlers at key venues)")
    print(f"{'='*60}")

    for bowler in ["JJ Bumrah", "Rashid Khan", "B Kumar", "YS Chahal", "Mustafizur Rahman"]:
        va = venue_adj.get(bowler, {})
        if not va:
            continue
        print(f"\n{bowler}:")
        entries = [(v, d) for v, d in va.items() if "bowling" in d]
        entries.sort(key=lambda x: x[1]["bowling"]["econVsVenue"])
        for vname, data in entries[:5]:
            b = data["bowling"]
            print(f"  {vname:35s}  econ vs venue: {b['econVsVenue']:+5.1f}%  [{b['rating']}]")
        if len(entries) > 5:
            worst = entries[-2:]
            for vname, data in worst:
                b = data["bowling"]
                print(f"  {vname:35s}  econ vs venue: {b['econVsVenue']:+5.1f}%  [{b['rating']}]")

    print(f"\n{'='*60}")
    print("OPPOSITION QUALITY (who do they dismiss / get dismissed by?)")
    print(f"{'='*60}")

    for name in ["V Kohli", "JJ Bumrah", "Rashid Khan", "KA Pollard", "Shakib Al Hasan", "GJ Maxwell"]:
        oq = opp_quality.get(name, {})
        if not oq:
            continue
        print(f"\n{name}:")
        if "battingOpposition" in oq:
            bo = oq["battingOpposition"]
            print(f"  Faces bowlers avg econ {bo['avgBowlerEconomy']} ({bo['qualityLabel']})")
        if "vsQualityBowlers" in oq:
            vq = oq["vsQualityBowlers"]
            print(f"  vs Quality Bowlers (econ<8): {vq['runs']} runs, {vq['balls']} balls, SR {vq['strikeRate']}, avg {vq['average']}, dismissed {vq['dismissals']}x")
        if "bowlingOpposition" in oq:
            bo = oq["bowlingOpposition"]
            print(f"  Dismisses batters avg {bo['avgDismissedBatterAvg']} ({bo['qualityLabel']}, {bo['qualityDismissals']} scalps)")
        if "vsQualityBatters" in oq:
            vq = oq["vsQualityBatters"]
            print(f"  vs Quality Batters (avg>25): {vq['runsConceded']} runs in {vq['balls']} balls, econ {vq['economy']}")


if __name__ == "__main__":
    main()
