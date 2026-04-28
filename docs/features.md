# MatchPrism - Feature Spec

## Core Concept
One page per match, auto-generated from data. Published 2-3 hours before each IPL match. No manual work after initial build.

---

## V1 Features (IPL 2026 Season)

### 1. Venue Intelligence Card
**Data:** Cricsheet 1,169 IPL matches
- Average 1st/2nd innings score (all-time + last 2 seasons)
- Toss decision: bat/bowl first win %
- Pace vs Spin wicket split
- Phase breakdown: powerplay / middle / death overs avg runs
- Highest & lowest scores
- One-line "venue verdict"
- **Shareable as image card (WhatsApp/Twitter)**

### 2. Head-to-Head
**Data:** Cricsheet
- All-time record between the two teams
- Record at this specific venue
- Last 5 meetings with scores

### 3. Player Venue Fit Table
**Data:** Cricsheet + squad lists
- Every player's stats AT THIS GROUND vs their overall average
- Venue Fit Grade: A+ (>130% of overall), A (>115%), B (85-115%), C (60-85%), D (<60%)
- Batting: avg, SR, 50s, highest score at venue
- Bowling: wickets, economy, average at venue
- Last 5 match form

### 4. Captain Genius (Fantasy Pick)
**Data:** Cricsheet venue+player matrices
- Top 3 captain picks with data-backed reasoning
- "Avoid Today" picks (D-grade venue fit players)
- Reasoning: "Kohli averages 38.4 at Chinnaswamy vs 34.2 overall, SR 132.5 here"
- **Shareable card format**

### 5. Win Probability
**Data:** Cricsheet historical model
- Pre-match probability based on: venue advantage, H2H, recent form, squad venue fit
- Visual bar: "RCB 54% | SRH 46%"
- Post-toss update

### 6. Value Finder (Premium - toggleable)
**Data:** Model probabilities + The Odds API bookmaker odds
- Compare model probability vs bookmaker implied probability
- Flag value bets: "RCB at 1.85 is underpriced by 7.2%"
- Markets: match winner, top batsman, over/under total runs
- Graceful fallback if no odds available

### 7. New to Cricket (collapsible)
- What's a powerplay, DRS, impact player
- Baseball analogies for American users
- "Which team should I root for?" personality guide

---

## V1 NON-features (explicitly excluded)
- No live scores (need paid API)
- No user accounts / auth
- No fantasy league management
- No betting / real money
- No mobile app (web only)
- No LLM costs

---

## V2 Features (if V1 gains traction)
- Pitch Scanner (weather + pitch condition analysis: read weather APIs, pitch photos, dew forecasts → translate into actionable batting/bowling intelligence per match)
- Smart Builder (combined scenario analysis with model confidence %)
- Player Prop Insights mapped to probability markets
- Fan Pulse (Reddit sentiment per team from our 365K scraped posts)
- Live Edge Alerts (needs Roanuz API at $240/season)
- Telegram premium channel with instant captain picks
- Expand to Big Bash, The Hundred, SA20, PSL, CPL
- Football (Premier League) expansion

---

## Tech Architecture

```
Cricsheet data (1,169 matches)
    ↓ Python scripts (one-time processing)
Pre-computed JSON per venue/player/team
    ↓ generate_match_pages.py (per IPL fixture)
Static JSON per match
    ↓ Next.js static site (getStaticProps)
Match preview pages
    ↓ Share buttons
WhatsApp / Twitter / Reddit distribution
```

## Revenue Model
- **Free:** Venue cards, H2H, basic predictions, player table
- **Premium ($9.99-24.99/mo):** Captain Genius reasoning, Value Finder, Avoid picks, alerts
- **Telegram channel:** Free tier drives to premium
