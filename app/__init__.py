import secrets

from flask import Flask

from app.config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config["SECRET_KEY"]:
        # No hardcoded fallback: generate a throwaway key for this process only.
        # Sessions reset on restart; set FLASK_SECRET_KEY to keep them.
        app.config["SECRET_KEY"] = secrets.token_hex(32)
        app.logger.warning("FLASK_SECRET_KEY is not set; using a temporary key for this run.")

    from app.routes.weather_routes import weather_bp
    from app.routes.location_routes import location_bp

    app.register_blueprint(weather_bp)
    app.register_blueprint(location_bp)

    return app
