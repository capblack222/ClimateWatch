import copy

import pytest
import requests

from app.errors import UpstreamServiceError
from app.services.weather_service import FORECAST_URL, fetch_weather, summarize_current, summarize_forecast
from tests.payloads import FORECAST


def test_fetch_weather_returns_payload(mocked_http):
    mocked_http.get(FORECAST_URL, json=FORECAST)
    assert fetch_weather(42.67, 21.17)["current"]["temperature_2m"] == 7.0


@pytest.mark.parametrize(
    "kwargs, reason",
    [
        ({"status": 500}, "500"),
        ({"body": requests.ConnectTimeout("timed out")}, "timed out"),
        ({"body": "not json"}, "not valid JSON"),
        ({"json": {"current": {}}}, "missing"),
    ],
)
def test_fetch_weather_raises_upstream_error(mocked_http, kwargs, reason):
    mocked_http.get(FORECAST_URL, **kwargs)
    with pytest.raises(UpstreamServiceError, match=reason):
        fetch_weather(1, 2)


def test_summarize_current_maps_fields():
    current = summarize_current(FORECAST)
    assert current["temperature"] == 7.0
    assert current["feels_like"] == 5.0
    assert current["description"] == "Clear Sky"


def test_summarize_forecast_one_entry_per_day():
    forecast = summarize_forecast(FORECAST)
    assert [d["date"] for d in forecast] == ["2026-10-19", "2026-10-20"]
    assert forecast[1]["description"] == "Light Rain"
    assert forecast[1]["precip"] == 1.4


def test_summarize_forecast_rejects_uneven_arrays():
    raw = copy.deepcopy(FORECAST)
    raw["daily"]["temperature_2m_max"] = [20.0]  # one value for two days
    with pytest.raises(UpstreamServiceError, match="different lengths"):
        summarize_forecast(raw)
