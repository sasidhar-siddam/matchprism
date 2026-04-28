# MatchPrism - Data Sources

## Tier 1: FREE, No API Key

| Source | What | URL | Format |
|--------|------|-----|--------|
| Cricsheet | 1,169 IPL matches, ball-by-ball since 2008 | https://cricsheet.org/downloads/ipl_json.zip | JSON |
| Cricsheet (all T20) | 21,376 total matches across all formats | https://cricsheet.org/downloads/ | JSON/YAML/CSV |

## Tier 2: FREE with API Key

| Source | What | Limits | URL |
|--------|------|--------|-----|
| CricAPI / CricketData.org | Live scores, player stats, fantasy scorecards | 100K hits/hr | https://cricketdata.org/ |
| The Odds API | Bookmaker odds from Bet365, Sky Bet, etc. | 500 req/mo free | https://the-odds-api.com/ |
| GitHub cricket-api | Self-hosted live scores | Unlimited | https://github.com/sanwebinfo/cricket-api |

## Tier 3: Paid

| Source | What | Cost | URL |
|--------|------|------|-----|
| Roanuz Cricket API | Live WebSocket, ball-by-ball, fantasy points | $240/season | https://www.cricketapi.com/ |
| Entity Sport | Ultra-low latency, 250+ competitions | Free trial | https://www.entitysport.com/ |

## Scrapers (unofficial, use carefully)

| Source | What | URL |
|--------|------|-----|
| python-espncricinfo | Match details via Cricinfo internal JSON | https://github.com/outside-edge/python-espncricinfo |
| cricguru | Statsguru query results as Pandas DataFrames | https://github.com/puppetmaster12/cricguru |
| ESPNcricinfo commentary scraper | Ball-by-ball commentary text | https://github.com/AlbertBannister/cricinfo-commentary-scraper |

## Our Unique Data (from saasknowledgebase)
- 365,708 IPL/cricket Reddit posts across 17 subreddits
- Fan sentiment, predictions, complaints, player perception
- Located at: C:\Projects\saasknowledgebase\data\knowledgebase.db
