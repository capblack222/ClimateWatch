import os


class Config:
    """Settings read from environment variables (or a local .env file)."""

    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
    DB_PATH = os.environ.get("DB_PATH", "data/weather_planner.db")
