"""Does Open-Meteo close idle keep-alive connections? Measures one pooled session with growing idle gaps.

For each gap, makes N calls separated by that pause, and records latency plus whether urllib3 had to
open a new connection. If a host closes idle connections after T seconds, calls after gaps > T will
show ~100% new connections and handshake-level latency.

Usage:
    python3 -m perf.idle_probe --calls 8 --csv _notes/metrics/idle_probe_raw.csv
"""
import argparse
import csv
import statistics
import time

from app import http_client
from app.services.geocoding_service import GEOCODING_URL, geocoding_params
from app.services.weather_service import FORECAST_URL, forecast_params
from perf.cities import CITIES

GAPS_S = [0, 0.5, 1, 2, 3, 5, 10]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--calls", type=int, default=8)
    parser.add_argument("--csv", default=None)
    args = parser.parse_args()

    _city, _country, _code, lat, lon = CITIES[0]
    apis = {
        "forecast": (FORECAST_URL, forecast_params(lat, lon)),
        "geocoding": (GEOCODING_URL, geocoding_params(CITIES[0][0])),
    }
    rows = []
    for api, (url, params) in apis.items():
        for gap in GAPS_S:
            session = http_client.counting_session()
            session.get(url, params=params, timeout=15).raise_for_status()  # open the connection once
            for _ in range(args.calls):
                time.sleep(gap)
                before = http_client.new_connections_total()
                start = time.perf_counter()
                session.get(url, params=params, timeout=15).raise_for_status()
                rows.append({"api": api, "gap_s": gap, "ms": round((time.perf_counter() - start) * 1000, 1),
                             "new_connection": http_client.new_connections_total() - before})
            session.close()
            print(f"{api} gap={gap}s done", flush=True)

    if args.csv:
        with open(args.csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    print("\n| API | Idle gap (s) | n | Median (ms) | New connections |")
    print("| --- | --- | --- | --- | --- |")
    for api in apis:
        for gap in GAPS_S:
            sel = [r for r in rows if r["api"] == api and r["gap_s"] == gap]
            new = sum(r["new_connection"] for r in sel)
            print(f"| {api} | {gap} | {len(sel)} | {statistics.median(r['ms'] for r in sel):.0f} | "
                  f"{new}/{len(sel)} |")


if __name__ == "__main__":
    main()
