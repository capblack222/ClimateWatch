import requests

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
