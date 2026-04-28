"""
Generate per-match JSON files for IPL 2026 fixtures.

Combines venue stats, player stats, H2H records, and computes
win probability + captain picks for each match.
"""

import json
import os

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
MATCHES_DIR = os.path.join(PROCESSED_DIR, "matches")

# ── IPL 2026 Schedule (first 14 matches) ─────────────────────────────
# Format: (date, team1_full, team2_full, venue_canonical, time)
IPL_2026_SCHEDULE = [
    ("2026-03-28", "Royal Challengers Bengaluru", "Sunrisers Hyderabad", "M Chinnaswamy Stadium", "19:30 IST"),
    ("2026-03-29", "Mumbai Indians", "Chennai Super Kings", "Wankhede Stadium", "19:30 IST"),
    ("2026-03-30", "Kolkata Knight Riders", "Rajasthan Royals", "Eden Gardens", "19:30 IST"),
    ("2026-03-31", "Punjab Kings", "Delhi Capitals", "IS Bindra Stadium", "15:30 IST"),
    ("2026-03-31", "Lucknow Super Giants", "Gujarat Titans", "Ekana Cricket Stadium", "19:30 IST"),
    ("2026-04-01", "Sunrisers Hyderabad", "Mumbai Indians", "Rajiv Gandhi International Stadium", "19:30 IST"),
    ("2026-04-02", "Chennai Super Kings", "Kolkata Knight Riders", "MA Chidambaram Stadium", "19:30 IST"),
    ("2026-04-03", "Royal Challengers Bengaluru", "Rajasthan Royals", "M Chinnaswamy Stadium", "19:30 IST"),
    ("2026-04-04", "Gujarat Titans", "Delhi Capitals", "Narendra Modi Stadium", "19:30 IST"),
    ("2026-04-05", "Punjab Kings", "Lucknow Super Giants", "IS Bindra Stadium", "19:30 IST"),
    ("2026-04-06", "Mumbai Indians", "Kolkata Knight Riders", "Wankhede Stadium", "15:30 IST"),
    ("2026-04-06", "Sunrisers Hyderabad", "Chennai Super Kings", "Rajiv Gandhi International Stadium", "19:30 IST"),
    ("2026-04-07", "Rajasthan Royals", "Gujarat Titans", "Sawai Mansingh Stadium", "19:30 IST"),
    ("2026-04-08", "Royal Challengers Bengaluru", "Delhi Capitals", "M Chinnaswamy Stadium", "19:30 IST"),
]

# ── Team abbreviations ────────────────────────────────────────────────
TEAM_ABBR = {
    "Royal Challengers Bengaluru": "RCB",
    "Royal Challengers Bangalore": "RCB",
    "Sunrisers Hyderabad": "SRH",
    "Chennai Super Kings": "CSK",
    "Mumbai Indians": "MI",
    "Kolkata Knight Riders": "KKR",
    "Delhi Capitals": "DC",
    "Delhi Daredevils": "DC",
    "Rajasthan Royals": "RR",
    "Punjab Kings": "PBKS",
    "Kings XI Punjab": "PBKS",
    "Gujarat Titans": "GT",
    "Lucknow Super Giants": "LSG",
}

# ── IPL 2026 Official Squads (after mini-auction, Dec 16 2025) ────────
# Source: ESPNcricinfo, The Federal, Deccan Herald
# Note: Player names use Cricsheet format where possible for data matching.
# Cricsheet uses initials (e.g., "V Kohli" not "Virat Kohli").
IPL_2026_SQUADS = {
    "Royal Challengers Bengaluru": [
        "V Kohli", "RM Patidar", "D Padikkal", "PD Salt", "JM Sharma",
        "KH Pandya", "TH David", "R Shepherd", "JG Bethell", "JR Hazlewood",
        "Yash Dayal", "B Kumar", "N Thushara", "Rasikh Salam", "Suyash Sharma",
        "VR Iyer", "Abhinandan Singh", "JA Duffy", "Mangesh Yadav",
        "JM Cox", "VV Ostwal", "Vihaan Malhotra", "Kanishk Chouhan",
        "S Deswal", "Swapnil Singh",
    ],
    "Sunrisers Hyderabad": [
        "PJ Cummins", "TM Head", "Abhishek Sharma", "Ishan Kishan",
        "H Klaasen", "Nithish Kumar Reddy", "PHKD Mendis", "HV Patel",
        "Harsh Dubey", "JD Unadkat", "E Malinga", "Zeeshan Ansari",
        "Aniket Verma", "R Smaran", "LS Livingstone", "S Mavi",
        "BA Carse", "Shivang Kumar", "Salil Arora", "Sakib Hussain",
        "Onkar Tarmale", "Amit Kumar", "Praful Hinge", "Krains Fuletra",
        "JR Edwards",
    ],
    "Chennai Super Kings": [
        "MS Dhoni", "RD Gaikwad", "SV Samson", "S Dube", "Noor Ahmad",
        "KK Ahmed", "A Kamboj", "D Brevis", "J Overton", "NT Ellis",
        "Mukesh Choudhary", "Ramakrishna Ghosh", "Shreyas Gopal",
        "A Mhatre", "Urvil Patel", "Gurjapneet Singh",
        "Prashant Veer", "Kartik Sharma", "Rahul Chahar", "Akeal Hosein",
        "MJ Henry", "MW Short", "Sarfaraz Khan", "Z Foulkes", "Aman Khan",
    ],
    "Mumbai Indians": [
        "RG Sharma", "SA Yadav", "JJ Bumrah", "HH Pandya", "Tilak Varma",
        "TA Boult", "RD Rickelton", "WG Jacks", "MJ Santner", "Naman Dhir",
        "DL Chahar", "C Bosch", "Ashwani Kumar", "R Minz", "RA Bawa",
        "Q de Kock", "SN Thakur", "SE Rutherford", "Mayank Markande",
        "AM Ghazanfar", "Atharva Ankolekar", "Mohammad Izhar",
        "Danish Malewar", "Mayank Rawat", "Raghu Sharma",
    ],
    "Kolkata Knight Riders": [
        "AM Rahane", "A Raghuvanshi", "AS Roy", "Harshit Rana",
        "MK Pandey", "Ramandeep Singh", "RK Singh", "R Powell",
        "SP Narine", "Umran Malik", "VG Arora", "CV Varun",
        "C Green", "Mustafizur Rahman", "M Pathirana", "Tejasvi Singh",
        "FH Allen", "R Ravindra", "TL Seifert", "Akash Deep",
        "RA Tripathi", "Prashant Solanki", "Kartik Tyagi",
        "Sarthak Ranjan", "Daksh Kamra",
    ],
    "Delhi Capitals": [
        "AR Patel", "KL Rahul", "Kuldeep Yadav", "MA Starc",
        "T Natarajan", "T Stubbs", "Mukesh Kumar", "N Rana",
        "Abishek Porel", "Ashutosh Sharma", "Sameer Rizvi",
        "PVD Chameera", "KK Nair", "M Tiwari", "Ajay Mandal",
        "Tripurana Vijay", "V Nigam",
        "Auqib Nabi Dar", "P Nissanka", "DA Miller", "BA Duckett",
        "L Ngidi", "KA Jamieson", "PP Shaw", "Sahil Parikh",
    ],
    "Rajasthan Royals": [
        "RA Jadeja", "SM Curran", "D Ferreira", "Sandeep Sharma",
        "SB Dubey", "V Suryavanshi", "L du Plooy", "SO Hetmyer",
        "YBK Jaiswal", "Dhruv Jurel", "R Parag", "Yudhvir Singh",
        "JC Archer", "TU Deshpande", "KT Maphaka", "N Burger",
        "Ravi Bishnoi", "Sushant Mishra", "Yash Raj Punja",
        "V Puthur", "Ravi Singh", "Aman Rao", "Brijesh Sharma",
        "AF Milne", "Kuldeep Sen",
    ],
    "Punjab Kings": [
        "Arshdeep Singh", "Azmatullah Omarzai", "Harpreet Brar",
        "LH Ferguson", "M Jansen", "MP Stoinis", "MJ Owen",
        "Musheer Khan", "N Wadhera", "P Simran Singh", "Priyansh Arya",
        "SS Iyer", "Shashank Singh", "Suryansh Shedge",
        "Vijaykumar Vyshak", "XC Bartlett", "YS Chahal", "Yash Thakur",
        "BJ Dwarshuis", "C Connolly", "Vishnu Vinod",
        "Vishal Nishad", "P Dubey", "Harnoor Singh Pannu", "Pyla Avinash",
    ],
    "Gujarat Titans": [
        "Shubman Gill", "Rashid Khan", "B Sai Sudharsan", "K Rabada",
        "Mohammed Siraj", "Washington Sundar", "R Tewatia",
        "M Shahrukh Khan", "M Prasidh Krishna", "R Sai Kishore",
        "I Sharma", "Arshad Khan", "Nishant Sindhu", "Anuj Rawat",
        "GD Phillips", "Gurnoor Brar", "Jayant Yadav", "JC Buttler",
        "Kumar Kushagra", "Manav Suthar", "JO Holder", "T Banton",
        "Ashok Sharma", "L Wood", "Prithvi Raj",
    ],
    "Lucknow Super Giants": [
        "RR Pant", "MR Marsh", "AK Markram", "Abdul Samad",
        "Avesh Khan", "A Badoni", "Shahbaz Ahmed", "DS Rathi",
        "Himmat Singh", "M Siddharth", "MP Breetzke", "MP Yadav",
        "Mohsin Khan", "N Pooran", "Prince Yadav",
        "Mohammed Shami", "Akash Singh",
        "JR Inglis", "Mukul Choudhary", "Akshat Raghuwanshi",
        "Wanindu Hasaranga", "A Nortje", "Naman Tiwari",
        "Arjun Tendulkar", "Arshin Kulkarni",
    ],
}


def load_data():
    with open(os.path.join(PROCESSED_DIR, "venues.json")) as f:
        venues = json.load(f)
    with open(os.path.join(PROCESSED_DIR, "players.json")) as f:
        players = json.load(f)
    with open(os.path.join(PROCESSED_DIR, "h2h.json")) as f:
        h2h = json.load(f)
    return venues, players, h2h


def get_h2h(h2h_data, team1_full, team2_full):
    """Find the H2H record for two teams."""
    key1 = f"{team1_full} vs {team2_full}"
    key2 = f"{team2_full} vs {team1_full}"
    return h2h_data.get(key1) or h2h_data.get(key2)


def get_player_venue_stats(players_data, player_name, venue_name):
    """Get a player's stats at a specific venue."""
    player = players_data.get(player_name)
    if not player:
        return None
    venue_stats = player.get("venues", {}).get(venue_name)
    return venue_stats, player


def compute_win_probability(venue, h2h_record, team1_full, team2_full,
                            team1_players, team2_players, players_data, venue_name):
    """
    Simple win probability model:
    - 50% base
    - Home venue advantage: +5% for home team
    - H2H weighting (20%): shifts based on historical record
    - Squad strength (30%): avg venue fit grade score
    """
    prob = 50.0

    # Home advantage: team1 is usually home in our schedule
    # Check if venue matches team's home ground
    home_venues = {
        "Royal Challengers Bengaluru": "M Chinnaswamy Stadium",
        "Sunrisers Hyderabad": "Rajiv Gandhi International Stadium",
        "Chennai Super Kings": "MA Chidambaram Stadium",
        "Mumbai Indians": "Wankhede Stadium",
        "Kolkata Knight Riders": "Eden Gardens",
        "Delhi Capitals": "Arun Jaitley Stadium",
        "Rajasthan Royals": "Sawai Mansingh Stadium",
        "Punjab Kings": "IS Bindra Stadium",
        "Gujarat Titans": "Narendra Modi Stadium",
        "Lucknow Super Giants": "Ekana Cricket Stadium",
    }
    if home_venues.get(team1_full) == venue_name:
        prob += 5
    elif home_venues.get(team2_full) == venue_name:
        prob -= 5

    # H2H weighting (20% of model)
    if h2h_record:
        t1_key = "team1" if h2h_record["team1"] == team1_full else "team2"
        t2_key = "team2" if t1_key == "team1" else "team1"
        t1_wins = h2h_record[f"{t1_key}Wins"]
        t2_wins = h2h_record[f"{t2_key}Wins"]
        total = t1_wins + t2_wins
        if total > 0:
            h2h_edge = ((t1_wins / total) - 0.5) * 20  # max ±10
            prob += h2h_edge

    # Squad strength via venue grades (30% of model)
    grade_scores = {"A+": 5, "A": 4, "B": 3, "C": 2, "D": 1, "N/A": 3}

    def avg_grade_score(player_names):
        scores = []
        for name in player_names:
            vs, _ = get_player_venue_stats(players_data, name, venue_name) or (None, None)
            if vs and vs.get("grade"):
                scores.append(grade_scores.get(vs["grade"], 3))
            else:
                scores.append(3)  # neutral if unknown
        return sum(scores) / len(scores) if scores else 3

    t1_score = avg_grade_score(team1_players)
    t2_score = avg_grade_score(team2_players)
    if t1_score + t2_score > 0:
        strength_edge = ((t1_score - t2_score) / 5) * 15  # max ±15
        prob += strength_edge

    # Clamp
    prob = max(20, min(80, prob))
    return round(prob)


def generate_captain_picks(team1_players, team2_players, players_data, venue_name):
    """Rank players by venue performance and return top 3 + avoid picks."""
    candidates = []

    for player_name in team1_players + team2_players:
        result = get_player_venue_stats(players_data, player_name, venue_name)
        if not result or not result[0]:
            continue
        venue_stats, player_data = result
        batting = venue_stats.get("batting", {})
        bowling = venue_stats.get("bowling", {})
        grade = venue_stats.get("grade", "N/A")

        # Score: batters by avg * SR, bowlers by wickets / economy
        bat_score = 0
        bowl_score = 0
        if batting.get("innings", 0) >= 3:
            avg = batting.get("average", 0)
            sr = batting.get("strikeRate", 0)
            bat_score = avg * (sr / 100) if sr > 0 else 0

        if bowling.get("innings", 0) >= 3:
            wickets = bowling.get("wickets", 0)
            econ = bowling.get("economy", 99)
            bowl_score = (wickets / max(bowling.get("innings", 1), 1)) / max(econ / 8, 0.5) * 30

        total_score = max(bat_score, bowl_score)

        # Determine role
        role = "Batter"
        if bowl_score > bat_score and bowling.get("innings", 0) >= 3:
            role = "Bowler"
        elif bowl_score > 0 and bat_score > 0:
            role = "All-rounder"

        # Find team
        team = None
        for t in player_data.get("teams", []):
            abbr = TEAM_ABBR.get(t)
            if abbr:
                team = abbr
        if not team:
            team = player_data.get("teams", [""])[0]

        # Build reasoning
        reasoning_parts = []
        if batting.get("innings", 0) >= 3:
            reasoning_parts.append(
                f"Averages {batting.get('average', 0)} at this venue "
                f"(SR {batting.get('strikeRate', 0)}) in {batting['innings']} innings."
            )
        if bowling.get("innings", 0) >= 3:
            reasoning_parts.append(
                f"Takes {bowling.get('wickets', 0)} wickets here at economy {bowling.get('economy', 0)}."
            )
        if batting.get("sixes", 0) > 5:
            reasoning_parts.append(f"Has hit {batting['sixes']} sixes at this ground.")

        # Projected points (fantasy-style range)
        base = int(total_score * 1.5)
        proj_low = max(40, base - 15)
        proj_high = base + 20

        candidates.append({
            "playerName": player_name,
            "team": team,
            "role": role,
            "grade": grade,
            "score": total_score,
            "venueAvg": batting.get("average", 0),
            "venueSR": batting.get("strikeRate", 0),
            "venueEcon": bowling.get("economy"),
            "last5": player_data.get("last5", []),
            "reasoning": " ".join(reasoning_parts) if reasoning_parts else "Limited venue data available.",
            "projectedPoints": f"{proj_low} - {proj_high}",
        })

    # Sort by score descending
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # Top 3 picks
    picks = candidates[:3]

    # Avoid picks: players with D or C grade who are likely to play
    avoid = [
        {
            "playerName": c["playerName"],
            "team": c["team"],
            "grade": c["grade"],
            "reason": f"Below-average venue record (Grade {c['grade']}). "
                      f"Venue avg {c['venueAvg']} suggests poor conditions fit.",
        }
        for c in candidates
        if c["grade"] in ("D", "C") and c["score"] > 0
    ][:2]

    return picks, avoid


def build_advanced_analysis(team1_prob, team1_full, team2_full, venue):
    """Generate model vs implied probability comparison rows."""
    rows = []

    # Match winner
    implied1 = max(20, team1_prob - 3 + (2 if team1_prob > 50 else -2))
    edge1 = round(team1_prob - implied1, 1)
    rows.append({
        "outcome": f"{TEAM_ABBR[team1_full]} Home Win",
        "modelProb": team1_prob,
        "impliedProb": implied1,
        "edge": edge1,
        "verdict": "VALUE" if edge1 > 2 else ("FAIR" if edge1 > -2 else "AVOID"),
    })

    # High-scoring game
    avg = venue.get("avg1stInnings", 160)
    high_prob = min(75, max(25, round(50 + (avg - 165) * 1.5)))
    implied_high = high_prob - 1
    edge_high = round(high_prob - implied_high, 1)
    rows.append({
        "outcome": f"Total Match Sixes > {int(venue.get('sixesPerInnings', 6) * 1.8)}",
        "modelProb": high_prob,
        "impliedProb": implied_high,
        "edge": edge_high,
        "verdict": "FAIR",
    })

    # Chase win
    chase_prob = venue.get("chaseWinPct", 50)
    implied_chase = chase_prob + 3
    edge_chase = round(chase_prob - implied_chase, 1)
    rows.append({
        "outcome": "Chasing Team Wins",
        "modelProb": chase_prob,
        "impliedProb": implied_chase,
        "edge": edge_chase,
        "verdict": "AVOID" if edge_chase < -2 else "FAIR",
    })

    return rows


def format_date(date_str):
    """Convert 2026-03-28 to March 28, 2026."""
    months = ["", "January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    parts = date_str.split("-")
    return f"{months[int(parts[1])]} {int(parts[2])}, {parts[0]}"


def generate_match(fixture, venues, players, h2h):
    date_str, team1_full, team2_full, venue_name, time_str = fixture
    team1 = TEAM_ABBR[team1_full]
    team2 = TEAM_ABBR[team2_full]
    slug = f"{team1.lower()}-vs-{team2.lower()}"

    # Venue
    venue = venues.get(venue_name, {})

    # H2H
    h2h_record = get_h2h(h2h, team1_full, team2_full)

    # Players
    team1_players = IPL_2026_SQUADS.get(team1_full, [])
    team2_players = IPL_2026_SQUADS.get(team2_full, [])

    # Win probability
    team1_prob = compute_win_probability(
        venue, h2h_record, team1_full, team2_full,
        team1_players, team2_players, players, venue_name
    )
    team2_prob = 100 - team1_prob

    # Captain picks
    picks, avoid = generate_captain_picks(
        team1_players, team2_players, players, venue_name
    )

    # H2H formatted
    h2h_out = {"team1Wins": 0, "team2Wins": 0, "recentMatches": []}
    if h2h_record:
        if h2h_record["team1"] == team1_full:
            h2h_out["team1Wins"] = h2h_record["team1Wins"]
            h2h_out["team2Wins"] = h2h_record["team2Wins"]
        else:
            h2h_out["team1Wins"] = h2h_record["team2Wins"]
            h2h_out["team2Wins"] = h2h_record["team1Wins"]

        for m in h2h_record.get("recentMatches", [])[:5]:
            h2h_out["recentMatches"].append({
                "date": m["date"],
                "venue": m["venue"],
                "team1": TEAM_ABBR.get(m.get("team1", ""), m.get("team1", "")),
                "team1Score": m.get("team1Score", ""),
                "team2": TEAM_ABBR.get(m.get("team2", ""), m.get("team2", "")),
                "team2Score": m.get("team2Score", ""),
                "winner": TEAM_ABBR.get(m.get("winner", ""), m.get("winner", "")),
                "margin": m.get("margin", ""),
            })

    # Player venue fit tables
    def player_fit_list(player_names, team_abbr):
        rows = []
        for name in player_names:
            result = get_player_venue_stats(players, name, venue_name)
            if not result or not result[0]:
                continue
            vs, pd = result
            batting = vs.get("batting", {})
            bowling = vs.get("bowling", {})
            role = "Batter"
            if bowling.get("innings", 0) > batting.get("innings", 0):
                role = "Bowler"
            elif bowling.get("innings", 0) >= 3 and batting.get("innings", 0) >= 3:
                role = "All-rounder"

            rows.append({
                "name": name,
                "team": team_abbr,
                "role": role,
                "venueAvg": batting.get("average", 0),
                "venueSR": batting.get("strikeRate", 0),
                "venueEcon": bowling.get("economy"),
                "grade": vs.get("grade", "N/A"),
                "last5": pd.get("last5", []),
                "overallAvg": pd.get("overall", {}).get("batting", {}).get("average", 0),
            })
        rows.sort(key=lambda x: {"A+": 5, "A": 4, "B": 3, "C": 2, "D": 1, "N/A": 0}.get(x["grade"], 0), reverse=True)
        return rows

    # Advanced analysis
    analysis = build_advanced_analysis(team1_prob, team1_full, team2_full, venue)

    # Model confidence (based on data availability)
    data_points = len(team1_players) + len(team2_players) + venue.get("totalMatches", 0)
    confidence = min(95, max(60, 70 + data_points // 5))

    match_data = {
        "slug": slug,
        "date": format_date(date_str),
        "dateRaw": date_str,
        "time": time_str,
        "team1": team1,
        "team2": team2,
        "team1Full": team1_full,
        "team2Full": team2_full,
        "venue": venue,
        "team1WinProb": team1_prob,
        "team2WinProb": team2_prob,
        "modelConfidence": confidence,
        "captainPicks": picks,
        "avoidPicks": avoid,
        "h2h": h2h_out,
        "playerFit": {
            "team1": player_fit_list(team1_players, team1),
            "team2": player_fit_list(team2_players, team2),
        },
        "advancedAnalysis": analysis,
    }

    return match_data


def main():
    print("Loading processed data...")
    venues, players, h2h = load_data()
    print(f"  Venues: {len(venues)}, Players: {len(players)}, H2H pairs: {len(h2h)}")

    os.makedirs(MATCHES_DIR, exist_ok=True)

    all_matches = []
    for fixture in IPL_2026_SCHEDULE:
        match = generate_match(fixture, venues, players, h2h)
        filename = f"{fixture[0]}-{match['slug']}.json"
        filepath = os.path.join(MATCHES_DIR, filename)
        with open(filepath, "w") as f:
            json.dump(match, f, indent=2)
        all_matches.append(match)
        print(f"  Generated: {filename} | {match['team1']} {match['team1WinProb']}% vs {match['team2']} {match['team2WinProb']}% | Captain: {match['captainPicks'][0]['playerName'] if match['captainPicks'] else 'N/A'}")

    # Also write a schedule index
    schedule = []
    for m in all_matches:
        schedule.append({
            "slug": m["slug"],
            "date": m["date"],
            "dateRaw": m["dateRaw"],
            "time": m["time"],
            "team1": m["team1"],
            "team2": m["team2"],
            "team1Full": m["team1Full"],
            "team2Full": m["team2Full"],
            "venue": m["venue"]["name"] if m["venue"] else "TBD",
            "city": m["venue"].get("city", "") if m["venue"] else "",
            "team1WinProb": m["team1WinProb"],
            "team2WinProb": m["team2WinProb"],
            "modelConfidence": m["modelConfidence"],
        })

    with open(os.path.join(PROCESSED_DIR, "schedule.json"), "w") as f:
        json.dump(schedule, f, indent=2)

    print(f"\nDone! Generated {len(all_matches)} match files + schedule.json")


if __name__ == "__main__":
    main()
