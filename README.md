# MatchPrism

**T20 Cricket Match Intelligence Platform**

Data-driven match previews, player analytics, venue intelligence, and conditions analysis for T20 cricket worldwide. Built on 6,847 ball-by-ball matches across 12 leagues.

Live at: [matchprism.com](https://matchprism.com)

---

## What It Does

MatchPrism processes raw ball-by-ball cricket data into actionable match intelligence:

- **Match Previews** — Win probability, captain picks, venue fit grades, H2H records
- **Player Profiles** — Career stats, form trends, venue grades, season comparisons across all T20 leagues
- **Venue Intelligence** — Scoring trends, phase dynamics, toss intelligence, dew analysis
- **Pitch Scanner** — Match-day conditions: dew probability, swing/spin potential, toss recommendations
- **Matchup Data** — 90,192 batter-vs-bowler matchups, player-vs-team records
- **Quality Metrics** — Venue-adjusted stats, opposition quality ratings

---

## Architecture

```
                              ┌──────────────────────────────┐
                              │        DATA SOURCES          │
                              │                              │
                              │   Cricsheet.org (free)       │
                              │   6,847 T20 matches          │
                              │   12 leagues, 107 nations    │
                              │   Ball-by-ball JSON          │
                              └──────────────┬───────────────┘
                                             │
                                      download_all.py
                                             │
                              ┌──────────────▼───────────────┐
                              │        RAW DATA (497 MB)     │
                              │                              │
                              │   data/raw/ipl/    (1,169)   │
                              │   data/raw/t20i/   (3,231)   │
                              │   data/raw/bbl/      (662)   │
                              │   data/raw/bpl/      (469)   │
                              │   data/raw/cpl/      (407)   │
                              │   data/raw/psl/      (315)   │
                              │   + 6 more leagues           │
                              └──────────────┬───────────────┘
                                             │
                    ┌────────────────────────┼─────────────────────────┐
                    │                        │                         │
           process_venues.py        process_players.py        process_h2h.py
                    │                        │                         │
                    │                 process_matchups.py               │
                    │                        │                         │
                    │                 process_quality.py                │
                    │                        │                         │
                    ▼                        ▼                         ▼
          ┌─────────────┐         ┌──────────────────┐      ┌──────────────┐
          │ venues.json │         │  players.json    │      │   h2h.json   │
          │ 350 venues  │         │  5,704 players   │      │ 1,129 pairs  │
          │ 1.5 MB      │         │  58 MB           │      │ 1.6 MB       │
          └──────┬──────┘         └────────┬─────────┘      └──────┬───────┘
                 │                         │                        │
                 │    ┌────────────────────┼────────────────────────┘
                 │    │                    │
                 ▼    ▼                    ▼
          ┌──────────────────────────────────────────────┐
          │          generate_matches.py                  │
          │          pitch_scanner.py                     │
          │                                              │
          │   Combines all data per IPL 2026 fixture:    │
          │   - Win probability model                    │
          │   - Captain picks (ranked by venue fit)      │
          │   - Advanced analysis                        │
          │   - Conditions intelligence                  │
          └──────────────────┬───────────────────────────┘
                             │
                             ▼
          ┌──────────────────────────────────────────────┐
          │          PROCESSED DATA (90 MB)              │
          │                                              │
          │   schedule.json          14 fixtures         │
          │   matches/*.json         14 match files      │
          │   pitch_reports.json     14 reports           │
          │   matchups.json          90,192 matchups     │
          │   batter_vs_team.json    2,385 batters       │
          │   bowler_vs_team.json    1,809 bowlers       │
          │   quality_stats.json     5,704 players       │
          └──────────────────┬───────────────────────────┘
                             │
                      Next.js SSG (build time)
                             │
                             ▼
          ┌──────────────────────────────────────────────┐
          │          FRONTEND (276 static pages)         │
          │                                              │
          │   /                  Homepage + countdown    │
          │   /matches           IPL 2026 schedule       │
          │   /players           1,000+ player cards     │
          │   /venues            100+ venue cards        │
          │   /match/[slug]      14 match previews       │
          │   /player/[slug]     156 player profiles     │
          │   /venue/[slug]      100 venue deep-dives    │
          │                                              │
          │   Next.js 16 · TypeScript · Tailwind v4     │
          │   Static site · Vercel deployment            │
          └──────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 16, TypeScript, Tailwind CSS v4 | Static site generation, App Router |
| **Data Processing** | Python 3 (stdlib only) | Ball-by-ball analysis, no external dependencies |
| **Data Source** | [Cricsheet.org](https://cricsheet.org) | Free ball-by-ball JSON for all T20 leagues |
| **Hosting** | Vercel (free tier) | Static site CDN |
| **Testing** | Playwright (E2E), Vitest (unit) | 56 E2E + 35 unit tests |

**Zero paid APIs. Zero databases. Zero LLM costs.** All intelligence is computed from historical match data.

---

## Leagues Covered

| League | Matches | Region | Latest Data |
|--------|---------|--------|-------------|
| T20 Internationals | 3,231 | Global (107 nations) | Mar 2026 |
| Indian Premier League | 1,169 | India | Jun 2025 |
| Big Bash League | 662 | Australia | Jan 2026 |
| Bangladesh Premier League | 469 | Bangladesh | Jan 2026 |
| Caribbean Premier League | 407 | Caribbean | Sep 2025 |
| Pakistan Super League | 315 | Pakistan | Mar 2026 |
| ILT20 | 134 | UAE | Jan 2026 |
| SA20 | 130 | South Africa | Jan 2026 |
| Lanka Premier League | 119 | Sri Lanka | Jul 2024 |
| Major League Cricket | 75 | USA | Jul 2025 |
| The Hundred | 72 | England | Jun 2025 |
| Nepal Premier League | 64 | Nepal | Dec 2025 |

---

## Project Structure

```
matchprism/
├── src/
│   ├── app/
│   │   ├── layout.tsx              Root layout (fonts, nav, metadata)
│   │   ├── globals.css             Tailwind v4 @theme tokens
│   │   ├── page.tsx                Homepage
│   │   ├── matches/page.tsx        Schedule index
│   │   ├── players/page.tsx        Player directory
│   │   ├── venues/page.tsx         Venue directory
│   │   ├── match/[slug]/page.tsx   Match preview (14 pages)
│   │   ├── player/[slug]/page.tsx  Player profile (156 pages)
│   │   └── venue/[slug]/page.tsx   Venue detail (100 pages)
│   ├── components/
│   │   ├── TopNav.tsx              Glassmorphic header
│   │   ├── BottomNav.tsx           Mobile bottom nav
│   │   ├── Countdown.tsx           Live countdown (UTC-based)
│   │   ├── LocalTime.tsx           User timezone display
│   │   └── GradeBadge.tsx          A+/A/B/C/D grade chips
│   └── lib/
│       ├── data.ts                 Server-side data loaders
│       ├── teams.ts                10 IPL team metadata
│       └── types.ts                Shared TypeScript types
├── scripts/
│   ├── download_all.py             Download all 12 league datasets
│   ├── process_venues.py           Venue stats + trends
│   ├── process_players.py          Player stats + form timelines
│   ├── process_h2h.py              Team head-to-head records
│   ├── process_matchups.py         Batter vs bowler matchups
│   ├── process_quality.py          Venue-adjusted + opposition quality
│   ├── generate_matches.py         Per-match intelligence files
│   ├── pitch_scanner.py            Conditions analysis engine
│   └── venue_map.py                Venue name normalization (100+ aliases)
├── data/
│   ├── raw/                        6,847 Cricsheet JSON files (497 MB)
│   └── processed/                  Computed analytics (90 MB)
├── e2e/
│   └── matchprism.spec.ts          56 Playwright E2E tests
├── docs/
│   ├── ROADMAP.md                  Feature roadmap
│   ├── features.md                 Feature spec
│   ├── personas.md                 User personas
│   ├── data-sources.md             Data source documentation
│   └── stitch-prompt.md            Design system prompt
└── CLAUDE.md                       Project context for AI assistants
```

---

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+

### 1. Install dependencies
```bash
npm install
```

### 2. Download cricket data
```bash
cd scripts
python download_all.py
```
This downloads ~40 MB of ball-by-ball JSON from Cricsheet across 12 T20 leagues (6,847 matches).

### 3. Process data
```bash
python process_venues.py
python process_players.py
python process_h2h.py
python process_matchups.py
python process_quality.py
python generate_matches.py
python pitch_scanner.py
cd ..
```

### 4. Run the site
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000)

### 5. Build for production
```bash
npm run build    # Generates 276 static pages
npm run start    # Serve production build
```

---

## Testing

```bash
# E2E tests (56 tests, requires dev server running)
npx playwright test

# Unit tests with coverage (35 tests)
npx vitest run --coverage
```

| Suite | Tests | Coverage |
|-------|-------|----------|
| E2E (Playwright) | 56 | All pages, navigation, interactions, a11y |
| Unit (Vitest) | 35 | 82% statements, 90% lines on data layer |

---

## Data Pipeline

All processing uses **Python stdlib only** — no pandas, no numpy, no external packages.

| Script | Input | Output | What it computes |
|--------|-------|--------|-----------------|
| `download_all.py` | Cricsheet URLs | `data/raw/` | Downloads 12 league datasets |
| `process_venues.py` | Raw matches | `venues.json` | 350 venues: scoring trends, phase dynamics, season comparisons |
| `process_players.py` | Raw matches | `players.json` | 5,704 players: per-venue grades, form timelines, rolling averages |
| `process_h2h.py` | Raw matches | `h2h.json` | 1,129 rivalry pairs with recent scorecards |
| `process_matchups.py` | Raw matches | `matchups.json` + `*_vs_team.json` | 90K batter-bowler matchups, player-vs-team records |
| `process_quality.py` | Processed data | `quality_stats.json` | Venue-adjusted stats, opposition quality ratings |
| `generate_matches.py` | All processed | `matches/*.json` | Per-match intelligence: win probability, captain picks |
| `pitch_scanner.py` | Venues + schedule | `pitch_reports.json` | Dew, swing, spin, toss recommendations |

### Updating Data
Cricsheet updates daily. To refresh:
```bash
cd scripts
python download_all.py          # Re-downloads all leagues
python process_venues.py        # ~2 min
python process_players.py       # ~3 min
python process_h2h.py           # ~1 min
python process_matchups.py      # ~2 min
python generate_matches.py      # ~10 sec
python pitch_scanner.py         # ~30 sec
cd .. && npm run build           # Regenerate static pages
```

---

## Design System

"The Digital Oracle" — dark, data-dense, premium analytics aesthetic.

- **Palette**: Midnight foundation (`#10131a`) with electric blue accents (`#a4e6ff`)
- **Typography**: Space Grotesk (headlines) + Inter (data/body)
- **Tonal Layering**: No 1px borders — depth through surface-container color shifts
- **Grade Colors**: A+ emerald, A green, B yellow, C orange, D red
- **Min Font Size**: 11px (accessibility baseline)

See `docs/stitch-prompt.md` for the full design specification.

---

## Key Design Decisions

1. **Static site, not SPA** — All 276 pages pre-rendered at build time. No client-side data fetching. Fast, SEO-friendly, free hosting.

2. **Python stdlib only** — No pandas/numpy dependency. The entire data pipeline runs with just `json`, `os`, `collections`. Keeps the processing portable and dependency-free.

3. **No LLM costs** — All "intelligence" is computed from historical patterns. Win probability, captain picks, venue grades, pitch analysis — all rule-based math on real data.

4. **Analytics language, not betting language** — The platform uses "probability", "intelligence", "insights" — never "odds", "betting", "bookmaker". Positioned as sports analytics.

5. **Cross-league data** — Player profiles aggregate stats across all T20 leagues. Kohli's profile includes IPL + T20I data. Rashid Khan spans 9 leagues.

6. **Venue-adjusted metrics** — Raw averages are misleading. A bowler's economy is rated relative to the venue's run rate, not in isolation.

---

## License

MIT
