from app.database.db import get_db


def list_locations():
    rows = get_db().execute("SELECT * FROM saved_locations ORDER BY added_at DESC, id DESC").fetchall()
    return [dict(row) for row in rows]


def add_location(city, country_code, country, lat, lon):
    """Insert a location. Returns False if it was already saved (enforced by the unique index)."""
    db = get_db()
    cur = db.execute(
        """INSERT OR IGNORE INTO saved_locations (city_name, country_code, country_name, latitude, longitude)
           VALUES (?, ?, ?, ?, ?)""",
        (city, country_code, country, lat, lon),
    )
    db.commit()
    return cur.rowcount == 1


def delete_location(location_id):
    """Delete a location. Returns False if no location had that id."""
    db = get_db()
    cur = db.execute("DELETE FROM saved_locations WHERE id = ?", (location_id,))
    db.commit()
    return cur.rowcount == 1
