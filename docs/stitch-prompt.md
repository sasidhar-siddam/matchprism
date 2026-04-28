# Stitch Prompt - MatchPrism

Copy everything below the line into Stitch.

---

Build a Next.js web application called **"MatchPrism"** - a sports match intelligence platform that provides data-driven match previews, player analytics, fantasy cricket captain picks, and probability analysis for every IPL 2026 match.

**CRITICAL BRANDING RULE: The application name is "MatchPrism" everywhere — in the header, navigation, page titles, meta tags, share cards, and all copy. Do NOT rename it to anything else. Do NOT use "CricMind" or any other name. The brand is "MatchPrism".**

**CRITICAL LANGUAGE RULE: This is a sports analytics platform, NOT a betting/gambling site. NEVER use the words: "bet", "betting", "gamble", "gambling", "wager", "bookie", "bookmaker", "punter", "odds" (use "probability" instead), "arbitrage", "market alpha". Use instead: "analysis", "analytics", "intelligence", "insights", "probability", "model confidence", "edge", "value signal". This applies to ALL text — headings, labels, buttons, metadata, component names, tooltips, and body copy.**

## TECH STACK
- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS
- Python scripts for data processing (separate /scripts directory)
- Static JSON data files (no database needed for frontend)
- Vercel deployment

## DATA SOURCE
The primary data source is Cricsheet (cricsheet.org) ball-by-ball IPL data - 1,169 matches in JSON format. Download from https://cricsheet.org/downloads/ipl_json.zip

Each Cricsheet JSON match file contains:
- info.teams, info.toss, info.venue, info.dates, info.player_of_match
- info.outcome (winner, by runs/wickets)
- innings[].overs[].deliveries[] - every ball: batter, bowler, runs, wickets, extras

## PROJECT STRUCTURE
```
matchprism/
  scripts/                    # Python data processing
    download_data.py          # Download and extract Cricsheet IPL JSON zip
    process_venues.py         # Generate venue stats JSON
    process_players.py        # Generate player-by-venue stats JSON
    process_h2h.py            # Generate team head-to-head stats JSON
    generate_match_pages.py   # Combine all data for each IPL 2026 fixture
  data/
    raw/                      # Raw Cricsheet JSON files
    processed/
      venues.json             # Pre-computed venue stats
      players.json            # Player stats by venue
      h2h.json                # Team H2H records
      matches/                # One JSON per IPL 2026 match
        2026-03-28-rcb-vs-srh.json
        ...
  src/
    app/
      page.tsx                # Homepage - today's match + upcoming schedule
      match/[slug]/page.tsx   # Individual match preview page
      player/[slug]/page.tsx  # Player profile page
      venue/[slug]/page.tsx   # Venue intelligence deep-dive page
    components/
      VenueCard.tsx           # Venue intelligence card
      HeadToHead.tsx          # H2H record display
      PlayerTable.tsx         # Player venue fit table with grades
      CaptainGenius.tsx       # Top 3 captain picks with reasoning
      WinProbability.tsx      # Win probability bar
      ValueAnalysis.tsx       # Model probability vs market comparison
      ShareCard.tsx           # Shareable image card component
      MatchHeader.tsx         # Match title, teams, venue, time
      SmartBuilder.tsx        # Combined scenario analysis with confidence %
      NewToCricket.tsx        # Collapsible explainer for new fans
      PlayerProfile.tsx       # Full player stats, radar chart, form pulse
      BottomNav.tsx           # Fixed bottom navigation bar
    lib/
      types.ts                # TypeScript interfaces for all data
      calculations.ts         # Win probability model, value calculations
      probabilities.ts        # Fetch external probability data
      teams.ts                # Team colors, logos, metadata
```

## PYTHON SCRIPTS (scripts/)

### download_data.py
- Download https://cricsheet.org/downloads/ipl_json.zip
- Extract to data/raw/

### process_venues.py
For each IPL venue, compute from all historical matches at that ground:
- Average 1st innings score (all-time + last 2 seasons)
- Average 2nd innings score
- Win % batting first vs chasing
- Toss decision breakdown (bat/bowl) and win % by toss decision
- Pace wickets vs spin wickets percentage
- Phase breakdown: powerplay avg runs (overs 1-6), middle overs (7-15), death overs (16-20)
- Highest and lowest totals
- Average wickets per innings
- Total matches played
- A one-line "venue verdict" string summarizing the ground character
Output: data/processed/venues.json

### process_players.py
For each player who has played IPL, compute per-venue stats:
- Batting: innings, runs, average, strike rate, 50s, 100s, highest score, boundaries, sixes
- Bowling: innings, wickets, average, economy, strike rate, best figures
- Last 5 IPL match scores/figures (regardless of venue)
- Overall IPL career stats for comparison
- "Venue Fit Grade": Compare venue-specific average to overall average.
  - A+ = venue avg > 130% of overall avg
  - A = venue avg > 115% of overall
  - B = venue avg 85-115% of overall (neutral)
  - C = venue avg 60-85% of overall
  - D = venue avg < 60% of overall
  Same logic for bowlers using economy rate (inverted - lower economy at venue = better fit).
Output: data/processed/players.json (keyed by player name, then by venue)

### process_h2h.py
For each pair of IPL teams, compute:
- Overall H2H record (wins each, ties)
- H2H at each venue specifically
- Last 5 meetings with scores and winners
- Average score in H2H matches
Output: data/processed/h2h.json

### generate_match_pages.py
Takes the IPL 2026 schedule (hardcoded list of fixtures with date, team1, team2, venue) and for each match, combines:
- Venue stats from venues.json
- H2H stats from h2h.json
- Player stats for both squads from players.json (use IPL 2026 squad lists, hardcoded)
- Compute win probability: simple model using venue advantage (home team +5%), H2H record weighting (20%), recent form weighting (30%), squad strength (50% based on avg player venue fit grades)
- Generate top 3 captain picks: rank players by (venue_average * venue_strike_rate) for batters, (venue_wickets_per_match / venue_economy) for bowlers, pick top 3 with reasoning strings
- Generate "avoid today" picks: players with D or C venue fit grades who are likely to play
Output: data/processed/matches/{date}-{team1}-vs-{team2}.json

## DESIGN SYSTEM

### Creative Direction: "The Digital Oracle"
The interface should feel like a high-end financial terminal — dense yet breathable, dark yet luminous. Data is the protagonist. Reject cluttered sports media aesthetics in favor of a sophisticated, editorial-grade analytical environment.

### Color Palette (Tonal Layering)
The palette is rooted in a deep midnight foundation using blues and teals to guide the eye toward actionable intelligence.

Foundation surfaces:
- Surface Base (canvas): #10131a
- Surface Container Lowest: #0b0e14
- Surface Container Low: #191c22
- Surface Container: #1d2026
- Surface Container High: #272a31
- Surface Container Highest: #32353c

Accents:
- Primary (actions, critical insights): #a4e6ff
- Primary Container (CTAs, gradients): #00d1ff
- Secondary (supplemental data): #bdc7d9
- On-Surface (body text — never use pure #FFFFFF): #e1e2eb
- Outline Variant (ghost borders at 15% opacity only): #3c494e

Grade colors (for chips and display numbers):
- A+ (Emerald / Peak): #10b981
- A (Green / High): #34d399
- B (Yellow / Average): #fbbf24
- C (Orange / At Risk): #fb923c
- D (Red / Critical): #ef4444

Team colors (used sparingly as identification ribbons or 2px accent pips, never full backgrounds):
- RCB: #ff4d4d / gold | MI: #004BA0 / gold | CSK: #FDB913 / blue
- SRH: #ff8200 / black | KKR: #3B2D6B / gold | DC: #004C93 / red
- RR: #EA1A85 / blue | PBKS: #ED1B24 / silver | GT: #1B2133 / gold
- LSG: #00A5E3 / navy

### The "No-Line" Rule
1px solid borders for sectioning are prohibited. Define boundaries through:
- Background color shifts between surface-container tiers
- Tonal transitions for organic separation
- Exception: ghost borders at 15% opacity for badges/special containers only

### Typography (Dual-Font Strategy)
- Display & Headline: Space Grotesk (geometric, authoritative)
- Title, Body, Label: Inter (dense stats readability)

Scale:
- Display-LG (3.5rem): High-impact hero metrics
- Headline-SM (1.5rem): Player names, match titles
- Body-MD (0.875rem / 14px): Analytical summaries
- Label-SM (0.6875rem / 11px): Technical metadata — THIS IS THE MINIMUM FONT SIZE. Never use anything smaller than 11px.

### Glass & Gradient
- Floating headers and nav: surface-container-high at 70% opacity + backdrop-blur 12px
- CTA gradients: linear-gradient(135deg, #a4e6ff, #00d1ff) for "lit-from-within" glow
- Primary action buttons: solid primary fill, on-primary text, 0.75rem border-radius

### Elevation
No drop shadows on cards. Achieve depth through tonal layering only:
- Level 0: surface-container-lowest
- Level 1: surface-container-low
- Level 2: surface-container-high
- Ambient shadows only for floating modals: 24px blur, 0px offset, 6% opacity

### Do's and Don'ts
- DO: Prioritize vertical rhythm with consistent spacing between sections
- DO: Use soft card corners (rounded-2xl / rounded-3xl)
- DO: Keep all data tables and lists left-aligned for rapid scanning
- DON'T: Use emojis anywhere — this is a professional intelligence tool
- DON'T: Use #FFFFFF — always use on-surface (#e1e2eb)
- DON'T: Use standard drop shadows on cards
- DON'T: Center-align large data blocks
- DON'T: Use any font size below 11px

## FRONTEND PAGES & COMPONENTS

### Homepage (page.tsx)
- Hero section: "Today's Match" card with stadium background image (gradient overlay), team names large, countdown timer in a glassmorphic box
- "Intelligence Picks" section: Top 3 captain picks as cards showing player name, team badge pip, venue fit grade, projected points range
- Upcoming fixtures list: 5-7 matches as rows with overlapping team circle avatars, venue name, date/time
- "System Core" sidebar: explains the data-driven methodology with feature bullet points
- Tagline: "See every match through a data lens"
- Bottom navigation bar: Home (filled), Matches, Insights, Profile
- IMPORTANT: No gambling/betting language anywhere on homepage

### Match Preview Page (match/[slug]/page.tsx)
Full match preview with these sections in order:

1. **Match Header**: Team names large with team color pips, venue, date, time. Win probability bar below — horizontal bar split by team colors with percentage labels.

2. **Venue Intelligence Card** (bento grid layout):
   - Left 2/3: avg 1st innings score, chase win %, toss decision breakdown, pitch nature — with a callout quote for venue verdict
   - Right 1/3: Pace vs Spin wicket split as stacked progress bars
   - Share button

3. **Captain Genius** (highlighted section):
   - Top 3 picks as cards with: player name, team, role, venue fit grade (A+/A/B/C/D colored), last 5 scores as small square chips, 2-3 sentence reasoning
   - "Avoid Today" alert bar: D-grade player with reason, red styling
   - Share button

4. **Value Analysis** (toggleable, labeled "Advanced Analysis", hidden by default):
   - Table: Outcome name, Model Probability %, Implied Probability %, Confidence Edge %, Verdict (VALUE / FAIR / AVOID)
   - Uses external probability data (graceful fallback: "Probability data available closer to match time")
   - Small disclaimer: "For informational purposes only."

5. **Head to Head**:
   - Overall record as large styled numbers (e.g., "RCB 9 - 7 SRH")
   - Last 3-5 meetings as horizontally scrollable mini scorecards with team color left-border accent

6. **Player Venue Fit Table**:
   - Tabbed: Team A | Team B (underline-style tab selector)
   - Table: Player, Role, Venue Avg, Venue SR/Econ, Grade (color-coded)
   - Color-coded grades: A+ emerald, A green, B yellow, C orange, D red

7. **New to Cricket?** (collapsible accordion at bottom):
   - What's a powerplay? (with baseball analogy)
   - What's DRS? (like video review in NFL)
   - What's an impact player?
   - What are death overs?
   - "Which team should I root for?" personality guide

### Player Profile Page (player/[slug]/page.tsx)
- Player name, team, role with photo placeholder
- Overall venue fit grade (large, colored) + composite score (e.g., "98.4")
- "Recent Form Pulse": sparkline or bar chart of last 10 match scores
- Radar chart: Venue Fit Analysis showing dimensions like Power, Consistency, Pace Handling, Spin Handling — per venue toggle
- Batting/Bowling stats table: Avg, SR, Runs, Innings, 50s, 100s, Boundaries, etc.
- "Intelligence Insight" callout: one-line data insight (e.g., "Averages 48 against pace at Chinnaswamy since 2022")
- Share Analysis button + bottom nav Profile tab active

### Venue Intelligence Page (venue/[slug]/page.tsx)
- Venue name, city, total matches played as header
- Key metrics row: Average Score, Run Rate, Boundaries per innings
- Toss decision breakdown (bat/bowl %) as donut or split bar
- Historical trends section: phase-by-phase analysis (Powerplay, Middle, Death)
- Pace Specialist vs Spin Specialist section with key players and their venue stats
- List of upcoming matches at this venue

### Component Library Reference
Build a consistent set of reusable components:
- **Atmospheric Metrics**: Weather/conditions icons with contextual data (Sun/Cloud/Humidity/Wind)
- **Player Comparison Card**: Side-by-side VS layout with centered ghost border separator
- **Form Timeline**: Sparkline chart showing performance trend with High/Low Thursday indicators
- **Grade Badge**: Consistent A+/A/B/C/D chips with background tint + border

### Bottom Navigation Bar
- Fixed bottom, glassmorphic background (surface-container-low at 90% opacity + backdrop-blur)
- 4 items: Home, Matches, Insights, Profile
- Active state: primary color text + primary/10 background pill
- Inactive: secondary at 60% opacity
- Material Symbols Outlined icons with filled variant for active state

### ShareCard Component
- Share button on Venue Card and Captain Genius sections
- Copies pre-formatted text with key stats + link to the full page
- Format: "MatchPrism | RCB vs SRH | Chinnaswamy\nAvg score: 178 | Chase wins: 58%\nCaptain pick: Kohli (A+ venue fit)\nFull analysis: matchprism.com/match/..."

## IPL 2026 DATA TO HARDCODE

First match: March 28, 2026 - Royal Challengers Bengaluru vs Sunrisers Hyderabad at M. Chinnaswamy Stadium, Bengaluru

Teams and home venues:
- Royal Challengers Bengaluru (RCB) - M. Chinnaswamy Stadium, Bengaluru
- Sunrisers Hyderabad (SRH) - Rajiv Gandhi International Stadium, Hyderabad
- Chennai Super Kings (CSK) - MA Chidambaram Stadium, Chennai
- Mumbai Indians (MI) - Wankhede Stadium, Mumbai
- Kolkata Knight Riders (KKR) - Eden Gardens, Kolkata
- Delhi Capitals (DC) - Arun Jaitley Stadium, Delhi
- Rajasthan Royals (RR) - Sawai Mansingh Stadium, Jaipur
- Punjab Kings (PBKS) - IS Bindra Stadium, Mohali / HPCA Stadium, Dharamsala
- Gujarat Titans (GT) - Narendra Modi Stadium, Ahmedabad
- Lucknow Super Giants (LSG) - BRSABV Ekana Cricket Stadium, Lucknow

Groups (IPL 2026 format):
- Group A: CSK, KKR, RR, RCB, PBKS
- Group B: MI, SRH, GT, DC, LSG

## ENV VARS
- ODDS_API_KEY: API key for external probability data (optional, graceful fallback)
- NEXT_PUBLIC_SITE_URL: Base URL for share links (default: https://matchprism.com)

## KEY REQUIREMENTS
1. All match data is pre-computed by Python scripts and stored as static JSON
2. Next.js reads from static JSON files at build time (generateStaticParams + fetch from local files)
3. No server-side API calls at request time except optional client-side probability fetch
4. Site must work fully without external API keys (hides Value Analysis section)
5. Mobile-first - every component must look good on a 375px wide phone screen
6. Share functionality on Venue Card and Captain Genius sections
7. SEO: unique title/description per match page, og:image placeholder
8. Accessibility: minimum 11px font size (labels/captions), 14-16px body text, 4.5:1 contrast ratios, 44x44px touch targets
9. **CRITICAL: The brand name is "MatchPrism" in all headers, nav, titles, and share text. No gambling/betting language anywhere — use "analytics", "intelligence", "insights", "probability", "model confidence" instead.**
10. Performance: static site should score 90+ on Lighthouse
