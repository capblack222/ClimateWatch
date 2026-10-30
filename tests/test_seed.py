from app.database.db import init_db
from app.database.seed import OWID_CO2_URL, load_owid_csv
from tests.conftest import add_indicator
from tests.payloads import OWID_CSV


def _rows(db):
    return {r["country_code"]: (r["value"], r["year"], r["source"])
            for r in db.execute("SELECT country_code, value, year, source FROM climate_indicators")}


def test_loads_latest_year_per_country_and_skips_regions(db, mocked_http):
    mocked_http.get(OWID_CO2_URL, body=OWID_CSV)
    load_owid_csv()
    assert _rows(db) == {
        "NER": (0.11, 2024, "owid"),
        "NGA": (0.60, 2024, "owid"),
        "OWID_KOS": (4.6, 2024, "owid"),
    }


def test_falls_back_to_labelled_samples_when_download_fails(db, mocked_http):
    mocked_http.get(OWID_CO2_URL, status=503)
    load_owid_csv()
    rows = _rows(db)
    assert len(rows) == 10
    assert {source for _v, _y, source in rows.values()} == {"sample"}


def test_replaces_samples_once_download_succeeds(db, mocked_http):
    add_indicator(db, "USA", "United States", 14.9, year=2025, source="sample")
    mocked_http.get(OWID_CO2_URL, body=OWID_CSV)
    load_owid_csv()
    assert "USA" not in _rows(db)
    assert _rows(db)["NER"][2] == "owid"


def test_does_not_download_when_real_data_exists(db, mocked_http):
    add_indicator(db, "NER", "Niger", 0.11)
    load_owid_csv()  # mocked_http has nothing registered, so any HTTP call would fail the test
    assert len(mocked_http.calls) == 0


def test_migration_tags_old_unlabelled_sample_rows(db):
    # A database from before the `source` column existed, holding the old fallback rows.
    db.executescript("DROP TABLE climate_indicators; CREATE TABLE climate_indicators ("
                     "id INTEGER PRIMARY KEY, country_code TEXT, country_name TEXT NOT NULL, "
                     "indicator_name TEXT NOT NULL, year INTEGER, value REAL, unit TEXT);")
    db.execute("INSERT INTO climate_indicators (country_code, country_name, indicator_name, year, value, unit) "
               "VALUES ('USA', 'United States', 'co2_per_capita', 2025, 14.9, 'tonnes')")
    db.execute("INSERT INTO climate_indicators (country_code, country_name, indicator_name, year, value, unit) "
               "VALUES ('NER', 'Niger', 'co2_per_capita', 2024, 0.11, 'tonnes')")
    init_db()
    assert _rows(db)["USA"][2] == "sample"
    assert _rows(db)["NER"][2] == "owid"


def test_accepts_older_column_name(db, mocked_http):
    mocked_http.get(OWID_CO2_URL, body="entity,code,year,co2_per_capita\nNiger,NER,2024,0.11\n")
    load_owid_csv()
    assert _rows(db) == {"NER": (0.11, 2024, "owid")}


def test_unexpected_columns_fall_back_to_samples(db, mocked_http):
    mocked_http.get(OWID_CO2_URL, body="entity,code,year,a,b\nNiger,NER,2024,1,2\n")
    load_owid_csv()
    assert {source for _v, _y, source in _rows(db).values()} == {"sample"}
