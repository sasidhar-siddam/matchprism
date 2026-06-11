"""
Proofread the newest World Cup articles with one headless Claude call,
applying the article-editor skill. Edits are written back in place with
an edit log per article.

USAGE:
    python scripts/worldcup_edit_articles.py            # edits unedited articles
    python scripts/worldcup_edit_articles.py --all      # re-edit everything recent
    python scripts/worldcup_edit_articles.py --model opus

COST:
    Exactly ONE `claude -p` call per run (default: sonnet), and only if there
    is something to edit. Skips cleanly when all articles are already edited.

INPUT:   data/processed/worldcup/articles.json, news.json, schedule.json
         .claude/skills/article-editor/SKILL.md
OUTPUT:  data/processed/worldcup/articles.json (in place)
"""

import json
import os
import re
import subprocess
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(__file__), "..")
PROCESSED_DIR = os.path.join(ROOT, "data", "processed", "worldcup")
SKILL_FILE = os.path.join(ROOT, ".claude", "skills", "article-editor", "SKILL.md")
ARTICLES_FILE = os.path.join(PROCESSED_DIR, "articles.json")

MAX_EDIT_BATCH = 4  # newest articles per run, keeps the single call small


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_skill():
    with open(SKILL_FILE, encoding="utf-8") as f:
        return re.sub(r"^---.*?---\s*", "", f.read(), flags=re.DOTALL)


def build_prompt(articles, news, schedule):
    """Editor needs the same source data the writer had, for check #1."""
    headlines = (news or {}).get("items", [])[:30]
    all_matches = (schedule or {}).get("matches", [])
    played = [m for m in all_matches if m["status"] == "played"][-12:]
    upcoming = [m for m in all_matches if m["status"] == "upcoming"][:15]

    lines = [load_skill(), "", "=" * 60, ""]
    lines.append("## Verified source data (ground truth for check #1):")
    for m in played:
        lines.append(f"- RESULT: {m['homeTeam']} {m['homeScore']}-{m['awayScore']} {m['awayTeam']} ({m['group'] or m['stage']}, {m['date']}, {m['venue']})")
    for m in upcoming:
        lines.append(f"- FIXTURE: {m['homeTeam']} vs {m['awayTeam']} ({m['group'] or m['stage']}) | {m['date']} {m['time']} | {m['venue']}, {m['city']}")
    for h in headlines:
        lines.append(f"- HEADLINE ({h['source']}): {h['title']}")
    lines += [
        "",
        "## Articles to edit (full JSON):",
        json.dumps(articles, ensure_ascii=False, indent=1),
        "",
        "Apply every check from the editor guide. Respond with ONLY JSON, no fences:",
        '{"articles": [same schema as supplied, corrected, each with an added "editLog": ["short change note", ...]]}',
        "Return ALL supplied articles in the same order, edited or not.",
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


def main():
    model = "sonnet"
    if "--model" in sys.argv:
        model = sys.argv[sys.argv.index("--model") + 1]
    re_edit_all = "--all" in sys.argv

    data = load_json(ARTICLES_FILE)
    if not data or not data.get("articles"):
        print("No articles to edit.")
        return
    news = load_json(os.path.join(PROCESSED_DIR, "news.json"))
    schedule = load_json(os.path.join(PROCESSED_DIR, "schedule.json"))

    candidates = [
        a for a in data["articles"][:MAX_EDIT_BATCH]
        if re_edit_all or not a.get("editedAt")
    ]
    if not candidates:
        print("All recent articles already edited — nothing to do (0 claude calls).")
        return

    # Strip bulky fields the editor doesn't need; restore after
    slim = []
    held_back = {}
    for a in candidates:
        held_back[a["slug"]] = {k: a.get(k) for k in ("image", "sources", "publishedAt", "generator", "editedAt")}
        slim.append({k: v for k, v in a.items() if k not in held_back[a["slug"]]})

    prompt = build_prompt(slim, news, schedule)
    print(f"Editing {len(slim)} article(s) via claude -p (model={model}, ~{len(prompt)} chars, 1 call) ...")
    result = call_claude(prompt, model)

    edited_by_slug = {}
    now_iso = datetime.now(timezone.utc).isoformat()
    for art in result.get("articles", []):
        slug = art.get("slug")
        if slug not in held_back:
            continue
        restored = {**art, **{k: v for k, v in held_back[slug].items() if v is not None}}
        restored["editedAt"] = now_iso
        restored["editLog"] = art.get("editLog", [])
        edited_by_slug[slug] = restored
        changes = len(restored["editLog"])
        print(f"  {slug}: {changes} change(s)" + (f" — {'; '.join(restored['editLog'][:3])}" if changes else " (clean)"))

    data["articles"] = [edited_by_slug.get(a["slug"], a) for a in data["articles"]]
    data["updatedAt"] = now_iso
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Wrote edited articles to {ARTICLES_FILE}")


if __name__ == "__main__":
    main()
