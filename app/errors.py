"""Error types and the single JSON error shape shared by every route."""
import logging

from flask import jsonify
from werkzeug.exceptions import InternalServerError, MethodNotAllowed, NotFound

logger = logging.getLogger(__name__)


class UpstreamServiceError(Exception):
    """An external API (Open-Meteo, Our World in Data) failed or returned unusable data."""

    def __init__(self, service, reason):
        super().__init__(f"{service}: {reason}")
        self.service = service
        self.reason = reason


def error_response(code, message, status, details=None):
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


def register_error_handlers(app):
    @app.errorhandler(UpstreamServiceError)
    def _upstream(err):
        logger.warning("Upstream service failed", extra={"service": err.service, "reason": err.reason})
        return error_response("upstream_unavailable", f"{err.service} is temporarily unavailable", 502)

    @app.errorhandler(NotFound)
    def _not_found(_err):
        return error_response("not_found", "Resource not found", 404)

    @app.errorhandler(MethodNotAllowed)
    def _method_not_allowed(_err):
        return error_response("method_not_allowed", "Method not allowed", 405)

    @app.errorhandler(InternalServerError)
    def _internal(err):
        # Log the real cause server-side; never leak a stack trace to the client.
        logger.error("Unhandled exception", exc_info=getattr(err, "original_exception", None) or err)
        return error_response("internal_error", "Something went wrong", 500)
