"""Isolate where Open-Meteo latency comes from, independent of Flask.

Compares a new HTTPS connection per call against one pooled session, for both Open-Meteo APIs.
Both modes query the SAME locations (the ones the load test uses), and the mode that goes first
alternates every round, so city-specific server time and network drift affect both modes equally.
Output is broken down per city, so per-location differences are visible instead of averaged away.

Usage:
    python3 -m perf.probe_upstream --rounds 10 --csv _notes/metrics/probe_v2_raw.csv
"""
import argparse
import csv
import math
import statistics
import time

import requests

from app.services.geocoding_service import GEOCODING_URL, geocoding_params
from app.services.weather_service import FORECAST_URL, forecast_params
from perf.cities import CITIES  # not perf.locustfile: importing locust patches sockets via gevent


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
        order = list(clients) if rnd % 2 else list(reversed(clients))
        for mode in order:
            get = clients[mode]
            for city, _country, _code, lat, lon in CITIES:
                for api, url, params in (
                    ("forecast", FORECAST_URL, forecast_params(lat, lon)),
                    ("geocoding", GEOCODING_URL, geocoding_params(city)),
                ):
                    rows.append({"round": rnd, "mode": mode, "api": api, "city": city,
                                 "ms": round(timed(get, url, params), 1)})
        print(f"round {rnd}/{args.rounds} done", flush=True)

    if args.csv:
        with open(args.csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    # Round 1 includes the pooled session's one-off connection setup, so steady state is rounds 2+.
    steady = [r for r in rows if r["round"] > 1]

    print("\n## Overall (rounds 2+)\n")
    print("| API | Mode | n | p50 (ms) | p95 | Mean |")
    print("| --- | --- | --- | --- | --- | --- |")
    for api in ("forecast", "geocoding"):
        for mode in clients:
            ms = [r["ms"] for r in steady if r["api"] == api and r["mode"] == mode]
            print(f"| {api} | {mode} | {len(ms)} | {nearest_rank(ms, 50):.0f} | {nearest_rank(ms, 95):.0f} | "
                  f"{statistics.mean(ms):.0f} |")

    print("\n## Per city, median ms (rounds 2+)\n")
    print("| API | City | New connection | Pooled session | Saved |")
    print("| --- | --- | --- | --- | --- |")
    for api in ("forecast", "geocoding"):
        for city, *_ in CITIES:
            med = {mode: statistics.median(r["ms"] for r in steady
                                           if r["api"] == api and r["mode"] == mode and r["city"] == city)
                   for mode in clients}
            saved = med["new_connection"] - med["pooled_session"]
            print(f"| {api} | {city} | {med['new_connection']:.0f} | {med['pooled_session']:.0f} | {saved:.0f} |")


if __name__ == "__main__":
    main()
