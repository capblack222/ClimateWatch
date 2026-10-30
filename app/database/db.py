"""SQLite access: one connection per app context, closed automatically when the request ends."""
import logging
import os
import sqlite3

from flask import current_app, g

from app.database.sample_data import SAMPLE_DATA, SAMPLE_YEAR

logger = logging.getLogger(__name__)

_SCHEMA = """
    CREATE TABLE IF NOT EXISTS saved_locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_name TEXT NOT NULL,
        country_code TEXT,
        country_name TEXT,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS climate_indicators (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_code TEXT,
        country_name TEXT NOT NULL,
        indicator_name TEXT NOT NULL,
        year INTEGER,
        value REAL,
        unit TEXT,
        source TEXT NOT NULL DEFAULT 'owid'
    );
"""

# The same city at the same place (coordinates rounded to ~1 km) can only be saved once.
_UNIQUE_LOCATION_INDEX = """
    CREATE UNIQUE INDEX IF NOT EXISTS ux_saved_locations_place
    ON saved_locations (city_name COLLATE NOCASE, ROUND(latitude, 2), ROUND(longitude, 2))
"""


def get_db():
    """Return this app context's connection, opening it on first use."""
    if "db" not in g:
        path = current_app.config["DB_PATH"]
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        g.db = sqlite3.connect(path)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables and apply in-place migrations. Must run inside an app context."""
    db = get_db()
    db.executescript(_SCHEMA)

    # Migration: databases created before the `source` column existed.
    columns = {row["name"] for row in db.execute("PRAGMA table_info(climate_indicators)")}
    if "source" not in columns:
        db.execute("ALTER TABLE climate_indicators ADD COLUMN source TEXT NOT NULL DEFAULT 'owid'")
        # Older versions stored fallback rows unlabelled; tag them so the next start retries the real download.
        db.executemany(
            "UPDATE climate_indicators SET source = 'sample' WHERE country_code = ? AND year = ? AND value = ?",
            [(code, SAMPLE_YEAR, value) for code, _name, value in SAMPLE_DATA],
        )

    # Migration: remove duplicates saved before the unique index existed (keeps the oldest), then add the index.
    removed = db.execute(
        """DELETE FROM saved_locations WHERE id NOT IN (
               SELECT MIN(id) FROM saved_locations
               GROUP BY city_name COLLATE NOCASE, ROUND(latitude, 2), ROUND(longitude, 2))"""
    ).rowcount
    if removed:
        logger.info("Removed duplicate saved locations", extra={"rows": removed})
    db.execute(_UNIQUE_LOCATION_INDEX)
    db.commit()
