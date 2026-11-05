"""Local latency baseline for the Flask app (Phase 0). Results feed the before/after comparison after AWS deploy.

Usage (app running on :5050 in another terminal):
    pip install locust
    locust -f perf/locustfile.py --host http://127.0.0.1:5050 --headless -u 3 -r 1 -t 60s --csv perf_baseline

Kept deliberately small (3 users, ~1 request/s each) to stay far inside Open-Meteo's free-tier limits.
"""
import random

from locust import HttpUser, between, task

from perf.cities import CITIES


class DashboardUser(HttpUser):
    wait_time = between(1, 2)

    @task(3)
    def weather(self):
        city, country, code, lat, lon = random.choice(CITIES)
        self.client.get(
            "/weather",
            params={"lat": lat, "lon": lon, "city": city, "country": country, "country_code": code},
            name="/weather",
        )

    @task(1)
    def saved_locations(self):
        self.client.get("/saved")

    @task(1)
    def search(self):
        self.client.get("/search", params={"q": random.choice(CITIES)[0]}, name="/search")
