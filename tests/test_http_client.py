import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from flask import g

from app import http_client
from app.services.weather_service import FORECAST_URL, fetch_weather
from tests.payloads import FORECAST

SERVER_IDLE_TIMEOUT_S = 0.2


@pytest.fixture
def local_server(monkeypatch):
    """A real keep-alive HTTP server on localhost. `responses` replaces the socket layer, so it can't show
    whether urllib3 actually opened a connection; this can. It closes idle connections after
    SERVER_IDLE_TIMEOUT_S, like an upstream that drops idle keep-alives."""

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"  # keep-alive, so the client can pool the connection
        timeout = SERVER_IDLE_TIMEOUT_S

        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setattr(http_client, "_session", None)  # start with an empty pool
    yield f"http://127.0.0.1:{server.server_port}/"
    server.shutdown()
    server.server_close()


def test_reused_connection_is_not_counted_again(app, local_server):
    with app.test_request_context():
        http_client.get(local_server, timeout=5)
        http_client.get(local_server, timeout=5)
        assert g.upstream_new_connections == 1


def test_reconnect_of_a_dropped_pooled_connection_is_counted(app, local_server):
    with app.test_request_context():
        http_client.get(local_server, timeout=5)
        time.sleep(SERVER_IDLE_TIMEOUT_S * 3)  # server closes the idle connection; urllib3 reconnects it
        http_client.get(local_server, timeout=5)
        assert g.upstream_new_connections == 2


def test_process_total_counts_outside_an_app_context(local_server):
    # Standalone scripts (perf/idle_probe.py) have no Flask `g`, so they read the process-wide total.
    session = http_client.counting_session()
    before = http_client.new_connections_total()
    session.get(local_server, timeout=5)
    time.sleep(SERVER_IDLE_TIMEOUT_S * 3)  # server drops the idle connection; urllib3 reconnects it
    session.get(local_server, timeout=5)
    session.close()
    assert http_client.new_connections_total() - before == 2


def test_reuse_off_counts_every_call(app, local_server):
    app.config["HTTP_REUSE_CONNECTIONS"] = False
    with app.test_request_context():
        http_client.get(local_server, timeout=5)
        http_client.get(local_server, timeout=5)
        assert g.upstream_new_connections == 2


def test_upstream_time_is_recorded_per_request(app, mocked_http):
    mocked_http.get(FORECAST_URL, json=FORECAST)
    with app.test_request_context():
        fetch_weather(1, 2)
        fetch_weather(1, 2)
        assert g.upstream_calls == 2
        assert g.upstream_ms > 0


def test_reuse_uses_one_shared_session(app, mocked_http, monkeypatch):
    mocked_http.get(FORECAST_URL, json=FORECAST)
    monkeypatch.setattr(http_client, "_session", None)
    with app.test_request_context():
        fetch_weather(1, 2)
        first = http_client._session
        fetch_weather(1, 2)
        assert first is not None and http_client._session is first


def test_reuse_off_bypasses_the_session(app, mocked_http, monkeypatch):
    mocked_http.get(FORECAST_URL, json=FORECAST)
    monkeypatch.setattr(http_client, "_session", None)
    app.config["HTTP_REUSE_CONNECTIONS"] = False
    with app.test_request_context():
        fetch_weather(1, 2)
    assert http_client._session is None


def test_request_log_includes_upstream_fields(client, mocked_http, caplog):
    mocked_http.get(FORECAST_URL, json=FORECAST)
    caplog.set_level("INFO", logger="app.request")
    client.get("/weather?lat=1&lon=2")
    record = next(r for r in caplog.records if r.name == "app.request")
    assert record.upstream_calls == 1
    assert record.upstream_ms > 0
    assert record.http_reuse is True


def test_urllib3_warnings_still_reach_the_root_logger(app, caplog):
    import logging

    caplog.set_level("WARNING")
    logging.getLogger("urllib3.connectionpool").warning("Connection pool is full, discarding connection")
    assert "Connection pool is full" in caplog.text
