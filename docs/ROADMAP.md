# MatchPrism Roadmap

Last updated: 2026-03-28

---

## What's Built & Working

### Data Pipeline (Complete)
- [x] Cricsheet data download — 6,847 matches across 12 T20 leagues
- [x] Venue processor — 350 venues with scoring trends, phase breakdowns, season comparisons
- [x] Player processor — 5,704 players with per-venue grades, form timelines, rolling averages
- [x] H2H processor — 1,129 rivalry pairs with recent scorecards
- [x] Matchup processor — 90,192 batter-vs-bowler matchups (6+ balls each)
- [x] Batter vs team / Bowler vs team records — 2,385 batters, 1,809 bowlers
- [x] Quality-adjusted stats — venue-adjusted performance, opposition quality ratings
- [x] Match generator — 14 IPL 2026 fixtures with win probability, captain picks, analysis
- [x] Pitch Scanner — dew probability, swing/spin potential, toss intelligence per match
- [x] Official IPL 2026 squads (post mini-auction Dec 2025)
- [x] Venue normalization — 100+ aliases mapped to canonical names with city lookup

### Frontend (Partially Complete)
- [x] Next.js 14 project — TypeScript, Tailwind CSS v4, App Router
- [x] Design system — "Digital Oracle" dark theme, full token system in globals.css
- [x] Layout — TopNav (glassmorphic), BottomNav (mobile), responsive
- [x] Homepage — hero, live countdown, intelligence picks, upcoming fixtures, system core
- [x] Match preview pages — 14 pages with real data (win probability, venue bento, captain picks, H2H, player fit table, glossary)
- [x] Live countdown timer — UTC-based, works in any timezone
- [x] Local time display — shows match time in user's timezone
- [x] GradeBadge component — A+/A/B/C/D with proper colors
- [x] Build passes clean, all pages statically generated

---

## Phase 1: Ship for IPL 2026 (Critical — IPL starts today)

### P0 — Must fix before sharing
- [ ] Wire player profile page to real data (currently imports from mock-data.ts)
- [ ] Wire venue page to real data (currently imports from mock-data.ts)
- [ ] Generate player pages for all key IPL 2026 players (currently only /player/virat-kohli)
- [ ] Generate venue pages for all 10 IPL home grounds (currently only /venue/chinnaswamy)
- [ ] Add Pitch Scanner data to match preview pages (data exists, not rendered)
- [ ] Add venue scoring trend sparkline/chart to match preview (data exists in scoringTimeline)
- [ ] Add player form timeline to captain pick cards (data exists in formTimeline)
- [ ] Fix any remaining hardcoded values in pages

### P1 — Should have for launch
- [ ] Deploy to Vercel (free tier, static site)
- [ ] Share card functionality — copy formatted text + link for WhatsApp/Twitter
- [ ] SEO — og:image placeholders, proper meta descriptions per match
- [ ] Add remaining IPL 2026 fixtures beyond the first 14 matches
- [ ] Data update script — fetch Cricsheet's recently_added_7 feed, re-process, rebuild
- [ ] Mobile polish — test on 375px, verify touch targets, bottom nav spacing

### P2 — Nice to have for IPL season
- [ ] Player search — find any player across 5,704 in the database
- [ ] Venue search — browse all 350 venues
- [ ] Head-to-head page — standalone page for any rivalry (e.g., /h2h/rcb-vs-csk)
- [ ] Batter vs bowler matchup lookup (data exists: 90K matchups)
- [ ] "New to Cricket" content on every match page
- [ ] Dark/light theme toggle (currently dark only)

---

## Phase 2: Post-Launch Improvements

### Data Enrichment
- [ ] Wire real-time weather API (OpenWeatherMap free tier) into Pitch Scanner
- [ ] Player injury/availability status system (manual or scraped)
- [ ] Post-break performance analysis (performance dip after 30+ day gaps)
- [ ] Return-from-injury historical analysis from Cricsheet gaps
- [ ] Improve win probability model (currently simple weighted formula)
- [ ] Add player photos/headshots (need source — possibly CricAPI or manual)

### Analytics Depth
- [ ] Venue-adjusted player grades (replace raw avg comparison with venue-baseline comparison)
- [ ] Opposition quality filtering on player profiles (show stats vs Tier 1 vs Tier 2)
- [ ] Batter vs bowler matchup card on match preview pages (Kohli vs Bumrah: 101 balls, SR 148.5)
- [ ] Phase-specific player stats (powerplay specialist, death overs finisher)
- [ ] Team strength index based on squad venue fit + form trends
- [ ] "What if" toss simulator — how probabilities change if team X wins toss

### Multi-League Expansion
- [ ] BBL match previews (Australian season ~Dec-Jan)
- [ ] PSL match previews (Pakistan season ~Feb-Mar)
- [ ] SA20 match previews (South Africa season ~Jan)
- [ ] CPL match previews (Caribbean season ~Aug-Sep)
- [ ] The Hundred match previews (UK season ~Jul-Aug)
- [ ] T20I series previews (bilateral tours)
- [ ] Cross-league player comparison tool

---

## Phase 3: Revenue & Growth

### Distribution (Free Tier)
- [ ] WhatsApp share cards (venue card + captain pick as formatted text)
- [ ] Twitter/X share cards with OG images
- [ ] Telegram channel with auto-posted match previews
- [ ] Reddit bot for r/Cricket match threads
- [ ] Instagram story template generator

### Premium Features
- [ ] Captain Genius reasoning (free tier shows picks, premium shows why)
- [ ] Value Analysis section (model probability vs market comparison)
- [ ] Avoid picks with detailed reasoning
- [ ] Custom alerts — "notify me when X player is picked for a match"
- [ ] Export match intelligence as PDF
- [ ] API access for data

### Pitch Scanner (V2)
- [ ] Live weather integration per venue on match day
- [ ] Pitch photo analysis (manual upload → conditions assessment)
- [ ] Dew forecast model using historical + real-time humidity/temperature
- [ ] Toss impact calculator with confidence intervals
- [ ] Historical conditions archive — what happened when it was 35C+ at Chepauk?

### Infrastructure
- [ ] Automated daily data refresh (Cricsheet recently_added feed → re-process → Vercel rebuild)
- [ ] CI/CD pipeline (push to main → build → deploy)
- [ ] Analytics (PostHog or Plausible, privacy-first)
- [ ] Error monitoring (Sentry free tier)
- [ ] Performance monitoring (Core Web Vitals)

---

## Current Data Inventory

| Dataset | Records | Size | Source |
|---------|---------|------|--------|
| Raw matches | 6,847 | ~40 MB | Cricsheet (12 leagues) |
| Venues | 350 | 1.5 MB | Processed |
| Players | 5,704 | 58 MB | Processed (with trends) |
| H2H pairs | 1,129 | 1.6 MB | Processed |
| Batter vs Bowler | 90,192 | 21 MB | Processed |
| Batter vs Team | 2,385 | 2.2 MB | Processed |
| Bowler vs Team | 1,809 | 2.3 MB | Processed |
| Quality stats | 5,704 | 2.6 MB | Processed |
| Match pages | 14 | 150 KB | Generated (IPL 2026) |
| Pitch reports | 14 | 23 KB | Generated |
| Schedule | 14 | 5 KB | Generated |

## Leagues Covered

| League | Matches | Latest Data |
|--------|---------|-------------|
| IPL | 1,169 | Jun 2025 |
| T20I (all nations) | 3,231 | Mar 2026 |
| BBL | 662 | Jan 2026 |
| BPL | 469 | Jan 2026 |
| CPL | 407 | Sep 2025 |
| PSL | 315 | Mar 2026 |
| ILT20 | 134 | Jan 2026 |
| SA20 | 130 | Jan 2026 |
| LPL | 119 | Jul 2024 |
| MLC | 75 | Jul 2025 |
| The Hundred | 72 | Jun 2025 |
| NPL | 64 | Dec 2025 |
