"""
Generate full World Cup articles with one headless Claude call, styled by
the worldcup-article skill, with best-effort Wikimedia Commons images.

USAGE:
    python scripts/worldcup_generate_articles.py            # one claude -p call
    python scripts/worldcup_generate_articles.py --model opus
    python scripts/worldcup_generate_articles.py --count 3

COST:
    Exactly ONE `claude -p` call per run (default model: sonnet), billed to
    the Claude Code plan. Commons image lookups are free API calls.

INPUT:   data/processed/worldcup/{schedule,news,digest}.json
         .claude/skills/worldcup-article/SKILL.md  (style guide)
OUTPUT:  data/processed/worldcup/articles.json  (accumulates across runs)
"""

import html
import json
import os
import re
import subprocess
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(__file__), "..")
PROCESSED_DIR = os.path.join(ROOT, "data", "processed", "worldcup")
SKILL_FILE = os.path.join(ROOT, ".claude", "skills", "worldcup-article", "SKILL.md")
OUT_FILE = os.path.join(PROCESSED_DIR, "articles.json")

MAX_HEADLINES = 30
MAX_KEPT_ARTICLES = 60
USER_AGENT = "MatchPrism/1.0 (sports analytics; contact via github)"


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_style_guide():
    with open(SKILL_FILE, encoding="utf-8") as f:
        text = f.read()
    # Drop the frontmatter block; the body is the style guide
    return re.sub(r"^---.*?---\s*", "", text, flags=re.DOTALL)


def build_prompt(schedule, news, digest, existing_slugs, count):
    today = datetime.now(timezone.utc).date().isoformat()
    headlines = (news or {}).get("items", [])[:MAX_HEADLINES]
    played = [m for m in schedule["matches"] if m["status"] == "played"][-12:]
    upcoming = [m for m in schedule["matches"] if m["status"] == "upcoming"][:10]

    lines = [load_style_guide(), "", "=" * 60, ""]
    lines.append(f"Today (UTC): {today}. Write {count} articles for MatchPrism's World Cup section.")
    lines.append("Pick the most newsworthy angles from the data below. Mix categories")
    lines.append("(recap if there are fresh results, preview for imminent fixtures, one analysis).")
    if existing_slugs:
        lines.append(f"Already published (do NOT duplicate these angles): {', '.join(sorted(existing_slugs)[-20:])}")
    lines.append("")
    if digest:
        lines.append(f"## Tournament state:\n{digest.get('dailyBrief', '')}\n")
    if played:
        lines.append("## Recent results:")
        for m in played:
            lines.append(f"- {m['homeTeam']} {m['homeScore']}-{m['awayScore']} {m['awayTeam']} ({m['group'] or m['stage']}, {m['date']}, {m['venue']})")
        lines.append("")
    lines.append("## Upcoming fixtures (UTC):")
    for m in upcoming:
        lines.append(f"- {m['homeTeam']} vs {m['awayTeam']} ({m['group'] or m['stage']}) | {m['date']} {m['time']} | {m['venue']}")
    lines.append("")
    if headlines:
        lines.append("## Headlines (index | source | title):")
        for i, h in enumerate(headlines):
            lines.append(f"{i} | {h['source']} | {h['title']}")
    lines += [
        "",
        "Respond with ONLY a JSON object, no markdown fences:",
        "{",
        '  "articles": [',
        "    {",
        f'      "slug": "kebab-case-with-{today}-suffix",',
        '      "title": "headline per style guide",',
        '      "dek": "one-sentence subtitle with new information",',
        '      "category": "Match Preview" | "Match Recap" | "Analysis",',
        '      "imageSearch": "Wikimedia Commons search term per style guide",',
        '      "keyStats": [3-4 of {"label": "short label", "value": "short value"}],',
        '      "sections": [{"heading": "optional, may be null for the opening section", "paragraphs": ["...", "..."]}],',
        '      "sourceIndices": [headline indices actually drawn on]',
        "    }",
        "  ]",
        "}",
    ]
    return "\n".join(lines)


def call_claude(prompt: str, model: str):
    result = subprocess.run(
        ["claude", "-p", "--model", model, "--output-format", "json"],
        input=prompt, capture_output=True, text=True, encoding="utf-8",
        timeout=600, shell=(os.name == "nt"),
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude -p failed: {result.stderr[:500]}")
    envelope = json.loads(result.stdout)
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", envelope.get("result", "").strip())
    return json.loads(text)


def fetch_commons_image(search_term: str):
    """Best-effort: first usable bitmap on Wikimedia Commons with attribution."""
    params = urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": f"filetype:bitmap {search_term}", "gsrnamespace": 6, "gsrlimit": 5,
        "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 1000,
    })
    url = f"https://commons.wikimedia.org/w/api.php?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        pages = sorted((data.get("query") or {}).get("pages", {}).values(),
                       key=lambda p: p.get("index", 99))
        for page in pages:
            info = (page.get("imageinfo") or [{}])[0]
            thumb = info.get("thumburl")
            if not thumb or not re.search(r"\.(jpe?g|png)$", thumb, re.IGNORECASE):
                continue
            meta = info.get("extmetadata", {})
            artist = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "")).strip()
            license_name = meta.get("LicenseShortName", {}).get("value", "")
            return {
                "url": thumb,
                "attribution": html.unescape(artist) or "Wikimedia Commons",
                "license": license_name,
                "descriptionUrl": info.get("descriptionurl", ""),
            }
    except Exception as e:
        print(f"    Commons lookup failed for '{search_term}': {e}")
    return None


def main():
    model = "sonnet"
    count = 2
    if "--model" in sys.argv:
        model = sys.argv[sys.argv.index("--model") + 1]
    if "--count" in sys.argv:
        count = int(sys.argv[sys.argv.index("--count") + 1])

    schedule = load_json(os.path.join(PROCESSED_DIR, "schedule.json"))
    news = load_json(os.path.join(PROCESSED_DIR, "news.json"))
    digest = load_json(os.path.join(PROCESSED_DIR, "digest.json"))
    if not schedule:
        print("ERROR: run worldcup_fetch_fixtures.py first.")
        sys.exit(1)

    existing = load_json(OUT_FILE) or {"articles": []}
    existing_slugs = {a["slug"] for a in existing["articles"]}

    prompt = build_prompt(schedule, news, digest, existing_slugs, count)
    print(f"Calling claude -p (model={model}, ~{len(prompt)} chars input, 1 call) ...")
    result = call_claude(prompt, model)

    headlines = (news or {}).get("items", [])
    now_iso = datetime.now(timezone.utc).isoformat()
    new_articles = []
    for art in result.get("articles", []):
        slug = re.sub(r"[^a-z0-9-]", "", art.get("slug", "").lower())
        if not slug or slug in existing_slugs:
            print(f"  SKIP duplicate/invalid slug: {art.get('slug')}")
            continue
        sources = [
            {"title": headlines[i]["title"], "url": headlines[i]["url"], "source": headlines[i]["source"]}
            for i in art.pop("sourceIndices", [])
            if isinstance(i, int) and 0 <= i < len(headlines)
        ]
        image = None
        term = art.pop("imageSearch", None)
        if term:
            print(f"  Commons image search: {term}")
            image = fetch_commons_image(term)
        new_articles.append({
            **art, "slug": slug, "sources": sources, "image": image,
            "publishedAt": now_iso, "generator": f"claude-{model}",
        })
        print(f"  + {art.get('category', '?')}: {art.get('title')}")

    merged = new_articles + existing["articles"]
    merged = merged[:MAX_KEPT_ARTICLES]
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"updatedAt": now_iso, "articles": merged}, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(new_articles)} new articles ({len(merged)} total) to {OUT_FILE}")


if __name__ == "__main__":
    main()
