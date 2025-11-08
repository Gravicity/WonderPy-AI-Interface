"""
Logging Configuration
Sets up structured logging for the application
"""

import logging
import sys
from pathlib import Path
from pythonjsonlogger import jsonlogger
from utils.config import settings


def setup_logging():
    """Configure application logging"""

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Console handler with color formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    if settings.ENVIRONMENT == "production":
        # JSON formatter for production
        json_formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s"
        )
        console_handler.setFormatter(json_formatter)
    else:
        # Human-readable formatter for development
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    # File handler for persistent logs
    file_handler = logging.FileHandler(log_dir / "wonderpy.log")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return logger
