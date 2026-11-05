"""Exact server-side latency from the app's JSON request logs (Locust's own percentiles are bucketed).

Splits each request into time waiting on Open-Meteo (upstream_ms) and time inside the app.

Usage:
    python3 perf/analyze_logs.py _notes/metrics/ab/*.server.log
"""
import json
import math
import statistics
import sys
from collections import defaultdict


def nearest_rank(values, pct):
    """Nearest-rank percentile: the smallest value with at least pct% of samples at or below it."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(pct / 100 * len(ordered)) - 1)]


def new_connection_rate(entries):
    """New connections per upstream call, over entries logged after the counter existed (None if none were)."""
    tracked = [e for e in entries if "upstream_new_connections" in e]
    calls = sum(e.get("upstream_calls", 0) for e in tracked)
    if not calls:
        return None
    return sum(e["upstream_new_connections"] for e in tracked) / calls


def load(paths):
    groups = defaultdict(list)
    for path in paths:
        with open(path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if entry.get("logger") != "app.request" or entry.get("status") != 200:
                    continue
                mode = "reuse on" if entry.get("http_reuse") else "reuse off"
                groups[(entry["path"], mode)].append(entry)
    return groups


def main(paths):
    groups = load(paths)
    print("| Endpoint | Connections | n | p50 (ms) | p95 | p99 | Mean | Mean upstream | Mean in-app "
          "| New conn. per call |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for (path, mode), entries in sorted(groups.items()):
        total = [e["duration_ms"] for e in entries]
        upstream = [e.get("upstream_ms", 0.0) for e in entries]
        in_app = [t - u for t, u in zip(total, upstream, strict=True)]
        rate = new_connection_rate(entries)
        new_rate = f"{rate:.0%}" if rate is not None else "-"
        p99 = f"{nearest_rank(total, 99):.0f}" if len(total) >= 100 else "n<100"
        print(
            f"| {path} | {mode} | {len(total)} | {nearest_rank(total, 50):.0f} | {nearest_rank(total, 95):.0f} | "
            f"{p99} | {statistics.mean(total):.0f} | {statistics.mean(upstream):.0f} | "
            f"{statistics.mean(in_app):.1f} | {new_rate} |"
        )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
