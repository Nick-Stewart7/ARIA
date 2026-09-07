"""Central logging configuration for the ARIA server process.

Called once, at the true entrypoint (cli.py), before any other aria module
is imported — so nothing else gets a chance to call logging.basicConfig()
first and lock in console-only output (basicConfig is a no-op once the root
logger already has handlers).
"""
import logging
import logging.handlers
import os
from pathlib import Path

MAX_BYTES = 5_000_000
BACKUP_COUNT = 5


def configure_logging() -> None:
    log_dir = Path(os.getenv("LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "aria.log", maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    root.addHandler(file_handler)
    root.addHandler(console_handler)
