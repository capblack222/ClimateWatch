from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.database.db import get_db
from app.schemas import (
    SaveLocationRequest,
    UnsaveLocationRequest,
    error_response,
    validation_error_response,
)

location_bp = Blueprint("location", __name__)


def _json_body():
    """Return the parsed JSON object, or None if the body is missing or not a JSON object."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


@location_bp.route("/save", methods=["POST"])
def save_location():
    data = _json_body()
    if data is None:
        return error_response("invalid_json", "Request body must be a JSON object", 400)
    try:
        loc = SaveLocationRequest.model_validate(data)
    except ValidationError as err:
        return validation_error_response(err)

    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM saved_locations WHERE city_name=? AND ABS(latitude-?)< 0.01",
        (loc.city, loc.lat)
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({"status": "already_saved"})
    conn.execute(
        "INSERT INTO saved_locations (city_name, country_code, country_name, latitude, longitude) VALUES (?,?,?,?,?)",
        (loc.city, loc.country_code, loc.country, loc.lat, loc.lon)
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "saved"})


@location_bp.route("/unsave", methods=["POST"])
def unsave_location():
    data = _json_body()
    if data is None:
        return error_response("invalid_json", "Request body must be a JSON object", 400)
    try:
        req = UnsaveLocationRequest.model_validate(data)
    except ValidationError as err:
        return validation_error_response(err)

    conn = get_db()
    cur = conn.execute("DELETE FROM saved_locations WHERE id=?", (req.id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        return error_response("not_found", "Saved location not found", 404)
    return jsonify({"status": "removed"})


@location_bp.route("/saved")
def get_saved():
    conn = get_db()
    rows = conn.execute("SELECT * FROM saved_locations ORDER BY added_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])
