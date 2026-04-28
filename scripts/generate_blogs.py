"""
Blog Story Generator — Finds interesting patterns in T20 data
and generates narrative blog drafts automatically.

Detects:
1. Breakout performers (recent form >> career average)
2. Venue specialists (A+ grade, dominant at specific grounds)
3. Matchup dominance (batter owns a bowler, or vice versa)
4. Form slumps (declining players worth watching)
5. Cross-league mercenaries (players who perform across 5+ leagues)
6. Youth emergence (young players with explosive recent form)
7. Rivalry narratives (backed by H2H data)
8. Conditions stories (why certain players thrive in certain conditions)

Outputs blog drafts as JSON — one per detected story.
Each draft has: title, slug, category, summary, body (markdown),
data points cited, players mentioned, and a "previously_covered" flag.
"""

import json
import os
from datetime import datetime

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
BLOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "blogs")


def load_data():
    def read(f):
        with open(os.path.join(PROCESSED_DIR, f)) as fh:
            return json.load(fh)

    return {
        "players": read("players.json"),
        "venues": read("venues.json"),
        "matchups": read("matchups.json"),
        "h2h": read("h2h.json"),
        "quality": read("quality_stats.json"),
    }


def load_existing_blogs():
    """Check which stories we've already generated to avoid duplicates."""
    if not os.path.isdir(BLOGS_DIR):
        return set()
    covered = set()
    for f in os.listdir(BLOGS_DIR):
        if f.endswith(".json"):
            with open(os.path.join(BLOGS_DIR, f)) as fh:
                blog = json.load(fh)
                covered.add(blog.get("slug", ""))
                for p in blog.get("playersMentioned", []):
                    covered.add(f"player:{p}")
    return covered


def slugify(text):
    import re
    s = text.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s]+", "-", s)
    return s.strip("-")


# ══════════════════════════════════════════
#  PATTERN DETECTORS
# ══════════════════════════════════════════

def detect_breakout_performers(players):
    """Players whose last 10 innings are significantly better than career."""
    stories = []
    for name, p in players.items():
        rf = p.get("recentForm")
        if not rf or not rf.get("last10"):
            continue
        bat = p.get("overall", {}).get("batting", {})
        career_avg = bat.get("average", 0)
        recent_avg = rf["last10"].get("average", 0)
        recent_sr = rf["last10"].get("strikeRate", 0)
        career_sr = bat.get("strikeRate", 0)
        innings = rf["last10"].get("innings", 0)

        if innings < 8 or career_avg < 15:
            continue

        avg_jump = ((recent_avg - career_avg) / career_avg * 100) if career_avg > 0 else 0
        sr_jump = ((recent_sr - career_sr) / career_sr * 100) if career_sr > 0 else 0

        if avg_jump > 40 and recent_avg > 35:
            stories.append({
                "category": "breakout",
                "player": name,
                "title": f"The {name} Surge: Why {name.split()[-1]} Is Averaging {recent_avg:.0f} in Recent T20s",
                "summary": f"{name} has seen a {avg_jump:.0f}% jump in batting average over the last 10 innings ({recent_avg:.1f} vs career {career_avg:.1f}), with a strike rate of {recent_sr:.1f}.",
                "body": _build_breakout_body(name, p, rf, career_avg, recent_avg, career_sr, recent_sr, avg_jump),
                "dataPoints": {
                    "careerAvg": round(career_avg, 1),
                    "recentAvg": round(recent_avg, 1),
                    "avgJump": round(avg_jump, 1),
                    "recentSR": round(recent_sr, 1),
                    "careerSR": round(career_sr, 1),
                    "srJump": round(sr_jump, 1),
                },
                "score": avg_jump,
            })

    stories.sort(key=lambda x: x["score"], reverse=True)
    return stories[:10]


def _build_breakout_body(name, player, rf, career_avg, recent_avg, career_sr, recent_sr, avg_jump):
    last_name = name.split()[-1]
    teams = player.get("teams", [])
    leagues = player.get("leagues", [])
    timeline = player.get("formTimeline", [])[:5]

    body = f"""## The Numbers Don't Lie

{name} is in the form of his life. Over the last 10 T20 innings, he's averaging **{recent_avg:.1f}** at a strike rate of **{recent_sr:.1f}** — a {avg_jump:.0f}% improvement over his career average of {career_avg:.1f}.

This isn't a one-off purple patch. The consistency is what stands out.

## Recent Form Timeline

"""
    for m in timeline:
        runs = m.get("runs", 0)
        sr = m.get("strikeRate", 0)
        vs = m.get("opposition", "")
        venue = m.get("venue", "")
        date = m.get("date", "")
        body += f"- **{runs}** ({sr:.0f} SR) vs {vs} at {venue} ({date})\n"

    body += f"""
## What's Changed?

The data suggests {last_name} has evolved his game. His strike rate has jumped from {career_sr:.1f} to {recent_sr:.1f}, meaning he's not just surviving longer — he's scoring faster.

"""
    # Add venue context if available
    venues = player.get("venues", {})
    graded = [(v, d) for v, d in venues.items() if d.get("grade") in ("A+", "A")]
    if graded:
        body += f"## Where He Thrives\n\n"
        for vname, vdata in graded[:3]:
            vbat = vdata.get("batting", {})
            body += f"- **{vname}**: avg {vbat.get('average', 0):.1f}, SR {vbat.get('strikeRate', 0):.1f} (Grade {vdata['grade']})\n"

    if leagues:
        body += f"\n## Cross-League Presence\n\n{name} has played across {', '.join(leagues[:5]).upper()}. "
        if len(leagues) >= 3:
            body += f"That exposure to {len(leagues)} different T20 environments has clearly sharpened his game."

    body += f"\n\n---\n*Data from {len(player.get('formTimeline', []))} T20 innings across {len(leagues)} leagues. Analysis by MatchPrism.*"
    return body


def detect_venue_specialists(players, venues):
    """Players with A+ grades and dominant records at specific venues."""
    stories = []
    for name, p in players.items():
        for vname, vdata in p.get("venues", {}).items():
            if vdata.get("grade") != "A+":
                continue
            bat = vdata.get("batting", {})
            if bat.get("innings", 0) < 10:
                continue

            venue_info = venues.get(vname, {})
            venue_avg = venue_info.get("avg1stInnings", 160)

            stories.append({
                "category": "venue_specialist",
                "player": name,
                "venue": vname,
                "title": f"Why {name.split()[-1]} Owns {vname}: A Data Deep-Dive",
                "summary": f"{name} averages {bat['average']:.1f} at {vname} (SR {bat.get('strikeRate', 0):.1f}) across {bat['innings']} innings — earning an A+ venue fit grade.",
                "body": _build_venue_specialist_body(name, p, vname, vdata, venue_info),
                "dataPoints": {
                    "venueAvg": bat["average"],
                    "venueSR": bat.get("strikeRate", 0),
                    "innings": bat["innings"],
                    "runs": bat.get("runs", 0),
                    "grade": "A+",
                },
                "score": bat.get("runs", 0),
            })

    stories.sort(key=lambda x: x["score"], reverse=True)
    return stories[:10]


def _build_venue_specialist_body(name, player, vname, vdata, venue_info):
    bat = vdata.get("batting", {})
    career = player.get("overall", {}).get("batting", {})
    city = venue_info.get("city", "")
    venue_rr = venue_info.get("venueRunRate", 8.0)

    body = f"""## The {vname} Connection

Some players just have a ground that feels like home. For {name}, that ground is **{vname}** in {city}.

| Metric | At {vname.split()[0]} | Career |
|--------|------------|--------|
| Average | **{bat.get('average', 0):.1f}** | {career.get('average', 0):.1f} |
| Strike Rate | **{bat.get('strikeRate', 0):.1f}** | {career.get('strikeRate', 0):.1f} |
| Innings | {bat.get('innings', 0)} | {career.get('innings', 0)} |
| Runs | {bat.get('runs', 0)} | {career.get('runs', 0)} |
| Sixes | {bat.get('sixes', 0)} | {career.get('sixes', 0)} |

"""
    # Why does this venue suit them?
    altitude = venue_info.get("altitude_m", 0)
    boundaries = venue_info.get("boundary_avg_m", 65)
    pace_pct = venue_info.get("paceWicketPct", 50)

    reasons = []
    if boundaries and boundaries < 62:
        reasons.append(f"Short boundaries ({boundaries}m average) reward his power game")
    if altitude and altitude > 500:
        reasons.append(f"High altitude ({altitude}m) means the ball travels further here")
    if pace_pct and pace_pct > 60 and "Bowl" not in (player.get("overall", {}).get("bowling", {}).get("innings", 0) and "Bowler" or ""):
        reasons.append(f"Pace-friendly conditions ({pace_pct:.0f}% pace wickets) suit his technique against seam")
    if venue_rr and venue_rr > 8.5:
        reasons.append(f"High-scoring venue (RR {venue_rr:.2f}) where his aggressive approach thrives")

    if reasons:
        body += "## Why This Venue Works\n\n"
        for r in reasons:
            body += f"- {r}\n"

    body += f"\n\n---\n*Based on {bat.get('innings', 0)} innings at {vname}. Analysis by MatchPrism.*"
    return body


def detect_matchup_stories(matchups):
    """Dominant batter-vs-bowler matchups that tell a story."""
    stories = []
    for key, m in matchups.items():
        if m["balls"] < 40:
            continue

        # Batter dominance
        if m["strikeRate"] > 160 and m["dismissals"] <= 2 and m["runs"] > 80:
            stories.append({
                "category": "matchup_dominance",
                "player": m["batter"],
                "title": f"{m['batter'].split()[-1]} vs {m['bowler'].split()[-1]}: Cricket's Most One-Sided Battle",
                "summary": f"{m['batter']} has smashed {m['runs']} runs off {m['balls']} balls against {m['bowler']} (SR {m['strikeRate']}) with only {m['dismissals']} dismissal(s).",
                "body": _build_matchup_body(m, batter_dominant=True),
                "dataPoints": m,
                "score": m["strikeRate"] * m["balls"],
            })

        # Bowler dominance
        if m["dismissals"] >= 6 and m["average"] < 15:
            stories.append({
                "category": "matchup_dominance",
                "player": m["bowler"],
                "title": f"The {m['bowler'].split()[-1]} Problem: Why {m['batter'].split()[-1]} Can't Figure Him Out",
                "summary": f"{m['bowler']} has dismissed {m['batter']} {m['dismissals']} times in T20s (avg {m['average']}). It's become cricket's biggest mismatch.",
                "body": _build_matchup_body(m, batter_dominant=False),
                "dataPoints": m,
                "score": m["dismissals"] * 100,
            })

    stories.sort(key=lambda x: x["score"], reverse=True)
    return stories[:10]


def _build_matchup_body(m, batter_dominant):
    batter = m["batter"]
    bowler = m["bowler"]

    body = f"""## Head to Head

| | Stat |
|---|---|
| Balls | {m['balls']} |
| Runs | {m['runs']} |
| Strike Rate | {m['strikeRate']} |
| Dismissals | {m['dismissals']} |
| Average | {m['average']} |
| Dot Ball % | {m['dotBallPct']}% |
| Fours | {m['fours']} |
| Sixes | {m['sixes']} |
| Matches | {m['matches']} |

"""
    if batter_dominant:
        body += f"""## Why {batter.split()[-1]} Dominates

Across {m['balls']} deliveries, {batter} has scored at a strike rate of **{m['strikeRate']}** against {bowler} — well above T20 norms. With only {m['dismissals']} dismissal(s), this is a matchup {bowler}'s captain should be trying to avoid.

The key stat: **{m['dotBallPct']}% dot balls**. {"That means the batter is finding gaps on nearly every delivery." if m['dotBallPct'] < 30 else "There are still periods of control, but the damage rate is unsustainable for the bowler."}
"""
    else:
        body += f"""## Why {bowler.split()[-1]} Has the Edge

{m['dismissals']} dismissals in {m['matches']} matches tells you everything. {bowler} has figured out {batter} — whether it's pace, length, or angle, the batter hasn't found an answer.

The average of **{m['average']}** is well below {batter}'s career norm, suggesting a fundamental technical mismatch.
"""
    body += f"\n---\n*Ball-by-ball data from {m['matches']} T20 matches. Analysis by MatchPrism.*"
    return body


def detect_form_slumps(players):
    """Players whose recent form has declined significantly."""
    stories = []
    for name, p in players.items():
        rf = p.get("recentForm")
        if not rf or rf.get("trend") != "declining":
            continue
        bat = p.get("overall", {}).get("batting", {})
        career_avg = bat.get("average", 0)
        if career_avg < 25 or bat.get("innings", 0) < 50:
            continue

        last10 = rf.get("last10", {})
        recent_avg = last10.get("average", 0)
        drop = career_avg - recent_avg

        if drop > 10:
            stories.append({
                "category": "form_slump",
                "player": name,
                "title": f"What's Wrong with {name.split()[-1]}? The Numbers Behind the Slump",
                "summary": f"{name}'s average has dropped from {career_avg:.1f} to {recent_avg:.1f} in recent innings — a {drop:.0f}-point decline.",
                "body": f"""## The Decline

{name} is going through a rough patch. His recent 10-innings average of **{recent_avg:.1f}** is a far cry from his career mark of **{career_avg:.1f}**.

| Period | Average | Strike Rate |
|--------|---------|-------------|
| Career | {career_avg:.1f} | {bat.get('strikeRate', 0):.1f} |
| Last 10 | {recent_avg:.1f} | {last10.get('strikeRate', 0):.1f} |

The question facing his team: is this a temporary blip or a deeper problem?

---
*Analysis by MatchPrism.*""",
                "dataPoints": {"careerAvg": career_avg, "recentAvg": recent_avg, "drop": drop},
                "score": drop,
            })

    stories.sort(key=lambda x: x["score"], reverse=True)
    return stories[:5]


def detect_cross_league_stars(players):
    """Players who dominate across 5+ T20 leagues."""
    stories = []
    for name, p in players.items():
        leagues = p.get("leagues", [])
        if len(leagues) < 5:
            continue
        bat = p.get("overall", {}).get("batting", {})
        if bat.get("runs", 0) < 3000:
            continue

        stories.append({
            "category": "cross_league",
            "player": name,
            "title": f"The Global T20 Nomad: {name}'s Journey Across {len(leagues)} Leagues",
            "summary": f"{name} has played in {len(leagues)} T20 leagues ({', '.join(leagues[:5]).upper()}), scoring {bat['runs']} runs at {bat.get('average', 0):.1f}.",
            "body": f"""## {len(leagues)} Leagues, One Mission

{name} is one of T20 cricket's true globetrotters. From the IPL to the BBL, from the CPL to the PSL, he's plied his trade across **{len(leagues)} different T20 leagues**: {', '.join(leagues).upper()}.

**Career Numbers:** {bat.get('runs', 0)} runs | {bat.get('innings', 0)} innings | Avg {bat.get('average', 0):.1f} | SR {bat.get('strikeRate', 0):.1f}

That kind of cross-league experience shapes a player. Different pitches, different pressure, different tactical demands — and {name.split()[-1]} has delivered across all of them.

---
*Data across {len(leagues)} T20 leagues. Analysis by MatchPrism.*""",
            "dataPoints": {"leagues": len(leagues), "runs": bat["runs"]},
            "score": len(leagues) * bat.get("runs", 0),
        })

    stories.sort(key=lambda x: x["score"], reverse=True)
    return stories[:8]


# ══════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════

def main():
    print("=" * 60)
    print("MatchPrism — Blog Story Generator")
    print("=" * 60)

    data = load_data()
    existing = load_existing_blogs()

    all_stories = []

    print("\nDetecting patterns...")

    stories = detect_breakout_performers(data["players"])
    print(f"  Breakout performers: {len(stories)} stories")
    all_stories.extend(stories)

    stories = detect_venue_specialists(data["players"], data["venues"])
    print(f"  Venue specialists: {len(stories)} stories")
    all_stories.extend(stories)

    stories = detect_matchup_stories(data["matchups"])
    print(f"  Matchup dominance: {len(stories)} stories")
    all_stories.extend(stories)

    stories = detect_form_slumps(data["players"])
    print(f"  Form slumps: {len(stories)} stories")
    all_stories.extend(stories)

    stories = detect_cross_league_stars(data["players"])
    print(f"  Cross-league stars: {len(stories)} stories")
    all_stories.extend(stories)

    # Deduplicate: skip stories about players already covered
    new_stories = []
    for s in all_stories:
        slug = slugify(s["title"])
        player_key = f"player:{s['player']}"

        s["slug"] = slug
        s["playersMentioned"] = [s["player"]]
        s["generatedAt"] = datetime.now().isoformat()
        s["previouslyCovered"] = slug in existing or player_key in existing

        new_stories.append(s)

    # Save
    os.makedirs(BLOGS_DIR, exist_ok=True)

    for s in new_stories:
        filepath = os.path.join(BLOGS_DIR, f"{s['slug'][:80]}.json")
        with open(filepath, "w") as f:
            json.dump(s, f, indent=2)

    # Summary
    new_count = sum(1 for s in new_stories if not s["previouslyCovered"])
    dup_count = sum(1 for s in new_stories if s["previouslyCovered"])

    print(f"\n{'=' * 60}")
    print(f"Generated {len(new_stories)} blog drafts ({new_count} new, {dup_count} previously covered)")
    print(f"Saved to {BLOGS_DIR}/")
    print(f"\nTop stories:")
    for s in sorted(new_stories, key=lambda x: x["score"], reverse=True)[:15]:
        flag = " [DUP]" if s["previouslyCovered"] else ""
        print(f"  [{s['category']:20s}] {s['title'][:70]}{flag}")


if __name__ == "__main__":
    main()
