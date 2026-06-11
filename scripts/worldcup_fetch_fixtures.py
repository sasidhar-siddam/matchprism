"""
Fetch the FIFA World Cup 2026 fixture list (all 104 matches).

USAGE:
    python scripts/worldcup_fetch_fixtures.py

SOURCE:
    fixturedownload.com free JSON feed — no API key required.
    Scores populate in the feed as matches are played, so re-running this
    script during the tournament refreshes results too.

OUTPUT:
    data/processed/worldcup/schedule.json
"""

import json
import os
import re
import urllib.request
from datetime import datetime, timezone

FEED_URL = "https://fixturedownload.com/feed/json/fifa-world-cup-2026"
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "worldcup")
OUT_FILE = os.path.join(PROCESSED_DIR, "schedule.json")


def stage_for_match(match_number: int) -> str:
    """104-match format: 72 group + 16 R32 + 8 R16 + 4 QF + 2 SF + bronze + final."""
    if match_number <= 72:
        return "Group Stage"
    if match_number <= 88:
        return "Round of 32"
    if match_number <= 96:
        return "Round of 16"
    if match_number <= 100:
        return "Quarter-final"
    if match_number <= 102:
        return "Semi-final"
    if match_number == 103:
        return "Third Place"
    return "Final"


def slugify(text: str) -> str:
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", text.lower()))


def fetch_fixtures():
    req = urllib.request.Request(
        FEED_URL,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def clean_team(name: str) -> str:
    """Feed uses 'To be announced' for unresolved knockout slots."""
    return "TBD" if name.strip().lower() == "to be announced" else name.strip()


def transform(raw):
    matches = []
    for m in raw:
        dt = datetime.strptime(m["DateUtc"], "%Y-%m-%d %H:%M:%SZ").replace(tzinfo=timezone.utc)
        home, away = clean_team(m["HomeTeam"]), clean_team(m["AwayTeam"])
        played = m["HomeTeamScore"] is not None and m["AwayTeamScore"] is not None
        matches.append({
            "matchNumber": m["MatchNumber"],
            "slug": f"m{m['MatchNumber']}-{slugify(home)}-vs-{slugify(away)}",
            "stage": stage_for_match(m["MatchNumber"]),
            "matchday": m["RoundNumber"] if m["MatchNumber"] <= 72 else None,
            "group": m.get("Group"),
            "dateRaw": dt.strftime("%Y-%m-%d"),
            "date": dt.strftime("%a, %b %d"),
            "time": dt.strftime("%H:%M UTC"),
            "homeTeam": home,
            "awayTeam": away,
            "venue": m["Location"],
            "city": re.sub(r"\s+Stadium$", "", m["Location"]),
            "homeScore": m["HomeTeamScore"],
            "awayScore": m["AwayTeamScore"],
            "winner": m.get("Winner") or None,
            "status": "played" if played else "upcoming",
        })
    matches.sort(key=lambda x: x["matchNumber"])
    return matches


def main():
    print(f"Fetching fixtures from {FEED_URL} ...")
    try:
        raw = fetch_fixtures()
        if not isinstance(raw, list) or len(raw) < 50:
            raise ValueError(f"feed returned {len(raw) if isinstance(raw, list) else 'non-list'} matches, expected 104")
    except Exception as e:
        # Never clobber good data with a failed fetch: fixtures are static
        # after the draw, so the last good schedule.json remains valid
        # (scores just go stale until the feed recovers).
        if os.path.exists(OUT_FILE):
            print(f"WARNING: fetch failed ({e}); keeping existing {OUT_FILE}")
            return
        raise
    matches = transform(raw)
    played = sum(1 for m in matches if m["status"] == "played")
    groups = sorted({m["group"] for m in matches if m["group"]})

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    payload = {
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "source": "fixturedownload.com",
        "totalMatches": len(matches),
        "playedMatches": played,
        "groups": groups,
        "matches": matches,
    }
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(matches)} matches ({played} played) to {OUT_FILE}")
    print(f"Groups: {', '.join(groups)}")


if __name__ == "__main__":
    main()
