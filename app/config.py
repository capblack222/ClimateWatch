import os


class Config:
    """Settings read from environment variables (or a local .env file)."""

    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
    DB_PATH = os.environ.get("DB_PATH", "data/weather_planner.db")
    # Reuse pooled HTTPS connections to Open-Meteo. Set to 0 only to reproduce the old behaviour in A/B tests.
    HTTP_REUSE_CONNECTIONS = os.environ.get("HTTP_REUSE_CONNECTIONS", "1") == "1"


def port_from_env():
    """Port for `python run.py`. Defaults to 5050 because macOS AirPlay Receiver answers on 5000 with 403s."""
    value = os.environ.get("PORT", "5050")
    if not value.isdigit() or not 1 <= int(value) <= 65535:
        raise ValueError(f"PORT must be a whole number from 1 to 65535, got {value!r}")
    return int(value)
