#!/usr/bin/env bash
# A/B load test: connection reuse off vs on, interleaved so network drift hits both equally.
# Usage: bash perf/ab_run.sh [output_dir]      (env: ROUNDS=3 DURATION=3m USERS=3)
set -euo pipefail

OUT="${1:-_notes/metrics/ab}"
ROUNDS="${ROUNDS:-3}"
DURATION="${DURATION:-3m}"
USERS="${USERS:-3}"
HOST="http://127.0.0.1:5000"
mkdir -p "$OUT"

for round in $(seq 1 "$ROUNDS"); do
  for reuse in 0 1; do
    label="reuse${reuse}_round${round}"
    echo "== $label"
    FLASK_DEBUG=0 HTTP_REUSE_CONNECTIONS="$reuse" python3 run.py > "$OUT/$label.server.log" 2>&1 &
    server_pid=$!
    trap 'kill $server_pid 2>/dev/null || true' EXIT

    for _ in $(seq 1 40); do
      curl -s -o /dev/null "$HOST/saved" && break
      sleep 0.5
    done

    locust -f perf/locustfile.py --host "$HOST" --headless -u "$USERS" -r 1 -t "$DURATION" \
      --csv "$OUT/$label" --only-summary

    kill "$server_pid"
    wait "$server_pid" 2>/dev/null || true
    sleep 2
  done
done

python3 perf/analyze_logs.py "$OUT"/*.server.log | tee "$OUT/summary.md"
