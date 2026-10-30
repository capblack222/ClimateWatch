"""Isolate where Open-Meteo latency comes from, independent of Flask.

Compares a new HTTPS connection per call against one pooled session, for both Open-Meteo APIs.
Modes are interleaved round by round, so network drift affects both equally. Round 1 is reported
separately because it is each location's first request (cold on Open-Meteo's side too).

Usage:
    python3 perf/probe_upstream.py --rounds 10 --csv _notes/metrics/probe_raw.csv
"""
import argparse
import csv
import math
import statistics
import time

import requests

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_PARAMS = {
    "current": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,wind_speed_10m,"
               "weather_code,is_day",
    "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
    "timezone": "auto",
    "forecast_days": 7,
}
# Separate locations per mode, so one mode can't warm Open-Meteo's cache for the other.
LOCATIONS = {
    "new_connection": [("Mumbai", 19.07, 72.88), ("Berlin", 52.52, 13.41), ("Niamey", 13.51, 2.11),
                       ("Lima", -12.05, -77.04), ("Osaka", 34.69, 135.50)],
    "pooled_session": [("Chicago", 41.88, -87.63), ("Nairobi", -1.29, 36.82), ("Pristina", 42.67, 21.17),
                       ("Hanoi", 21.03, 105.85), ("Perth", -31.95, 115.86)],
}


def nearest_rank(values, pct):
    """Nearest-rank percentile: the smallest value with at least pct% of samples at or below it."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(pct / 100 * len(ordered)) - 1)]


def timed(get, url, params):
    start = time.perf_counter()
    resp = get(url, params=params, timeout=15)
    elapsed = (time.perf_counter() - start) * 1000
    resp.raise_for_status()
    return elapsed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--csv", default=None)
    args = parser.parse_args()

    session = requests.Session()
    clients = {"new_connection": requests.get, "pooled_session": session.get}
    rows = []
    for rnd in range(1, args.rounds + 1):
        for mode, get in clients.items():
            for city, lat, lon in LOCATIONS[mode]:
                ms = timed(get, FORECAST_URL, {**FORECAST_PARAMS, "latitude": lat, "longitude": lon})
                rows.append({"round": rnd, "mode": mode, "api": "forecast", "city": city, "ms": round(ms, 1)})
                ms = timed(get, GEOCODING_URL, {"name": city, "count": 5, "language": "en", "format": "json"})
                rows.append({"round": rnd, "mode": mode, "api": "geocoding", "city": city, "ms": round(ms, 1)})
        print(f"round {rnd}/{args.rounds} done", flush=True)

    if args.csv:
        with open(args.csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    print("\n| API | Mode | Round 1 median (ms) | Rounds 2+ median | Rounds 2+ p95 | Rounds 2+ mean | n (rounds 2+) |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for api in ("forecast", "geocoding"):
        for mode in clients:
            first = [r["ms"] for r in rows if r["api"] == api and r["mode"] == mode and r["round"] == 1]
            rest = [r["ms"] for r in rows if r["api"] == api and r["mode"] == mode and r["round"] > 1]
            if not rest:
                continue
            print(f"| {api} | {mode} | {statistics.median(first):.0f} | {statistics.median(rest):.0f} | "
                  f"{nearest_rank(rest, 95):.0f} | {statistics.mean(rest):.0f} | {len(rest)} |")


if __name__ == "__main__":
    main()
