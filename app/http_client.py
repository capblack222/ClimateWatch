"""Outbound HTTP for Open-Meteo calls: optional connection reuse plus per-request timing.

Every call adds its wall-clock time to `g.upstream_ms`, and every TCP/TLS handshake urllib3 performs is
counted in `g.upstream_new_connections`, so the request log shows directly whether a request reused a
pooled connection or paid for a fresh handshake. Scripts without a Flask context (perf/idle_probe.py)
read the process-wide `new_connections_total()` instead.
"""
import threading
import time

import requests
from flask import current_app, g, has_app_context
from requests.adapters import HTTPAdapter
from urllib3.connection import HTTPConnection, HTTPSConnection
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool

_session = None
_total_connects = 0
_total_lock = threading.Lock()


def new_connections_total():
    """Handshakes performed by counting sessions in this process, across all threads."""
    return _total_connects


class _CountsConnects:
    """Counts at connect(), the one place every handshake passes through. This includes urllib3 reopening a
    pooled connection the server dropped, which reuses the same object and logs no 'Starting new' line."""

    def connect(self):
        global _total_connects
        super().connect()
        with _total_lock:
            _total_connects += 1
        if has_app_context():
            g.upstream_new_connections = g.get("upstream_new_connections", 0) + 1


class _CountingHTTPConnection(_CountsConnects, HTTPConnection):
    pass


class _CountingHTTPSConnection(_CountsConnects, HTTPSConnection):
    pass


class _CountingHTTPPool(HTTPConnectionPool):
    ConnectionCls = _CountingHTTPConnection


class _CountingHTTPSPool(HTTPSConnectionPool):
    ConnectionCls = _CountingHTTPSConnection


class _CountingAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        super().init_poolmanager(*args, **kwargs)
        self.poolmanager.pool_classes_by_scheme = {"http": _CountingHTTPPool, "https": _CountingHTTPSPool}


def counting_session(**adapter_kwargs):
    """A requests Session whose handshakes are counted (see module docstring)."""
    session = requests.Session()
    adapter = _CountingAdapter(**adapter_kwargs)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def _shared_session():
    """One pooled Session per process, so TCP and TLS connections are reused across requests."""
    global _session
    if _session is None:
        _session = counting_session(pool_connections=4, pool_maxsize=10)
    return _session


def _reuse_connections():
    return has_app_context() and current_app.config.get("HTTP_REUSE_CONNECTIONS", True)


def get(url, **kwargs):
    start = time.perf_counter()
    try:
        if _reuse_connections():
            return _shared_session().get(url, **kwargs)
        # Same as requests.get (a throwaway session per call), but with the counting adapter.
        with counting_session() as session:
            return session.get(url, **kwargs)
    finally:
        if has_app_context():
            elapsed = (time.perf_counter() - start) * 1000
            g.upstream_ms = g.get("upstream_ms", 0.0) + elapsed
            g.upstream_calls = g.get("upstream_calls", 0) + 1
