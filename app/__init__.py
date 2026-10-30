import logging
import secrets
import time

from flask import Flask, g, request

from app.config import Config
from app.database.db import close_db
from app.errors import register_error_handlers
from app.logging_config import configure_logging

request_logger = logging.getLogger("app.request")


def create_app(config_class=Config):
    # Configure logging before Flask creates app.logger, so Flask doesn't attach its own plain-text handler.
    configure_logging(config_class.LOG_LEVEL)

    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config["SECRET_KEY"]:
        # No hardcoded fallback: generate a throwaway key for this process only.
        # Sessions reset on restart; set FLASK_SECRET_KEY to keep them.
        app.config["SECRET_KEY"] = secrets.token_hex(32)
        app.logger.warning("FLASK_SECRET_KEY is not set; using a temporary key for this run")

    from app.routes.location_routes import location_bp
    from app.routes.weather_routes import weather_bp

    app.register_blueprint(weather_bp)
    app.register_blueprint(location_bp)
    register_error_handlers(app)
    app.teardown_appcontext(close_db)

    @app.before_request
    def _start_timer():
        g.request_start = time.perf_counter()

    @app.after_request
    def _log_request(response):
        start = g.get("request_start")
        duration_ms = round((time.perf_counter() - start) * 1000, 1) if start else None
        # Path only, no query string, so search terms and coordinates stay out of the logs.
        request_logger.info(
            "request",
            extra={"method": request.method, "path": request.path, "status": response.status_code,
                   "duration_ms": duration_ms},
        )
        return response

    return app
