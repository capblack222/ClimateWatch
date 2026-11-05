"""Outbound HTTP for Open-Meteo calls: optional connection reuse plus per-request timing.

Every call adds its wall-clock time to `g.upstream_ms`, and every new TCP/TLS connection that urllib3
opens is counted in `g.upstream_new_connections`, so the request log shows directly whether a request
reused a pooled connection or paid for a fresh handshake.
"""
import logging
import time

import requests
from flask import current_app, g, has_app_context
from requests.adapters import HTTPAdapter

_session = None
_URLLIB3_LOGGER = "urllib3.connectionpool"


class _NewConnectionCounter(logging.Handler):
    """Counts urllib3's 'Starting new HTTPS connection' events against the current request."""

    def emit(self, record):
        if record.levelno >= logging.WARNING:
            logging.getLogger().handle(record)  # keep urllib3 warnings visible in the normal log stream
            return
        if record.msg.startswith("Starting new HTTP") and has_app_context():
            g.upstream_new_connections = g.get("upstream_new_connections", 0) + 1


def install_connection_counter():
    """Idempotent. urllib3 reports new connections only at DEBUG, so capture that logger privately."""
    logger = logging.getLogger(_URLLIB3_LOGGER)
    if not any(isinstance(h, _NewConnectionCounter) for h in logger.handlers):
        logger.addHandler(_NewConnectionCounter())
        logger.setLevel(logging.DEBUG)
        logger.propagate = False  # don't print urllib3 debug lines; warnings are re-emitted above


def _shared_session():
    """One pooled Session per process, so TCP and TLS connections are reused across requests."""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.mount("https://", HTTPAdapter(pool_connections=4, pool_maxsize=10))
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
