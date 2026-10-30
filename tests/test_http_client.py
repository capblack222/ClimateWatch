from flask import g

from app import http_client
from app.services.weather_service import FORECAST_URL, fetch_weather
from tests.payloads import FORECAST


def test_upstream_time_is_recorded_per_request(app, mocked_http):
    mocked_http.get(FORECAST_URL, json=FORECAST)
    with app.test_request_context():
        fetch_weather(1, 2)
        fetch_weather(1, 2)
        assert g.upstream_calls == 2
        assert g.upstream_ms > 0


def test_reuse_uses_one_shared_session(app, mocked_http, monkeypatch):
    mocked_http.get(FORECAST_URL, json=FORECAST)
    monkeypatch.setattr(http_client, "_session", None)
    with app.test_request_context():
        fetch_weather(1, 2)
        first = http_client._session
        fetch_weather(1, 2)
        assert first is not None and http_client._session is first


def test_reuse_off_bypasses_the_session(app, mocked_http, monkeypatch):
    mocked_http.get(FORECAST_URL, json=FORECAST)
    monkeypatch.setattr(http_client, "_session", None)
    app.config["HTTP_REUSE_CONNECTIONS"] = False
    with app.test_request_context():
        fetch_weather(1, 2)
    assert http_client._session is None


def test_request_log_includes_upstream_fields(client, mocked_http, caplog):
    mocked_http.get(FORECAST_URL, json=FORECAST)
    caplog.set_level("INFO", logger="app.request")
    client.get("/weather?lat=1&lon=2")
    record = next(r for r in caplog.records if r.name == "app.request")
    assert record.upstream_calls == 1
    assert record.upstream_ms > 0
    assert record.http_reuse is True
