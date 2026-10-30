import pytest
import responses

from app import create_app
from app.config import Config
from app.database.db import get_db, init_db


@pytest.fixture
def app(tmp_path):
    class TestConfig(Config):
        TESTING = True
        SECRET_KEY = "test-secret"
        DB_PATH = str(tmp_path / "data" / "test.db")

    app = create_app(TestConfig)
    with app.app_context():
        init_db()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    """A connection inside an app context, for arranging and asserting database state."""
    with app.app_context():
        yield get_db()


@pytest.fixture
def mocked_http():
    """Every outbound HTTP call must be registered; an unregistered call fails the test."""
    with responses.RequestsMock() as rsps:
        yield rsps


def add_indicator(db, code, name, value, year=2024, source="owid", indicator="co2_per_capita"):
    db.execute(
        "INSERT INTO climate_indicators (country_code, country_name, indicator_name, year, value, unit, source) "
        "VALUES (?, ?, ?, ?, ?, 'tonnes', ?)",
        (code, name, indicator, year, value, source),
    )
    db.commit()
