from flask import Blueprint, jsonify, render_template, request, session
from pydantic import ValidationError

from app.repositories import locations_repo
from app.schemas import SearchQuery, WeatherQuery, validation_error_response
from app.services.climate_service import get_country_indicators
from app.services.geocoding_service import search_cities
from app.services.suggestion_service import activity_suggestion
from app.services.weather_service import fetch_weather, summarize_current, summarize_forecast

weather_bp = Blueprint("weather", __name__)


@weather_bp.route("/")
def index():
    return render_template(
        "index.html", saved_locations=locations_repo.list_locations(), last_city=session.get("last_city")
    )


@weather_bp.route("/search")
def search():
    try:
        params = SearchQuery.model_validate(request.args.to_dict())
    except ValidationError as err:
        return validation_error_response(err)
    return jsonify(search_cities(params.q) if params.q else [])


@weather_bp.route("/weather")
def weather():
    try:
        q = WeatherQuery.model_validate(request.args.to_dict())
    except ValidationError as err:
        return validation_error_response(err)

    session["last_city"] = {"city": q.city, "country": q.country, "lat": q.lat, "lon": q.lon,
                            "country_code": q.country_code}

    raw = fetch_weather(q.lat, q.lon)  # UpstreamServiceError -> 502 via app.errors
    current = summarize_current(raw)
    text, icon, note = activity_suggestion(current["temperature"], current["precipitation"], current["wind_speed"])

    return jsonify({
        "city": q.city,
        "country": q.country,
        "current": current,
        "forecast": summarize_forecast(raw),
        "suggestion": {"text": text, "icon": icon, "note": note},
        "climate": get_country_indicators(q.country_code, q.country),
    })
