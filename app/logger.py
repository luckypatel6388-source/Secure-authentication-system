import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.core.config import settings

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE_PATH = LOG_DIR / "app.log"

# Define Log Format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    """Configures global logging for stdout console and file output."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Root Logger Config
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear pre-existing handlers to prevent duplicate output
    if logger.hasHandlers():
        logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # 1. Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. File Handler (Rotating log files: max 5MB each, keeps last 3 copies)
    file_handler = RotatingFileHandler(
        filename=LOG_FILE_PATH,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Quiet overly noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING if not settings.DEBUG else logging.INFO)

    logger.info(f"Logging initialized at level: {logging.getLevelName(log_level)}")


# Instantiate custom logger getter for modules
def get_module_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)