"""
Centralized logging configuration for the ordering system.

Every module should obtain its logger via `logging.getLogger(__name__)` and
never call `print()` for diagnostic output. `setup_logging()` wires up the
root logger with a console handler and a rotating file handler and is safe
to call multiple times (e.g. once from the app factory, once from a
standalone CLI script) without creating duplicate handlers.
"""
import logging
import logging.handlers
import os
from pathlib import Path

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_CONFIGURED_FLAG = "_bestellsystem_logging_configured"


def setup_logging(log_level=None, log_dir=None):
    """Configure the root logger with console + rotating file handlers.

    Args:
        log_level: Level name (e.g. "INFO", "DEBUG"). Falls back to the
            LOG_LEVEL env var, then "INFO".
        log_dir: Directory to write app.log into. Falls back to the
            LOG_DIR env var, then <flask_app>/data/logs.

    Returns:
        The configured root logger.
    """
    root = logging.getLogger()

    level_name = log_level or os.getenv("LOG_LEVEL", "INFO")
    level = getattr(logging, str(level_name).upper(), logging.INFO)

    if getattr(root, _CONFIGURED_FLAG, False):
        # Already configured (e.g. called from both main() and create_app());
        # just refresh the level in case it changed.
        root.setLevel(level)
        return root

    root.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    resolved_log_dir = Path(
        log_dir or os.getenv("LOG_DIR", Path(__file__).resolve().parent.parent / "data" / "logs")
    )
    try:
        resolved_log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            resolved_log_dir / "app.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError as e:
        root.warning(f"Could not set up file logging in {resolved_log_dir}: {e}")

    # Quiet down noisy third-party loggers without hiding our own app logs
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    setattr(root, _CONFIGURED_FLAG, True)
    return root
