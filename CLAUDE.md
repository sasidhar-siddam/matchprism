# MatchPrism - Sports Match Intelligence Platform

## What This Is
Data-driven match intelligence for cricket (expanding to other sports). Provides venue analytics, player form, win probability, and value analysis by comparing model probabilities vs bookmaker odds.

## Key Principle
**India is the funnel (free, analytics-first). UK/AU/UAE is the revenue (paid betting intelligence).**
The product NEVER uses gambling/betting language in branding. It's positioned as "sports analytics" everywhere. Betting features are a premium toggle, not the identity.

## Tech Stack
- **Data processing:** Python scripts that process Cricsheet ball-by-ball data into pre-computed JSON
- **Frontend:** Next.js 14+ (App Router), TypeScript, Tailwind CSS
- **Hosting:** Vercel free tier
- **Data sources:** Cricsheet.org (free, 1,169 IPL matches), CricAPI (free, 100K hits/hr), The Odds API (free 500 req/mo)
- **LLM costs:** $0 API keys — cricket analysis is rule-based; World Cup editorial uses headless `claude -p` (sonnet, ~3 calls/refresh, billed to the Claude Code plan, never OpenAI)
- **Database:** None for v1 - static JSON files

## World Cup 2026 Section
- Pipeline: `npm run worldcup:refresh` → `scripts/worldcup_fetch_fixtures.py` (fixturedownload.com, free) → `worldcup_fetch_news.py` (RSS, free) → `worldcup_generate_digest.py` / `worldcup_generate_articles.py` / `worldcup_edit_articles.py` (one `claude -p` call each)
- Editorial voice lives in `.claude/skills/worldcup-article/SKILL.md`; proofreading rules in `.claude/skills/article-editor/SKILL.md` — scripts read these files as their prompts, so edit the skill to change the output style. Research basis: `docs/editorial-research.md`
- `data/processed/worldcup/` IS committed (gitignore exception, small JSON) so `.github/workflows/worldcup-refresh.yml` can refresh it on a daily cron (needs `CLAUDE_CODE_OAUTH_TOKEN` repo secret for the LLM steps)
- Pages: `/worldcup` (hub), `/worldcup/matches`, `/worldcup/news`, `/worldcup/news/[slug]`; loaders in `src/lib/worldcup.ts` degrade gracefully when JSON is missing
- Article images: Wikimedia Commons only (CC-licensed, attributed) + generated OG hero images — never scrape press photos

## Project Structure
```
scripts/           # Python data processing pipeline
data/raw/          # Raw Cricsheet JSON files
data/processed/    # Pre-computed venue/player/match stats
src/app/           # Next.js pages
src/components/    # React components
src/lib/           # Utilities, types, calculations
docs/              # Product specs, personas, research
```

## Critical Context
- IPL 2026 starts March 28, 2026 (RCB vs SRH at Chinnaswamy)
- India banned real-money fantasy/gaming Aug 2025 (Dream11 lost 95% revenue)
- 130M displaced Indian fantasy users = free distribution army
- UK cricket betting = £52M/yr, AU = 27% of bettors bet on cricket
- Primary revenue personas: Raj (UK diaspora), Priya (UAE expat), Dave (AU punter)

## Naming
- Brand: MatchPrism
- Domain: matchprism.com + matchprism.io (both available as of 2026-03-27)
- NO gambling/betting words in branding, URLs, or meta tags
- Analytics-first language: "intelligence," "insights," "analysis," "data-driven"
