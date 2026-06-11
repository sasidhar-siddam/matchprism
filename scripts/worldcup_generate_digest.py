"""
Generate the World Cup editorial digest with a single headless Claude call.

USAGE:
    python scripts/worldcup_generate_digest.py            # uses claude -p (one call)
    python scripts/worldcup_generate_digest.py --no-llm   # rule-based fallback only
    python scripts/worldcup_generate_digest.py --model opus

COST:
    Exactly ONE `claude -p` invocation per run, billed to your Claude Code
    plan (no OpenAI / Gemini keys involved). Input is pre-trimmed: headline
    titles only, today's + tomorrow's fixtures only. Default model: sonnet.

INPUT:   data/processed/worldcup/schedule.json, news.json
OUTPUT:  data/processed/worldcup/digest.json
"""

import json
import os
import re
import subprocess
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from datetime import datetime, timedelta, timezone

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "worldcup")
SCHEDULE_FILE = os.path.join(PROCESSED_DIR, "schedule.json")
NEWS_FILE = os.path.join(PROCESSED_DIR, "news.json")
OUT_FILE = os.path.join(PROCESSED_DIR, "digest.json")

MAX_HEADLINES = 30
MAX_PREVIEW_MATCHES = 8


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def upcoming_window(schedule):
    """Today's and tomorrow's matches (UTC), capped."""
    today = datetime.now(timezone.utc).date()
    window = {today.isoformat(), (today + timedelta(days=1)).isoformat()}
    return [m for m in schedule["matches"] if m["dateRaw"] in window][:MAX_PREVIEW_MATCHES]


def recent_results(schedule, limit=10):
    played = [m for m in schedule["matches"] if m["status"] == "played"]
    return played[-limit:]


def build_prompt(schedule, news):
    matches = upcoming_window(schedule)
    results = recent_results(schedule)
    headlines = news["items"][:MAX_HEADLINES] if news else []

    lines = [
        "You are the editorial engine for MatchPrism, a sports analytics site.",
        "Tone: data-driven, neutral, analytics-first. Never use betting or gambling language.",
        "",
        "## Upcoming matches (UTC):",
    ]
    for m in matches:
        grp = f" ({m['group']})" if m["group"] else f" ({m['stage']})"
        lines.append(f"- match {m['matchNumber']} | {m['slug']} | {m['homeTeam']} vs {m['awayTeam']}{grp} | {m['date']} {m['time']} | {m['venue']}")
    lines.append("")
    if results:
        lines.append("## Recent results:")
        for m in results:
            lines.append(f"- {m['homeTeam']} {m['homeScore']}-{m['awayScore']} {m['awayTeam']} ({m['group'] or m['stage']})")
        lines.append("")
    if headlines:
        lines.append("## Latest headlines (index | source | title):")
        for i, h in enumerate(headlines):
            lines.append(f"{i} | {h['source']} | {h['title']}")
    lines += [
        "",
        "Respond with ONLY a JSON object, no markdown fences, matching exactly:",
        "{",
        '  "dailyBrief": "2-3 sentence summary of where the tournament stands today",',
        '  "topStoryIndices": [up to 6 integer indices of the most important headlines above, most important first],',
        '  "matchPreviews": [for EACH upcoming match listed above: {"matchNumber": int, "slug": str, "headline": "short punchy preview title", "preview": "2-3 sentence analytical preview", "keyFact": "one concrete stat or storyline"}]',
        "}",
    ]
    return "\n".join(lines)


def call_claude(prompt: str, model: str):
    """One headless claude -p call; prompt passed via stdin to avoid cmdline limits."""
    result = subprocess.run(
        ["claude", "-p", "--model", model, "--output-format", "json"],
        input=prompt, capture_output=True, text=True, encoding="utf-8",
        timeout=300, shell=(os.name == "nt"),
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude -p failed: {result.stderr[:500]}")
    envelope = json.loads(result.stdout)
    text = envelope.get("result", "")
    # Strip accidental code fences before parsing
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    return json.loads(text)


def fallback_digest(schedule, news):
    """Rule-based digest when --no-llm is set or the claude call fails."""
    matches = upcoming_window(schedule)
    played = schedule["playedMatches"]
    brief = (
        f"World Cup 2026: {played} of {schedule['totalMatches']} matches played. "
        f"Next up: " + ", ".join(f"{m['homeTeam']} vs {m['awayTeam']}" for m in matches[:3]) + "."
        if matches else f"World Cup 2026: {played} of {schedule['totalMatches']} matches played."
    )
    return {
        "dailyBrief": brief,
        "topStoryIndices": list(range(min(6, len(news["items"])))) if news else [],
        "matchPreviews": [
            {
                "matchNumber": m["matchNumber"],
                "slug": m["slug"],
                "headline": f"{m['homeTeam']} vs {m['awayTeam']}",
                "preview": f"{m['stage']}{' · ' + m['group'] if m['group'] else ''} fixture at {m['venue']}, {m['date']} {m['time']}.",
                "keyFact": f"Match {m['matchNumber']} of 104.",
            }
            for m in matches
        ],
        "generator": "rule-based",
    }


def main():
    use_llm = "--no-llm" not in sys.argv
    model = "sonnet"
    if "--model" in sys.argv:
        model = sys.argv[sys.argv.index("--model") + 1]

    schedule = load_json(SCHEDULE_FILE)
    news = load_json(NEWS_FILE)
    if not schedule:
        print("ERROR: run worldcup_fetch_fixtures.py first.")
        sys.exit(1)

    digest = None
    if use_llm:
        prompt = build_prompt(schedule, news)
        print(f"Calling claude -p (model={model}, ~{len(prompt)} chars input, 1 call) ...")
        try:
            digest = call_claude(prompt, model)
            digest["generator"] = f"claude-{model}"
        except Exception as e:
            print(f"  claude call failed ({e}); using rule-based fallback.")
    if digest is None:
        digest = fallback_digest(schedule, news)

    # Resolve headline indices into full story objects
    items = news["items"] if news else []
    top_stories = []
    for idx in digest.pop("topStoryIndices", []):
        if isinstance(idx, int) and 0 <= idx < len(items):
            top_stories.append(items[idx])
    digest["topStories"] = top_stories
    digest["generatedAt"] = datetime.now(timezone.utc).isoformat()

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(digest, f, indent=2, ensure_ascii=False)
    print(f"Wrote digest ({digest['generator']}, {len(top_stories)} top stories, "
          f"{len(digest.get('matchPreviews', []))} previews) to {OUT_FILE}")


if __name__ == "__main__":
    main()
