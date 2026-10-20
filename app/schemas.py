"""Request schemas: every route validates its input here before touching the database or external APIs."""
from flask import jsonify
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class _Schema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")


class SearchQuery(_Schema):
    q: str = Field(default="", max_length=100)


class WeatherQuery(_Schema):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    city: str = Field(default="", max_length=100)
    country: str = Field(default="", max_length=100)
    country_code: str = Field(default="", max_length=3)


class SaveLocationRequest(_Schema):
    city: str = Field(min_length=1, max_length=100)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    country: str = Field(default="", max_length=100)
    country_code: str = Field(default="", max_length=3)


class UnsaveLocationRequest(_Schema):
    id: int = Field(gt=0)


def error_response(code, message, status, details=None):
    """Single JSON error shape used by every route."""
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


def validation_error_response(err: ValidationError):
    # Only field + message are returned; Pydantic's raw "input" is left out so user input is never echoed back.
    details = [
        {"field": ".".join(str(p) for p in e["loc"]) or "body", "message": e["msg"]}
        for e in err.errors()
    ]
    return error_response("validation_error", "Request validation failed", 400, details)
