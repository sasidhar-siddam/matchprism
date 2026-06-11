"""
Fetch World Cup 2026 news from free RSS feeds — no API keys, no LLM calls.

USAGE:
    python scripts/worldcup_fetch_news.py

SOURCES (pattern borrowed from the Cartesian Coordinates newsletter pipeline,
re-implemented with stdlib only — no feedparser dependency):
    - BBC Sport Football RSS
    - The Guardian Football RSS
    - ESPN Soccer RSS
    - Google News RSS search for "FIFA World Cup 2026" (free, no key)

FILTERING:
    Rule-based relevance scoring — items must mention the World Cup or a
    competing nation in a football context. No paid scoring model.

OUTPUT:
    data/processed/worldcup/news.json
"""

import base64
import html
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "worldcup")
SCHEDULE_FILE = os.path.join(PROCESSED_DIR, "schedule.json")
OUT_FILE = os.path.join(PROCESSED_DIR, "news.json")

MAX_ITEMS = 60
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0 Safari/537.36"

# (name, url, pre_filtered) — pre_filtered feeds are already World Cup queries
FEEDS = [
    ("BBC Sport", "https://feeds.bbci.co.uk/sport/football/rss.xml", False),
    ("The Guardian", "https://www.theguardian.com/football/rss", False),
    ("ESPN", "https://www.espn.com/espn/rss/soccer/news", False),
    (
        "Google News",
        "https://news.google.com/rss/search?q=%22World%20Cup%202026%22&hl=en-US&gl=US&ceid=US:en",
        True,
    ),
]

WORLD_CUP_TERMS = ["world cup", "fifa", "wc 2026", "world cup 2026"]


def fetch_feed(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def strip_html(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text or "")).strip()


def resolve_gnews_url(url: str) -> str:
    """
    Google News RSS wraps article links as news.google.com/rss/articles/<token>.
    For the common CBMi-style tokens the publisher URL is embedded in the
    base64 payload — decode it offline (no network). Newer token formats
    don't embed the URL; those keep the wrapper, which still redirects fine.
    """
    m = re.search(r"news\.google\.com/rss/articles/([^?/]+)", url)
    if not m:
        return url
    token = m.group(1)
    try:
        raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
        candidates = re.findall(rb"https?://[\x21-\x7e]+", raw)
        for c in candidates:
            decoded = c.decode("ascii", errors="ignore")
            # Embedded URLs end where protobuf framing resumes; trim trailing
            # non-URL bytes conservatively
            decoded = re.split(r"[\x00-\x20\"'<>\\^`{|}]", decoded)[0].rstrip("\\")
            if "google.com" not in decoded and len(decoded) > 12:
                return decoded
    except Exception:
        pass
    return url


def parse_rss(xml_text: str, source_name: str):
    """Parse RSS 2.0 items with stdlib ElementTree. Tolerant of bad items."""
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items
    for item in root.iter("item"):
        title = strip_html(item.findtext("title") or "")
        link = (item.findtext("link") or "").strip()
        if not title or not link:
            continue
        # Google News appends " - Publisher" to titles, nests the real source,
        # and wraps links in a redirect URL we can usually decode offline
        source = source_name
        if source_name == "Google News":
            nested = item.find("source")
            if nested is not None and (nested.text or "").strip():
                source = nested.text.strip()
            title = re.sub(r"\s+-\s+[^-]+$", "", title)
            link = resolve_gnews_url(link)
        published = None
        pub_date = item.findtext("pubDate")
        if pub_date:
            try:
                published = parsedate_to_datetime(pub_date).astimezone(timezone.utc).isoformat()
            except (ValueError, TypeError):
                pass
        items.append({
            "title": title,
            "url": link,
            "source": source,
            "published": published,
            "summary": strip_html(item.findtext("description") or "")[:300],
        })
    return items


def load_team_names():
    """Competing nations from the fixture file, for relevance matching."""
    if not os.path.exists(SCHEDULE_FILE):
        return []
    with open(SCHEDULE_FILE, encoding="utf-8") as f:
        schedule = json.load(f)
    names = set()
    for m in schedule["matches"]:
        for t in (m["homeTeam"], m["awayTeam"]):
            # Skip knockout placeholders like "Winner Group A" / "1A"
            if len(t) > 3 and not t.lower().startswith(("winner", "runner", "loser", "1", "2", "3")):
                names.add(t.lower())
    return sorted(names)


def relevance(item, team_names, pre_filtered: bool) -> int:
    text = f"{item['title']} {item['summary']}".lower()
    score = 2 if pre_filtered else 0
    for term in WORLD_CUP_TERMS:
        if term in text:
            score += 2
            break
    if any(name in text for name in team_names):
        score += 1
    return score


def main():
    team_names = load_team_names()
    if not team_names:
        print("WARNING: schedule.json not found — run worldcup_fetch_fixtures.py first.")

    all_items = []
    for name, url, pre_filtered in FEEDS:
        try:
            xml_text = fetch_feed(url)
        except Exception as e:  # network errors must not kill the whole run
            print(f"  SKIP {name}: {e}")
            continue
        items = parse_rss(xml_text, name)
        kept = [i for i in items if relevance(i, team_names, pre_filtered) >= 2]
        print(f"  {name}: {len(items)} items, {len(kept)} relevant")
        all_items.extend(kept)

    # Dedup by normalized title, newest first
    seen = set()
    deduped = []
    all_items.sort(key=lambda i: i["published"] or "", reverse=True)
    for item in all_items:
        key = re.sub(r"[^a-z0-9]+", "", item["title"].lower())[:80]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    deduped = deduped[:MAX_ITEMS]
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"fetchedAt": datetime.now(timezone.utc).isoformat(), "items": deduped},
            f, indent=2, ensure_ascii=False,
        )
    print(f"Wrote {len(deduped)} news items to {OUT_FILE}")


if __name__ == "__main__":
    main()
