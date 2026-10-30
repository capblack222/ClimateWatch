import requests

from app.errors import UpstreamServiceError
from app.utils.weather_codes import wmo_description

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
SERVICE = "Open-Meteo forecast"
_DAILY_FIELDS = ("weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_sum", "wind_speed_10m_max")


def fetch_weather(lat, lon):
    """Fetch current conditions + 7-day forecast from Open-Meteo. Raises UpstreamServiceError on failure."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m", "apparent_temperature", "relative_humidity_2m",
            "precipitation", "wind_speed_10m", "weather_code", "is_day",
        ],
        "daily": list(_DAILY_FIELDS),
        "timezone": "auto",
        "forecast_days": 7,
    }
    try:
        resp = requests.get(FORECAST_URL, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as err:
        raise UpstreamServiceError(SERVICE, str(err)) from err
    try:
        data = resp.json()
    except ValueError as err:  # requests' JSONDecodeError is also a RequestException, so check it separately
        raise UpstreamServiceError(SERVICE, "response was not valid JSON") from err

    if not isinstance(data, dict) or "current" not in data or "daily" not in data:
        raise UpstreamServiceError(SERVICE, "response missing 'current' or 'daily'")
    return data


def summarize_current(raw):
    current = raw["current"]
    description, emoji = wmo_description(current.get("weather_code", 0))
    return {
        "temperature": current.get("temperature_2m"),
        "feels_like": current.get("apparent_temperature"),
        "humidity": current.get("relative_humidity_2m"),
        "precipitation": current.get("precipitation"),
        "wind_speed": current.get("wind_speed_10m"),
        "description": description,
        "emoji": emoji,
        "is_day": current.get("is_day", 1),
    }


def summarize_forecast(raw):
    """One dict per day. Raises UpstreamServiceError if the daily arrays are missing or uneven."""
    daily = raw["daily"]
    days = daily.get("time", [])
    if any(len(daily.get(field, [])) != len(days) for field in _DAILY_FIELDS):
        raise UpstreamServiceError(SERVICE, "daily forecast arrays are missing or have different lengths")

    forecast = []
    for i, date in enumerate(days):
        description, emoji = wmo_description(daily["weather_code"][i])
        forecast.append({
            "date": date,
            "description": description,
            "emoji": emoji,
            "temp_max": daily["temperature_2m_max"][i],
            "temp_min": daily["temperature_2m_min"][i],
            "precip": daily["precipitation_sum"][i],
            "wind": daily["wind_speed_10m_max"][i],
        })
    return forecast
