"""
Fetch live IPL standings and (best-effort) bookmaker odds.

USAGE:
    python scripts/fetch_live_odds.py

WHAT WORKS:
    - Standings from Wikipedia (public, reliable, no auth required)

WHAT DOESN'T WORK (as of April 2026):
    - ESPNCricinfo, IPL official site, myKhel: return 403 Forbidden to
      non-browser user agents.
    - Oddschecker, Oddsportal, Goal.com: odds are rendered via JavaScript
      and not present in the initial HTML.
    - Polymarket, Kalshi: require JS rendering for market prices.

FOR RELIABLE ODDS: sign up for The Odds API (free 500 req/mo tier) at
    https://the-odds-api.com/ and set ODDS_API_KEY in your environment.
    Endpoint: /v4/sports/cricket_ipl/odds/?markets=outrights

This script currently:
    1. Scrapes standings from Wikipedia (works)
    2. Attempts The Odds API if ODDS_API_KEY is set
    3. Falls back to printing an instructional message for manual odds entry
    4. Writes standings into data/processed/odds.json preserving existing
       team-level model probabilities and reasoning
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
ODDS_FILE = os.path.join(PROCESSED_DIR, "odds.json")
WIKI_URL = "https://en.wikipedia.org/wiki/2026_Indian_Premier_League"

TEAM_CODES = {
    "Rajasthan Royals": "RR",
    "Royal Challengers Bengaluru": "RCB",
    "Punjab Kings": "PBKS",
    "Delhi Capitals": "DC",
    "Lucknow Super Giants": "LSG",
    "Sunrisers Hyderabad": "SRH",
    "Gujarat Titans": "GT",
    "Mumbai Indians": "MI",
    "Kolkata Knight Riders": "KKR",
    "Chennai Super Kings": "CSK",
}


def fetch_wikipedia_html():
    """Fetch Wikipedia's IPL 2026 page HTML with a realistic UA."""
    req = urllib.request.Request(
        WIKI_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/122.0 Safari/537.36"
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def parse_standings_from_wiki(html: str):
    """
    Very lightweight HTML scraper for Wikipedia's points table.
    Wikipedia's table markup is stable enough that regex is acceptable here.
    Returns dict: team_code -> {played, won, lost, noResult, points, nrr}
    """
    standings = {}
    for full_name, code in TEAM_CODES.items():
        # Find the team row and pull the nearest numeric cells.
        # Wikipedia wraps team names in links, then has <td>P</td><td>W</td>...
        pattern = re.compile(
            rf'>{re.escape(full_name)}</a>\s*</th>\s*'
            r'<td[^>]*>\s*(\d+)\s*</td>\s*'    # Played
            r'<td[^>]*>\s*(\d+)\s*</td>\s*'    # Won
            r'<td[^>]*>\s*(\d+)\s*</td>\s*'    # Lost
            r'<td[^>]*>\s*(\d+)\s*</td>\s*'    # NR
            r'<td[^>]*>\s*(\d+)\s*</td>\s*'    # Points
            r'<td[^>]*>\s*([+\-\u2212]?\d+\.\d+)\s*</td>',  # NRR
            re.DOTALL,
        )
        m = pattern.search(html)
        if not m:
            continue
        played, won, lost, nr, points, nrr = m.groups()
        standings[code] = {
            "played": int(played),
            "won": int(won),
            "lost": int(lost),
            "noResult": int(nr),
            "points": int(points),
            "nrr": float(nrr.replace("\u2212", "-")),
        }
    return standings


def fetch_odds_api():
    """Fetch outright odds from The Odds API if ODDS_API_KEY is set."""
    key = os.environ.get("ODDS_API_KEY")
    if not key:
        return None
    url = (
        "https://api.the-odds-api.com/v4/sports/cricket_ipl/odds"
        f"?apiKey={key}&regions=uk&markets=outrights&oddsFormat=decimal"
    )
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        print(f"  The Odds API request failed: {e}", file=sys.stderr)
        return None


def main():
    print("Fetching IPL 2026 data...")

    # 1. Standings from Wikipedia
    try:
        html = fetch_wikipedia_html()
        standings = parse_standings_from_wiki(html)
        print(f"  Wikipedia standings: {len(standings)}/10 teams parsed")
    except Exception as e:
        print(f"  ERROR fetching Wikipedia: {e}", file=sys.stderr)
        standings = {}

    # 2. Odds from The Odds API (optional)
    odds_api_data = fetch_odds_api()
    if odds_api_data:
        print("  The Odds API: data received")
    else:
        print("  The Odds API: not configured or unavailable")
        print("  (Set ODDS_API_KEY env var to enable — free tier at https://the-odds-api.com)")

    # 3. Merge into existing odds.json, preserving model probs and reasoning
    if not os.path.exists(ODDS_FILE):
        print(f"  ERROR: {ODDS_FILE} does not exist — cannot merge", file=sys.stderr)
        sys.exit(1)

    with open(ODDS_FILE, "r", encoding="utf-8") as f:
        odds = json.load(f)

    if standings:
        updated = 0
        for entry in odds.get("tournamentWinner", []):
            code = entry["team"]
            if code in standings:
                entry["record"] = standings[code]
                updated += 1
        odds["lastUpdated"] = datetime.now(timezone.utc).isoformat()
        print(f"  Updated {updated} team records in odds.json")

        with open(ODDS_FILE, "w", encoding="utf-8") as f:
            json.dump(odds, f, indent=2, ensure_ascii=False)
        print("  Wrote standings to odds.json")
    else:
        print("  No standings to write — odds.json unchanged")

    print("\nDone.")
    print("\nNOTE: Model probabilities and bookmaker odds are NOT automatically")
    print("refreshed by this script. Update them manually in odds.json or wire")
    print("up The Odds API for automated odds.")


if __name__ == "__main__":
    main()
