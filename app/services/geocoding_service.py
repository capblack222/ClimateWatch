import requests

from app.errors import UpstreamServiceError

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
SERVICE = "Open-Meteo geocoding"


def search_cities(name):
    """Up to 5 matching cities, shaped for the frontend. [] if none match; UpstreamServiceError on failure."""
    params = {"name": name, "count": 5, "language": "en", "format": "json"}
    try:
        resp = requests.get(GEOCODING_URL, params=params, timeout=8)
        resp.raise_for_status()
    except requests.RequestException as err:
        raise UpstreamServiceError(SERVICE, str(err)) from err
    try:
        data = resp.json()
    except ValueError as err:  # requests' JSONDecodeError is also a RequestException, so check it separately
        raise UpstreamServiceError(SERVICE, "response was not valid JSON") from err

    # Open-Meteo omits "results" entirely when nothing matches.
    results = data.get("results", []) if isinstance(data, dict) else []
    return [
        {
            "name": r.get("name"),
            "country": r.get("country"),
            "country_code": r.get("country_code", ""),
            "admin1": r.get("admin1", ""),
            "latitude": r.get("latitude"),
            "longitude": r.get("longitude"),
        }
        for r in results
    ]
