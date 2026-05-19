import pandas as pd
import ssl
import certifi
from app.database.db import get_db

def load_owid_csv():
    conn = get_db()
    existing = conn.execute("SELECT COUNT(*) FROM climate_indicators").fetchone()[0]
    if existing > 0:
        conn.close()
        return

    try:

        ssl._create_default_https_context = ssl.create_default_context(
            cafile=certifi.where()
        )

        df = pd.read_csv(
            "https://ourworldindata.org/grapher/co-emissions-per-capita.csv?v=1&csvType=filtered&useColumnShortNames=true",
            storage_options={"User-Agent": "Our World In Data data fetch/1.0"}
        )

        # OWID short-name CSV columns: entity, code, year, co2_per_capita
        # Keep only the most recent year per country to avoid bloat
        df = df.dropna(subset=["code", "co2_per_capita"])
        df = df.sort_values("year").groupby("code").last().reset_index()

        rows = [
            (row["code"], row["entity"], "co2_per_capita", int(row["year"]), float(row["co2_per_capita"]), "tonnes")
            for _, row in df.iterrows()
        ]
        conn.executemany(
            "INSERT INTO climate_indicators (country_code, country_name, indicator_name, year, value, unit) VALUES (?,?,?,?,?,?)",
            rows
        )
        conn.commit()
        print(f"Loaded {len(rows)} CO₂ rows from OWID.")

    except Exception as e:
        print(f"OWID fetch failed: {e}. Falling back to sample data.")
        _load_sample_data(conn)
        conn.commit()

    conn.close()


def _load_sample_data(conn):
    """Fallback if OWID is unreachable (offline dev, rate limit, etc.)."""
    sample_data = [
        ("USA", "United States",  "co2_per_capita", 2025, 14.9, "tonnes"),
        ("GBR", "United Kingdom", "co2_per_capita", 2025, 5.3, "tonnes"),
        ("DEU", "Germany",        "co2_per_capita", 2025, 8.1, "tonnes"),
        ("FRA", "France",         "co2_per_capita", 2025, 4.7, "tonnes"),
        ("IND", "India",          "co2_per_capita", 2025, 1.9, "tonnes"),
        ("CHN", "China",          "co2_per_capita", 2025, 8.0, "tonnes"),
        ("JPN", "Japan",          "co2_per_capita", 2025, 8.5, "tonnes"),
        ("BRA", "Brazil",         "co2_per_capita", 2025, 2.3, "tonnes"),
        ("CAN", "Canada",         "co2_per_capita", 2025, 14.2, "tonnes"),
        ("AUS", "Australia",      "co2_per_capita", 2025, 14.8, "tonnes"),
    ]
    conn.executemany(
        "INSERT INTO climate_indicators (country_code, country_name, indicator_name, year, value, unit) VALUES (?,?,?,?,?,?)",
        sample_data
    )