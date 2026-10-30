"""Outbound HTTP for Open-Meteo calls: optional connection reuse plus per-request timing.

Every call adds its wall-clock time to `g.upstream_ms`, so the request log can show how much of a
request was spent waiting on external APIs versus inside the app.
"""
import time

import requests
from flask import current_app, g, has_app_context
from requests.adapters import HTTPAdapter

_session = None


def _shared_session():
    """One pooled Session per process, so TCP and TLS connections are reused across requests."""
    global _session
    if _session is None:
        _session = requests.Session()
        adapter = HTTPAdapter(pool_connections=4, pool_maxsize=10)
        _session.mount("https://", adapter)
    return _session


def _reuse_connections():
    return has_app_context() and current_app.config.get("HTTP_REUSE_CONNECTIONS", True)


def get(url, **kwargs):
    client = _shared_session() if _reuse_connections() else requests
    start = time.perf_counter()
    try:
        return client.get(url, **kwargs)
    finally:
        if has_app_context():
            elapsed = (time.perf_counter() - start) * 1000
            g.upstream_ms = g.get("upstream_ms", 0.0) + elapsed
            g.upstream_calls = g.get("upstream_calls", 0) + 1
