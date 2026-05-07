from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import requests
import json
import os
import csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = "weather_planner_secret_key_2024"

DB_PATH = "weather_planner.db"
DATA_DIR = "data"

# ─── Database Setup ───────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS saved_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city_name TEXT NOT NULL,
            country_code TEXT,
            country_name TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS climate_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT,
            country_name TEXT NOT NULL,
            indicator_name TEXT NOT NULL,
            year INTEGER,
            value REAL,
            unit TEXT
        );

        CREATE TABLE IF NOT EXISTS weather_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT UNIQUE NOT NULL,
            data TEXT NOT NULL,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

# ─── OWID CSV Loader ──────────────────────────────────────────────────────────

def load_owid_csv():
    """Load sample OWID data into SQLite. In production, drop in real OWID CSVs."""
    conn = get_db()
    existing = conn.execute("SELECT COUNT(*) FROM climate_indicators").fetchone()[0]
    if existing > 0:
        conn.close()
        return

    # Sample data representing what OWID CSVs contain
    # In production, parse actual OWID CSV files placed in /data/
    sample_data = [
        ("USA", "United States", "co2_per_capita", 2022, 14.9, "tonnes"),
        ("USA", "United States", "obesity_prevalence", 2022, 36.2, "%"),
        ("GBR", "United Kingdom", "co2_per_capita", 2022, 5.3, "tonnes"),
        ("GBR", "United Kingdom", "obesity_prevalence", 2022, 27.8, "%"),
        ("DEU", "Germany", "co2_per_capita", 2022, 8.1, "tonnes"),
        ("DEU", "Germany", "obesity_prevalence", 2022, 22.3, "%"),
        ("FRA", "France", "co2_per_capita", 2022, 4.7, "tonnes"),
        ("FRA", "France", "obesity_prevalence", 2022, 21.6, "%"),
        ("IND", "India", "co2_per_capita", 2022, 1.9, "tonnes"),
        ("IND", "India", "obesity_prevalence", 2022, 3.9, "%"),
        ("CHN", "China", "co2_per_capita", 2022, 8.0, "tonnes"),
        ("CHN", "China", "obesity_prevalence", 2022, 6.2, "%"),
        ("JPN", "Japan", "co2_per_capita", 2022, 8.5, "tonnes"),
        ("JPN", "Japan", "obesity_prevalence", 2022, 4.3, "%"),
        ("BRA", "Brazil", "co2_per_capita", 2022, 2.3, "tonnes"),
        ("BRA", "Brazil", "obesity_prevalence", 2022, 22.1, "%"),
        ("CAN", "Canada", "co2_per_capita", 2022, 14.2, "tonnes"),
        ("CAN", "Canada", "obesity_prevalence", 2022, 29.4, "%"),
        ("AUS", "Australia", "co2_per_capita", 2022, 14.8, "tonnes"),
        ("AUS", "Australia", "obesity_prevalence", 2022, 29.0, "%"),
    ]

    conn.executemany(
        "INSERT INTO climate_indicators (country_code, country_name, indicator_name, year, value, unit) VALUES (?,?,?,?,?,?)",
        sample_data
    )

    # Also try to load any real OWID CSVs dropped in /data/
    for fname in os.listdir(DATA_DIR):
        if fname.endswith(".csv"):
            try:
                _parse_owid_csv(conn, os.path.join(DATA_DIR, fname))
            except Exception as e:
                print(f"Could not parse {fname}: {e}")

    conn.commit()
    conn.close()

def _parse_owid_csv(conn, filepath):
    """Generic OWID CSV parser (Entity, Code, Year, Value columns)."""
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if not rows:
            return
        indicator_col = [c for c in rows[0].keys() if c not in ("Entity", "Code", "Year")][0]
        indicator_name = indicator_col.lower().replace(" ", "_")
        for row in rows[-500:]:  # last 500 rows (recent years)
            try:
                val = float(row.get(indicator_col, "") or 0)
                conn.execute(
                    "INSERT OR IGNORE INTO climate_indicators (country_name, country_code, indicator_name, year, value) VALUES (?,?,?,?,?)",
                    (row["Entity"], row.get("Code", ""), indicator_name, int(row.get("Year", 0)), val)
                )
            except (ValueError, KeyError):
                continue

# ─── Geocoding ────────────────────────────────────────────────────────────────

def geocode_city(city_name):
    """Use Open-Meteo's geocoding API to resolve city → lat/lon."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city_name, "count": 5, "language": "en", "format": "json"}
    try:
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        return results
    except Exception as e:
        print(f"Geocoding error: {e}")
        return []

# ─── Weather Fetching ─────────────────────────────────────────────────────────

def fetch_weather(lat, lon):
    """Fetch current conditions + 7-day forecast from Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m", "apparent_temperature", "relative_humidity_2m",
            "precipitation", "wind_speed_10m", "weather_code", "is_day"
        ],
        "daily": [
            "weather_code", "temperature_2m_max", "temperature_2m_min",
            "precipitation_sum", "wind_speed_10m_max"
        ],
        "timezone": "auto",
        "forecast_days": 7
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Weather fetch error: {e}")
        return None

def wmo_description(code):
    """Map WMO weather code to human-readable description."""
    mapping = {
        0: ("Clear Sky", "☀️"), 1: ("Mostly Clear", "🌤️"), 2: ("Partly Cloudy", "⛅"),
        3: ("Overcast", "☁️"), 45: ("Foggy", "🌫️"), 48: ("Icy Fog", "🌫️"),
        51: ("Light Drizzle", "🌦️"), 53: ("Drizzle", "🌦️"), 55: ("Heavy Drizzle", "🌧️"),
        61: ("Light Rain", "🌧️"), 63: ("Rain", "🌧️"), 65: ("Heavy Rain", "🌧️"),
        71: ("Light Snow", "🌨️"), 73: ("Snow", "❄️"), 75: ("Heavy Snow", "❄️"),
        80: ("Rain Showers", "🌦️"), 81: ("Heavy Showers", "⛈️"), 82: ("Violent Showers", "⛈️"),
        95: ("Thunderstorm", "⛈️"), 96: ("Hail Storm", "⛈️"), 99: ("Heavy Hail", "⛈️"),
    }
    return mapping.get(code, ("Unknown", "🌡️"))

def activity_suggestion(temp, precip, wind):
    """Simple rule-based activity suggestion."""
    if precip and precip > 5:
        return ("Stay indoors today", "🏠", "heavy precipitation expected")
    if wind and wind > 40:
        return ("Indoor activities recommended", "💨", "strong winds today")
    if temp is None:
        return ("Check conditions before heading out", "🤔", "")
    if temp < 0:
        return ("Bundle up for winter walks", "🧥", "below freezing")
    if 0 <= temp < 10:
        return ("Good for a brisk run", "🏃", "cool and crisp")
    if 10 <= temp < 20:
        return ("Great day for walking or cycling", "🚴", "comfortable conditions")
    if 20 <= temp < 30:
        return ("Perfect for outdoor activities", "🌳", "ideal weather")
    return ("Stay hydrated, limit outdoor exertion", "💧", "hot conditions")

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    conn = get_db()
    saved = conn.execute("SELECT * FROM saved_locations ORDER BY added_at DESC").fetchall()
    conn.close()
    last_city = session.get("last_city")
    return render_template("index.html", saved_locations=saved, last_city=last_city)

@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    results = geocode_city(query)
    out = []
    for r in results:
        out.append({
            "name": r.get("name"),
            "country": r.get("country"),
            "country_code": r.get("country_code", ""),
            "admin1": r.get("admin1", ""),
            "latitude": r.get("latitude"),
            "longitude": r.get("longitude"),
        })
    return jsonify(out)

@app.route("/weather")
def weather():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    city = request.args.get("city", "")
    country = request.args.get("country", "")
    country_code = request.args.get("country_code", "")

    if lat is None or lon is None:
        return jsonify({"error": "lat/lon required"}), 400

    # Save last selected city in session
    session["last_city"] = {"city": city, "country": country, "lat": lat, "lon": lon, "country_code": country_code}

    # Fetch weather
    raw = fetch_weather(lat, lon)
    if not raw:
        return jsonify({"error": "Could not fetch weather data"}), 500

    current = raw.get("current", {})
    daily = raw.get("daily", {})

    temp = current.get("temperature_2m")
    precip = current.get("precipitation")
    wind = current.get("wind_speed_10m")
    code = current.get("weather_code", 0)
    desc, emoji = wmo_description(code)
    suggestion, sug_icon, sug_note = activity_suggestion(temp, precip, wind)

    # Build forecast list
    forecast = []
    for i in range(len(daily.get("time", []))):
        day_code = daily["weather_code"][i] if i < len(daily.get("weather_code", [])) else 0
        day_desc, day_emoji = wmo_description(day_code)
        forecast.append({
            "date": daily["time"][i],
            "description": day_desc,
            "emoji": day_emoji,
            "temp_max": daily["temperature_2m_max"][i],
            "temp_min": daily["temperature_2m_min"][i],
            "precip": daily["precipitation_sum"][i],
            "wind": daily["wind_speed_10m_max"][i],
        })

    # Climate indicators for this country
    conn = get_db()
    indicators = conn.execute(
        """SELECT indicator_name, value, unit, year FROM climate_indicators
           WHERE country_code = ? OR country_name LIKE ?
           ORDER BY year DESC""",
        (country_code.upper(), f"%{country}%")
    ).fetchall()
    conn.close()

    climate = {}
    for row in indicators:
        name = row["indicator_name"]
        if name not in climate:
            climate[name] = {"value": row["value"], "unit": row["unit"] or "", "year": row["year"]}

    return jsonify({
        "city": city,
        "country": country,
        "current": {
            "temperature": temp,
            "feels_like": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "precipitation": precip,
            "wind_speed": wind,
            "description": desc,
            "emoji": emoji,
            "is_day": current.get("is_day", 1),
        },
        "forecast": forecast,
        "suggestion": {"text": suggestion, "icon": sug_icon, "note": sug_note},
        "climate": climate,
    })

@app.route("/save", methods=["POST"])
def save_location():
    data = request.json
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM saved_locations WHERE city_name=? AND ABS(latitude-?)< 0.01",
        (data["city"], data["lat"])
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({"status": "already_saved"})
    conn.execute(
        "INSERT INTO saved_locations (city_name, country_code, country_name, latitude, longitude) VALUES (?,?,?,?,?)",
        (data["city"], data.get("country_code", ""), data.get("country", ""), data["lat"], data["lon"])
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "saved"})

@app.route("/unsave", methods=["POST"])
def unsave_location():
    loc_id = request.json.get("id")
    conn = get_db()
    conn.execute("DELETE FROM saved_locations WHERE id=?", (loc_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "removed"})

@app.route("/saved")
def get_saved():
    conn = get_db()
    rows = conn.execute("SELECT * FROM saved_locations ORDER BY added_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    init_db()
    load_owid_csv()
    app.run(debug=True)
