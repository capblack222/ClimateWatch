from flask import Blueprint, request, jsonify
from app.database.db import get_db, init_db
from app.database.seed import load_owid_csv

location_bp = Blueprint("location", __name__)

@location_bp.route("/save", methods=["POST"])
def save_location():
    data = request.json
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM saved_locations WHERE city_name=? AND ABS(latitude-?)< 0.01",
        (data["city"], data["lat"])
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({"status": "already_saved"})
    conn.execute(
        "INSERT INTO saved_locations (city_name, country_code, country_name, latitude, longitude) VALUES (?,?,?,?,?)",
        (data["city"], data.get("country_code", ""), data.get("country", ""), data["lat"], data["lon"])
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "saved"})

@location_bp.route("/unsave", methods=["POST"])
def unsave_location():
    loc_id = request.json.get("id")
    conn = get_db()
    conn.execute("DELETE FROM saved_locations WHERE id=?", (loc_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "removed"})

@location_bp.route("/saved")
def get_saved():
    conn = get_db()
    rows = conn.execute("SELECT * FROM saved_locations ORDER BY added_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    init_db()
    load_owid_csv()
    location_bp.run(debug=True)
