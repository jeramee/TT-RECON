import json
import logging
from datetime import datetime, timezone

def get_logger(name: str = "ttrecon") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    h = logging.StreamHandler()
    fmt = logging.Formatter("%(message)s")
    h.setFormatter(fmt)
    logger.addHandler(h)
    return logger

def log_event(logger: logging.Logger, event: str, **kwargs) -> None:
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **kwargs,
    }
    logger.info(json.dumps(payload, ensure_ascii=False))
