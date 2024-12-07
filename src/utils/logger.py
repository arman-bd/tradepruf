import json
import logging
import sys
from pathlib import Path
from typing import Any


class LoggerConfig:
    """Logger configuration settings."""

    DEFAULT_CONFIG = {
        "console": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "enabled": True,
        },
        "file": {
            "level": "DEBUG",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "enabled": True,
            "filename": "tradepruf.log",
            "max_size": 10485760,  # 10MB
            "backup_count": 5,
        },
    }

    def __init__(self, config_path: str | Path | None = None):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str | Path | None) -> dict[str, Any]:
        """Load configuration from file or use defaults."""
        if config_path:
            try:
                with open(config_path) as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load logger config: {e}")
        return self.DEFAULT_CONFIG


class LogManager:
    """Manages logging configuration and creation."""

    _instance = None
    _loggers: dict[str, logging.Logger] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.config = LoggerConfig()
        return cls._instance

    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger with the given name."""
        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)  # Set base level to DEBUG
        logger.propagate = False  # Prevent double logging

        self._setup_console_handler(logger)
        self._setup_file_handler(logger)

        self._loggers[name] = logger
        return logger

    def _setup_console_handler(self, logger: logging.Logger):
        """Set up console logging."""
        console_config = self.config.config["console"]
        if console_config["enabled"]:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, console_config["level"]))
            console_formatter = logging.Formatter(console_config["format"])
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

    def _setup_file_handler(self, logger: logging.Logger):
        """Set up file logging."""
        file_config = self.config.config["file"]
        if file_config["enabled"]:
            try:
                # Create logs directory if it doesn't exist
                log_dir = Path("logs")
                log_dir.mkdir(exist_ok=True)

                # Create rotating file handler
                from logging.handlers import RotatingFileHandler

                log_file = log_dir / file_config["filename"]
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=file_config["max_size"],
                    backupCount=file_config["backup_count"],
                )
                file_handler.setLevel(getattr(logging, file_config["level"]))
                file_formatter = logging.Formatter(file_config["format"])
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                # If file logging fails, log to console
                logger.warning(f"Could not set up file logging: {e}")


# Global log manager instance
_log_manager = LogManager()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: The name of the logger, typically __name__

    Returns:
        A configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting application...")
    """
    return _log_manager.get_logger(name)
