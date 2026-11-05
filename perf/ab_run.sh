#!/usr/bin/env bash
# A/B load test: connection reuse off vs on, interleaved so network drift hits both equally.
# Usage: bash perf/ab_run.sh [output_dir]      (env: ROUNDS=3 DURATION=3m USERS=3 PORT=5050)
set -euo pipefail

OUT="${1:-_notes/metrics/ab}"
ROUNDS="${ROUNDS:-3}"
DURATION="${DURATION:-3m}"
USERS="${USERS:-3}"
PORT="${PORT:-5050}"   # not 5000: macOS AirPlay Receiver answers there with 403s
HOST="http://127.0.0.1:$PORT"
mkdir -p "$OUT"

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port $PORT is already in use:"; lsof -nP -iTCP:"$PORT" -sTCP:LISTEN
  echo "Stop that process or rerun with PORT=<free port>."; exit 1
fi

for round in $(seq 1 "$ROUNDS"); do
  for reuse in 0 1; do
    label="reuse${reuse}_round${round}"
    echo "== $label"
    PORT="$PORT" FLASK_DEBUG=0 HTTP_REUSE_CONNECTIONS="$reuse" python3 run.py > "$OUT/$label.server.log" 2>&1 &
    server_pid=$!
    trap 'kill $server_pid 2>/dev/null || true' EXIT

    # Wait until *our* app answers with a JSON list (not just any process on the port).
    ready=0
    for _ in $(seq 1 40); do
      if curl -sf "$HOST/saved" | grep -q '^\['; then ready=1; break; fi
      sleep 0.5
    done
    if [ "$ready" -ne 1 ]; then
      echo "Server did not start; see $OUT/$label.server.log"; exit 1
    fi

    # Keep going even if Locust reports failures, but surface them.
    locust -f perf/locustfile.py --host "$HOST" --headless -u "$USERS" -r 1 -t "$DURATION" \
      --csv "$OUT/$label" --only-summary || echo "!! $label: Locust reported failures, check $OUT/${label}_failures.csv"

    kill "$server_pid"
    wait "$server_pid" 2>/dev/null || true
    sleep 2
  done
done

echo
echo "Failures per run (should all be 0):"
for f in "$OUT"/*_stats.csv; do
  printf '  %s: ' "$(basename "$f" _stats.csv)"
  awk -F, '$2=="Aggregated" {print $4}' "$f"
done
echo
python3 perf/analyze_logs.py "$OUT"/*.server.log | tee "$OUT/summary.md"
