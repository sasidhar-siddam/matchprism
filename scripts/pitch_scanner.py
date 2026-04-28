"""
Pitch Scanner — Conditions Intelligence Engine

Combines historical match data with live weather to produce
a per-match conditions report covering:
  1. Dew probability & impact
  2. Pitch behavior (pace vs spin friendliness by phase)
  3. Overhead conditions (cloud cover → swing potential)
  4. Temperature & humidity impact on ball behavior
  5. Wind factor (ground dimensions + wind speed)
  6. Toss recommendation with confidence
  7. Overall conditions verdict

Data sources:
  - Historical: 6,856 T20 matches from Cricsheet (seasonal patterns, venue behavior)
  - Live: OpenWeatherMap free API (temperature, humidity, wind, clouds, dew point)
"""

import json
import math
import os
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import datetime

from venue_map import normalize_venue

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

# ── Venue coordinates for weather lookup ──────────────────────────────
VENUE_COORDS = {
    "M Chinnaswamy Stadium": {"lat": 12.9788, "lon": 77.5996, "altitude_m": 920, "boundary_avg_m": 60},
    "Wankhede Stadium": {"lat": 18.9389, "lon": 72.8258, "altitude_m": 14, "boundary_avg_m": 65},
    "Eden Gardens": {"lat": 22.5646, "lon": 88.3433, "altitude_m": 9, "boundary_avg_m": 68},
    "MA Chidambaram Stadium": {"lat": 13.0629, "lon": 80.2792, "altitude_m": 6, "boundary_avg_m": 62},
    "Rajiv Gandhi International Stadium": {"lat": 17.4065, "lon": 78.5507, "altitude_m": 542, "boundary_avg_m": 64},
    "Arun Jaitley Stadium": {"lat": 28.6365, "lon": 77.2419, "altitude_m": 216, "boundary_avg_m": 63},
    "Sawai Mansingh Stadium": {"lat": 26.8933, "lon": 75.8077, "altitude_m": 431, "boundary_avg_m": 66},
    "IS Bindra Stadium": {"lat": 30.6928, "lon": 76.7375, "altitude_m": 316, "boundary_avg_m": 65},
    "Narendra Modi Stadium": {"lat": 23.0918, "lon": 72.5957, "altitude_m": 53, "boundary_avg_m": 76},
    "Ekana Cricket Stadium": {"lat": 26.8470, "lon": 80.9556, "altitude_m": 123, "boundary_avg_m": 70},
    "HPCA Stadium": {"lat": 32.2175, "lon": 76.3234, "altitude_m": 1457, "boundary_avg_m": 58},
    "MCA Stadium": {"lat": 18.6777, "lon": 73.8741, "altitude_m": 562, "boundary_avg_m": 68},
    "DY Patil Stadium": {"lat": 19.0453, "lon": 73.1029, "altitude_m": 10, "boundary_avg_m": 67},
    # International venues
    "Dubai International Cricket Stadium": {"lat": 25.0569, "lon": 55.2097, "altitude_m": 5, "boundary_avg_m": 75},
    "Sharjah Cricket Stadium": {"lat": 25.3387, "lon": 55.4041, "altitude_m": 5, "boundary_avg_m": 62},
    "Sheikh Zayed Stadium": {"lat": 24.4539, "lon": 54.6097, "altitude_m": 5, "boundary_avg_m": 72},
    "Shere Bangla National Stadium, Mirpur": {"lat": 23.8069, "lon": 90.3628, "altitude_m": 8, "boundary_avg_m": 64},
    "Melbourne Cricket Ground": {"lat": -37.82, "lon": 144.9834, "altitude_m": 30, "boundary_avg_m": 78},
    "Sydney Cricket Ground": {"lat": -33.8916, "lon": 151.2249, "altitude_m": 45, "boundary_avg_m": 65},
    "Brisbane Cricket Ground, Woolloongabba": {"lat": -27.4858, "lon": 153.0381, "altitude_m": 15, "boundary_avg_m": 68},
    "National Stadium": {"lat": 24.8922, "lon": 67.0667, "altitude_m": 10, "boundary_avg_m": 70},
    "Gaddafi Stadium": {"lat": 31.5133, "lon": 74.3397, "altitude_m": 208, "boundary_avg_m": 68},
    "R.Premadasa Stadium": {"lat": 6.9147, "lon": 79.8719, "altitude_m": 7, "boundary_avg_m": 62},
    "Newlands": {"lat": -33.9268, "lon": 18.4137, "altitude_m": 15, "boundary_avg_m": 68},
    "SuperSport Park": {"lat": -25.7478, "lon": 28.2114, "altitude_m": 1340, "boundary_avg_m": 70},
}


def compute_historical_conditions(venue_name):
    """
    Mine historical data for this venue to understand:
    - Monthly scoring patterns (dew proxy)
    - Pace vs spin phase behavior
    - Toss decision patterns and outcomes
    - Innings-by-innings progression
    """
    monthly = defaultdict(lambda: {
        "matches": 0,
        "chase_wins": 0, "bat_first_wins": 0,
        "toss_bowl": 0, "toss_bat": 0,
        "toss_bowl_wins": 0, "toss_bat_wins": 0,
        "avg_1st": [], "avg_2nd": [],
        "pp_1st": [], "pp_2nd": [],     # powerplay
        "mid_1st": [], "mid_2nd": [],    # middle overs
        "death_1st": [], "death_2nd": [], # death overs
        "wickets_pp_1st": [], "wickets_pp_2nd": [],
    })

    for league in os.listdir(RAW_DIR):
        league_dir = os.path.join(RAW_DIR, league)
        if not os.path.isdir(league_dir):
            continue
        for f in os.listdir(league_dir):
            if not f.endswith(".json"):
                continue
            with open(os.path.join(league_dir, f)) as fh:
                m = json.load(fh)

            info = m.get("info", {})
            v = normalize_venue(info.get("venue", ""))
            if v != venue_name:
                continue

            dates = info.get("dates", [])
            if not dates:
                continue
            month = int(dates[0].split("-")[1])
            outcome = info.get("outcome", {})
            winner = outcome.get("winner")
            toss = info.get("toss", {})

            ms = monthly[month]
            ms["matches"] += 1

            # Toss
            toss_decision = toss.get("decision", "")
            toss_winner = toss.get("winner", "")
            if toss_decision == "bat":
                ms["toss_bat"] += 1
                if winner == toss_winner:
                    ms["toss_bat_wins"] += 1
            else:
                ms["toss_bowl"] += 1
                if winner == toss_winner:
                    ms["toss_bowl_wins"] += 1

            # Innings analysis
            for i, inn in enumerate(m.get("innings", [])):
                if i >= 2:
                    break  # skip super overs
                pp_runs = mid_runs = death_runs = 0
                pp_wkts = 0
                total = 0
                for ov in inn.get("overs", []):
                    over_num = ov.get("over", 0)
                    for dl in ov.get("deliveries", []):
                        runs = dl["runs"]["total"]
                        total += runs
                        if over_num <= 5:
                            pp_runs += runs
                            if "wickets" in dl:
                                pp_wkts += len(dl["wickets"])
                        elif over_num <= 14:
                            mid_runs += runs
                        else:
                            death_runs += runs

                suffix = "_1st" if i == 0 else "_2nd"
                ms[f"avg{suffix}"].append(total)
                ms[f"pp{suffix}"].append(pp_runs)
                ms[f"mid{suffix}"].append(mid_runs)
                ms[f"death{suffix}"].append(death_runs)
                ms[f"wickets_pp{suffix}"].append(pp_wkts)

            # Chase vs bat first
            if winner and len(m.get("innings", [])) >= 2:
                batting_first = m["innings"][0].get("team", "")
                if winner == batting_first:
                    ms["bat_first_wins"] += 1
                else:
                    ms["chase_wins"] += 1

    return dict(monthly)


def fetch_weather(lat, lon, api_key=None):
    """
    Fetch current + forecast weather from OpenWeatherMap.
    Returns None if no API key or network fails.
    """
    key = api_key or os.environ.get("OPENWEATHER_API_KEY")
    if not key:
        return None

    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={key}&units=metric"
        )
        resp = urllib.request.urlopen(url, timeout=10)
        current = json.loads(resp.read())

        # Also get 5-day forecast for match-day
        furl = (
            f"https://api.openweathermap.org/data/2.5/forecast"
            f"?lat={lat}&lon={lon}&appid={key}&units=metric"
        )
        fresp = urllib.request.urlopen(furl, timeout=10)
        forecast = json.loads(fresp.read())

        return {"current": current, "forecast": forecast}
    except (urllib.error.URLError, Exception):
        return None


def compute_dew_probability(month, hour, humidity, temp, venue_coords):
    """
    Estimate dew probability based on:
    - Time of day (dew increases after sunset, ~18:30 IST)
    - Humidity (>65% = significant dew risk)
    - Temperature drop (dew forms when air cools to dew point)
    - Altitude (higher = cooler evenings = more dew)
    - Month (Apr-May peak dew in India)
    """
    base = 20  # base probability

    # Time factor: evening matches have more dew
    if hour >= 19:
        base += 25
    elif hour >= 16:
        base += 10

    # Humidity factor
    if humidity > 80:
        base += 25
    elif humidity > 65:
        base += 15
    elif humidity > 50:
        base += 5

    # Temperature: cooler = more condensation
    if temp < 25:
        base += 10
    elif temp < 30:
        base += 5

    # Month factor (peak dew in Indian subcontinent)
    if month in (4, 5, 10, 11):
        base += 10
    elif month in (6, 7, 8, 9):  # monsoon = very high humidity
        base += 15

    # Altitude bonus (Dharamsala, Chinnaswamy)
    altitude = venue_coords.get("altitude_m", 0) if venue_coords else 0
    if altitude > 800:
        base += 10
    elif altitude > 400:
        base += 5

    return min(95, max(5, base))


def compute_swing_potential(temp, humidity, cloud_cover, wind_speed):
    """
    Estimate swing bowling potential:
    - Overcast conditions (cloud > 60%) = conventional swing
    - Humidity > 70% = ball stays shiny longer
    - Temperature 18-25C = optimal for swing
    - Wind 10-20 km/h = helps swing, >25 = too much
    """
    score = 30  # base

    # Cloud cover
    if cloud_cover > 80:
        score += 25
    elif cloud_cover > 60:
        score += 15
    elif cloud_cover > 40:
        score += 5

    # Humidity
    if humidity > 80:
        score += 20
    elif humidity > 65:
        score += 10

    # Temperature sweet spot
    if 18 <= temp <= 25:
        score += 15
    elif 15 <= temp <= 30:
        score += 5

    # Wind
    if 10 <= wind_speed <= 20:
        score += 10
    elif wind_speed > 25:
        score -= 5

    return min(95, max(5, score))


def compute_spin_potential(temp, humidity, pitch_age_days=None):
    """
    Estimate spin friendliness:
    - Hot + dry = crumbling pitch = spin
    - Low humidity = dry surface
    - Later in tournament = more worn pitches
    """
    score = 30

    if temp > 35:
        score += 20
    elif temp > 30:
        score += 10

    if humidity < 40:
        score += 15
    elif humidity < 55:
        score += 5

    return min(95, max(5, score))


def compute_altitude_factor(altitude_m, boundary_avg_m):
    """
    Altitude effect on ball travel:
    - Higher altitude = thinner air = ball travels further
    - Chinnaswamy (920m) and Dharamsala (1457m) are significantly affected
    - Smaller boundaries compound the effect
    """
    # Ball travels ~1.5% further per 300m altitude
    travel_bonus_pct = (altitude_m / 300) * 1.5
    # Boundary factor: smaller boundaries = more impact
    boundary_factor = max(0.5, (70 - boundary_avg_m) / 10) if boundary_avg_m else 1.0

    six_probability_boost = round(travel_bonus_pct * (1 + boundary_factor * 0.3), 1)

    return {
        "altitude_m": altitude_m,
        "boundary_avg_m": boundary_avg_m,
        "ball_travel_bonus_pct": round(travel_bonus_pct, 1),
        "six_probability_boost_pct": six_probability_boost,
        "impact": "High" if six_probability_boost > 5 else ("Moderate" if six_probability_boost > 2 else "Low"),
    }


def generate_toss_recommendation(historical_month, dew_prob, chase_pct_venue):
    """
    Recommend toss decision based on conditions.
    """
    bowl_score = 50

    # Dew favors chasing
    if dew_prob > 70:
        bowl_score += 20
    elif dew_prob > 50:
        bowl_score += 10

    # Historical chase success
    if chase_pct_venue > 60:
        bowl_score += 15
    elif chase_pct_venue > 55:
        bowl_score += 8
    elif chase_pct_venue < 45:
        bowl_score -= 10

    # Historical toss outcomes for this month
    if historical_month:
        toss_bowl = historical_month.get("toss_bowl", 0)
        toss_bowl_wins = historical_month.get("toss_bowl_wins", 0)
        if toss_bowl > 5:
            bowl_win_rate = toss_bowl_wins / toss_bowl * 100
            if bowl_win_rate > 55:
                bowl_score += 10
            elif bowl_win_rate < 45:
                bowl_score -= 10

    bowl_score = min(90, max(10, bowl_score))
    decision = "Bowl First" if bowl_score > 55 else ("Bat First" if bowl_score < 45 else "Marginal - Bowl Slight Edge")
    confidence = abs(bowl_score - 50) * 2

    return {
        "recommendation": decision,
        "bowlFirstProbability": bowl_score,
        "confidence": min(95, confidence),
        "reasoning": [],
    }


def generate_pitch_report(venue_name, match_date_str, match_time="19:30",
                          weather_data=None, api_key=None):
    """
    Generate a complete pitch/conditions report for a match.
    """
    # Parse date
    date_parts = match_date_str.split("-")
    month = int(date_parts[1])
    hour = int(match_time.split(":")[0])

    # Venue metadata
    coords = VENUE_COORDS.get(venue_name, {})
    altitude = coords.get("altitude_m", 0)
    boundary = coords.get("boundary_avg_m", 65)

    # Historical data
    historical = compute_historical_conditions(venue_name)
    month_data = historical.get(month, {})

    # Weather (live or default estimates)
    if not weather_data and coords:
        weather_data = fetch_weather(coords.get("lat"), coords.get("lon"), api_key)

    if weather_data and weather_data.get("current"):
        wx = weather_data["current"]
        temp = wx.get("main", {}).get("temp", 28)
        humidity = wx.get("main", {}).get("humidity", 60)
        wind_speed = wx.get("wind", {}).get("speed", 10) * 3.6  # m/s to km/h
        clouds = wx.get("clouds", {}).get("all", 30)
        dew_point = wx.get("main", {}).get("dew_point")
        description = wx.get("weather", [{}])[0].get("description", "")
        weather_source = "live"
    else:
        # Defaults based on Indian venue seasonal norms
        temp = 32 if month in (4, 5) else 28
        humidity = 65 if month in (4, 5, 10, 11) else 55
        wind_speed = 12
        clouds = 25
        dew_point = None
        description = "Clear sky (estimated)"
        weather_source = "estimated"

    # ── Compute match-day variable factors ──
    dew_prob = compute_dew_probability(month, hour, humidity, temp, coords)
    swing = compute_swing_potential(temp, humidity, clouds, wind_speed)
    spin = compute_spin_potential(temp, humidity)

    # Historical chase % for this month at this venue
    chase_wins = month_data.get("chase_wins", 0)
    bat_wins = month_data.get("bat_first_wins", 0)
    total_decided = chase_wins + bat_wins
    chase_pct = (chase_wins / total_decided * 100) if total_decided > 5 else 55

    # Phase analysis for this month
    def safe_avg(lst):
        return round(sum(lst) / len(lst), 1) if lst else 0

    pp_1st = safe_avg(month_data.get("pp_1st", []))
    pp_2nd = safe_avg(month_data.get("pp_2nd", []))
    mid_1st = safe_avg(month_data.get("mid_1st", []))
    mid_2nd = safe_avg(month_data.get("mid_2nd", []))
    death_1st = safe_avg(month_data.get("death_1st", []))
    death_2nd = safe_avg(month_data.get("death_2nd", []))
    avg_1st = safe_avg(month_data.get("avg_1st", []))
    avg_2nd = safe_avg(month_data.get("avg_2nd", []))

    # Toss recommendation
    toss = generate_toss_recommendation(month_data, dew_prob, chase_pct)

    # Build reasoning — only match-day variable factors
    reasoning = []
    if dew_prob > 60:
        reasoning.append(f"Heavy dew expected ({dew_prob}% probability) — significant advantage to chasing team.")
    elif dew_prob > 40:
        reasoning.append(f"Moderate dew likely ({dew_prob}%) — slight edge to team batting second.")
    elif dew_prob < 20:
        reasoning.append("Minimal dew expected — conditions neutral for both innings.")

    if swing > 60:
        reasoning.append(f"Overcast/humid conditions favor swing bowling (potential: {swing}%). Pace bowlers in powerplay critical.")
    elif swing > 45:
        reasoning.append(f"Moderate swing conditions ({swing}%) — new ball movement likely in first 4 overs.")
    elif swing < 30:
        reasoning.append("Clear skies and low humidity — minimal swing expected. Spin could play a role in middle overs.")

    if temp > 35:
        reasoning.append(f"Extreme heat ({temp}C) — pitch likely to dry out faster. Spin advantage increases as match progresses.")
    elif temp < 22:
        reasoning.append(f"Cool conditions ({temp}C) — ball will swing more, expect lower totals than average.")

    if clouds > 70:
        reasoning.append("Heavy cloud cover — bowlers should dominate early. Overcast conditions aid seam movement.")
    elif clouds < 15:
        reasoning.append("Clear skies — batting-friendly overhead conditions, no assistance for seamers.")

    if humidity > 80:
        reasoning.append(f"Very high humidity ({humidity}%) — ball will stay shiny longer, grip harder for spinners.")
    elif humidity < 35:
        reasoning.append(f"Dry conditions ({humidity}% humidity) — ball will roughen quickly, reverse swing possible in death overs.")

    toss["reasoning"] = reasoning

    # Overall match-day conditions verdict (only variable factors)
    conditions = []
    if dew_prob > 50:
        conditions.append("dew-affected")
    if swing > 55:
        conditions.append("pace-friendly overhead")
    if spin > 55:
        conditions.append("spin-friendly surface")
    if temp > 35:
        conditions.append("extreme heat")
    if clouds > 70:
        conditions.append("overcast")
    if humidity > 75:
        conditions.append("high humidity")

    verdict = "Standard conditions — no significant weather advantage"
    if conditions:
        verdict = f"Match-day conditions: {', '.join(conditions)}"

    return {
        "venue": venue_name,
        "matchDate": match_date_str,
        "matchTime": match_time,
        "weatherSource": weather_source,
        "weather": {
            "temperature": round(temp, 1),
            "humidity": humidity,
            "windSpeed": round(wind_speed, 1),
            "windUnit": "km/h",
            "cloudCover": clouds,
            "dewPoint": round(dew_point, 1) if dew_point else None,
            "description": description,
        },
        "dewAnalysis": {
            "probability": dew_prob,
            "impact": "Heavy" if dew_prob > 70 else ("Moderate" if dew_prob > 40 else "Low"),
            "secondInningsAdvantage": dew_prob > 50,
        },
        "pitchBehavior": {
            "swingPotential": swing,
            "spinPotential": spin,
            "paceFriendly": swing > 50,
            "spinFriendly": spin > 50,
        },
        "phaseAnalysis": {
            "month": month,
            "sampleSize": month_data.get("matches", 0),
            "powerplay": {"firstInnings": pp_1st, "secondInnings": pp_2nd, "delta": round(pp_2nd - pp_1st, 1)},
            "middleOvers": {"firstInnings": mid_1st, "secondInnings": mid_2nd, "delta": round(mid_2nd - mid_1st, 1)},
            "deathOvers": {"firstInnings": death_1st, "secondInnings": death_2nd, "delta": round(death_2nd - death_1st, 1)},
            "totalFirst": avg_1st,
            "totalSecond": avg_2nd,
            "scoringDelta": round(avg_2nd - avg_1st, 1),
        },
        "tossIntelligence": toss,
        "historicalChaseWinPct": round(chase_pct, 1),
        "conditionsTags": conditions,
        "verdict": verdict,
        "reasoning": reasoning,
    }


def main():
    """Generate pitch reports for all IPL 2026 fixtures."""
    # Load schedule
    schedule_path = os.path.join(PROCESSED_DIR, "schedule.json")
    with open(schedule_path) as f:
        schedule = json.load(f)

    print("Generating Pitch Scanner reports...\n")

    reports = {}
    for match in schedule:
        venue = match.get("venue", "")
        date_raw = match.get("dateRaw", "")
        time = match.get("time", "19:30 IST").split()[0]
        slug = match.get("slug", "")

        report = generate_pitch_report(venue, date_raw, time)
        reports[slug] = report

        dew = report["dewAnalysis"]
        toss = report["tossIntelligence"]
        phase = report["phaseAnalysis"]
        wx = report["weather"]

        print(f"{'='*60}")
        print(f"{match['team1']} vs {match['team2']} | {venue} | {match['date']}")
        print(f"  Weather: {wx['temperature']}C, {wx['humidity']}% humidity, {wx['cloudCover']}% clouds, wind {wx['windSpeed']} km/h ({wx['description']})")
        print(f"  Dew: {dew['probability']}% ({dew['impact']}) | Swing: {report['pitchBehavior']['swingPotential']}% | Spin: {report['pitchBehavior']['spinPotential']}%")
        if phase["sampleSize"] > 0:
            print(f"  Phase ({phase['sampleSize']} matches in month {phase['month']}): PP {phase['powerplay']['firstInnings']}/{phase['powerplay']['secondInnings']}, Mid {phase['middleOvers']['firstInnings']}/{phase['middleOvers']['secondInnings']}, Death {phase['deathOvers']['firstInnings']}/{phase['deathOvers']['secondInnings']}")
            print(f"  Scoring: 1st inn {phase['totalFirst']}, 2nd inn {phase['totalSecond']} (delta {phase['scoringDelta']:+.1f})")
        print(f"  Toss: {toss['recommendation']} (bowl-first {toss['bowlFirstProbability']}%, confidence {toss['confidence']}%)")
        print(f"  Verdict: {report['verdict']}")
        for r in report["reasoning"][:3]:
            print(f"    - {r}")

    # Save reports
    output_path = os.path.join(PROCESSED_DIR, "pitch_reports.json")
    with open(output_path, "w") as f:
        json.dump(reports, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Done! {len(reports)} pitch reports saved to {output_path}")


if __name__ == "__main__":
    main()
