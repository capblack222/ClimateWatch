from app.database.db import get_db

_COLUMNS = "indicator_name, value, unit, year, source"
_INSERT = (
    "INSERT INTO climate_indicators (country_code, country_name, indicator_name, year, value, unit, source) "
    "VALUES (?, ?, ?, ?, ?, ?, ?)"
)


def find_by_country_code(alpha3):
    return get_db().execute(
        f"SELECT {_COLUMNS} FROM climate_indicators WHERE country_code = ? ORDER BY year DESC", (alpha3,)
    ).fetchall()


def find_by_country_name(name):
    return get_db().execute(
        f"SELECT {_COLUMNS} FROM climate_indicators WHERE LOWER(country_name) = LOWER(?) ORDER BY year DESC",
        (name,),
    ).fetchall()


def count(source=None):
    db = get_db()
    if source is None:
        return db.execute("SELECT COUNT(*) FROM climate_indicators").fetchone()[0]
    return db.execute("SELECT COUNT(*) FROM climate_indicators WHERE source = ?", (source,)).fetchone()[0]


def replace_samples_with(rows):
    """Atomically drop sample rows and insert real OWID rows."""
    db = get_db()
    with db:
        db.execute("DELETE FROM climate_indicators WHERE source = 'sample'")
        db.executemany(_INSERT, rows)


def insert_rows(rows):
    db = get_db()
    with db:
        db.executemany(_INSERT, rows)
