from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.errors import error_response
from app.repositories import locations_repo
from app.schemas import SaveLocationRequest, UnsaveLocationRequest, validation_error_response

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

    saved = locations_repo.add_location(loc.city, loc.country_code, loc.country, loc.lat, loc.lon)
    return jsonify({"status": "saved" if saved else "already_saved"})


@location_bp.route("/unsave", methods=["POST"])
def unsave_location():
    data = _json_body()
    if data is None:
        return error_response("invalid_json", "Request body must be a JSON object", 400)
    try:
        req = UnsaveLocationRequest.model_validate(data)
    except ValidationError as err:
        return validation_error_response(err)

    if not locations_repo.delete_location(req.id):
        return error_response("not_found", "Saved location not found", 404)
    return jsonify({"status": "removed"})


@location_bp.route("/saved")
def get_saved():
    return jsonify(locations_repo.list_locations())
