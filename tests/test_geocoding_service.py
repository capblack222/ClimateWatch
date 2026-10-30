import pytest

from app.errors import UpstreamServiceError
from app.services.geocoding_service import GEOCODING_URL, search_cities
from tests.payloads import GEOCODING


def test_search_cities_shapes_results(mocked_http):
    mocked_http.get(GEOCODING_URL, json=GEOCODING)
    assert search_cities("pristina") == [{
        "name": "Pristina", "country": "Kosovo", "country_code": "XK", "admin1": "Pristina",
        "latitude": 42.67272, "longitude": 21.16688,
    }]


def test_search_cities_no_matches(mocked_http):
    mocked_http.get(GEOCODING_URL, json={"generationtime_ms": 0.1})  # Open-Meteo omits "results"
    assert search_cities("zzzz") == []


def test_search_cities_upstream_failure(mocked_http):
    mocked_http.get(GEOCODING_URL, status=503)
    with pytest.raises(UpstreamServiceError):
        search_cities("paris")


def test_search_cities_invalid_json(mocked_http):
    mocked_http.get(GEOCODING_URL, body="<html>busy</html>")
    with pytest.raises(UpstreamServiceError, match="not valid JSON"):
        search_cities("paris")
