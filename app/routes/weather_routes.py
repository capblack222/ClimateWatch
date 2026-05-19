from flask import Blueprint, Flask, request, jsonify, session, render_template
from app.services.geocoding_service import geocode_city
from app.services.weather_service import fetch_weather
from app.services.suggestion_service import activity_suggestion
from app.utils.weather_codes import wmo_description
from app.database.db import get_db
import os

weather_bp = Blueprint("weather", __name__)
# weather_bp.secret_key = os.getenv("FLASK_SECRET_KEY", "weather_planner_secret_key_2026")

@weather_bp.route("/")
def index():
    conn = get_db()
    saved = conn.execute("SELECT * FROM saved_locations ORDER BY added_at DESC").fetchall()
    conn.close()
    last_city = session.get("last_city")
    return render_template("index.html", saved_locations=saved, last_city=last_city)

@weather_bp.route("/search")
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

@weather_bp.route("/weather")
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