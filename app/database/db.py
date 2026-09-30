import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "data/weather_planner.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = get_db()
    conn.executescript("""
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
            unit TEXT
        );
    """)
    conn.commit()
    conn.close()