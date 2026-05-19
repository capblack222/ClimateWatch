from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "weather_planner_secret_key_2026")

    from app.routes.weather_routes import weather_bp
    from app.routes.location_routes import location_bp

    app.register_blueprint(weather_bp)

    app.register_blueprint(location_bp)

    return app