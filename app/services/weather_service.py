import requests

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