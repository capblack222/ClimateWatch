"""JSON logging: one JSON object per line, ready for CloudWatch Logs Insights later."""
import json
import logging
import sys
from datetime import datetime, timezone

# Attributes every LogRecord has; anything else on a record came from `extra=` and is logged as a field.
_STANDARD_ATTRS = set(vars(logging.LogRecord("", 0, "", 0, "", None, None))) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update({k: v for k, v in vars(record).items() if k not in _STANDARD_ATTRS})
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level="INFO"):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    # The app logs every request itself (with duration), so Werkzeug's plain-text access log is redundant.
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
