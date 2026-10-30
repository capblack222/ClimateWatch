from app.services.geocoding_service import GEOCODING_URL
from app.services.weather_service import FORECAST_URL
from tests.conftest import add_indicator
from tests.payloads import FORECAST, GEOCODING

PRISTINA = "lat=42.67&lon=21.17&city=Pristina&country=Kosovo&country_code=XK"


def test_index_renders(client):
    assert client.get("/").status_code == 200


def test_weather_response_shape(client, mocked_http):
    mocked_http.get(FORECAST_URL, json=FORECAST)
    data = client.get(f"/weather?{PRISTINA}").get_json()
    assert data["city"] == "Pristina"
    assert data["current"]["temperature"] == 7.0
    assert len(data["forecast"]) == 2
    assert data["suggestion"]["text"] == "Good for a brisk run"
    assert data["climate"] == {}


def test_weather_remembers_last_city(client, mocked_http):
    mocked_http.get(FORECAST_URL, json=FORECAST)
    client.get(f"/weather?{PRISTINA}")
    with client.session_transaction() as session:
        assert session["last_city"]["city"] == "Pristina"


def test_climate_matches_exact_country_not_substring(client, db, mocked_http):
    add_indicator(db, "NER", "Niger", 0.11)
    add_indicator(db, "NGA", "Nigeria", 0.60)
    mocked_http.get(FORECAST_URL, json=FORECAST)

    niger = client.get("/weather?lat=13.5&lon=2.1&country=Niger&country_code=NE").get_json()
    nigeria = client.get("/weather?lat=6.5&lon=3.4&country=Nigeria&country_code=NG").get_json()
    assert niger["climate"]["co2_per_capita"]["value"] == 0.11
    assert nigeria["climate"]["co2_per_capita"]["value"] == 0.60


def test_climate_uses_latest_year_and_reports_source(client, db, mocked_http):
    add_indicator(db, "OWID_KOS", "Kosovo", 4.0, year=2022)
    add_indicator(db, "OWID_KOS", "Kosovo", 4.6, year=2024)
    mocked_http.get(FORECAST_URL, json=FORECAST)
    climate = client.get(f"/weather?{PRISTINA}").get_json()["climate"]
    assert climate["co2_per_capita"] == {"value": 4.6, "unit": "tonnes", "year": 2024, "source": "owid"}


def test_climate_falls_back_to_exact_name_only(client, db, mocked_http):
    add_indicator(db, "NER", "Niger", 0.11)
    mocked_http.get(FORECAST_URL, json=FORECAST)
    assert client.get("/weather?lat=1&lon=1&country=niger").get_json()["climate"]["co2_per_capita"]["value"] == 0.11
    assert client.get("/weather?lat=1&lon=1&country=Nig").get_json()["climate"] == {}


def test_weather_upstream_failure_is_502(client, mocked_http):
    mocked_http.get(FORECAST_URL, status=500)
    resp = client.get(f"/weather?{PRISTINA}")
    assert resp.status_code == 502
    assert resp.get_json()["error"]["code"] == "upstream_unavailable"


def test_weather_validation(client):
    resp = client.get("/weather?lat=10&lon=500")
    assert resp.status_code == 400
    assert resp.get_json()["error"]["details"] == [
        {"field": "lon", "message": "Input should be less than or equal to 180"}]
    assert client.get("/weather").status_code == 400


def test_search(client, mocked_http):
    mocked_http.get(GEOCODING_URL, json=GEOCODING)
    assert client.get("/search?q=pristina").get_json()[0]["country_code"] == "XK"


def test_empty_search_makes_no_upstream_call(client, mocked_http):
    assert client.get("/search?q=").get_json() == []
    assert len(mocked_http.calls) == 0


def test_search_too_long_is_400(client):
    assert client.get("/search?q=" + "a" * 101).status_code == 400


def test_search_upstream_failure_is_502(client, mocked_http):
    mocked_http.get(GEOCODING_URL, status=503)
    assert client.get("/search?q=paris").status_code == 502


def test_unknown_route_and_wrong_method_return_json(client):
    assert client.get("/nope").get_json()["error"]["code"] == "not_found"
    assert client.get("/save").get_json()["error"]["code"] == "method_not_allowed"


def test_unhandled_exception_returns_generic_500(app, client, monkeypatch):
    app.config["PROPAGATE_EXCEPTIONS"] = False  # testing mode re-raises by default

    def broken(*_args, **_kwargs):
        raise RuntimeError("database exploded")

    monkeypatch.setattr("app.routes.location_routes.locations_repo.list_locations", broken)
    resp = client.get("/saved")
    assert resp.status_code == 500
    assert resp.get_json() == {"error": {"code": "internal_error", "message": "Something went wrong"}}
    assert "exploded" not in resp.get_data(as_text=True)
