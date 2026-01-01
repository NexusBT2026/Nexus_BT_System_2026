"""
logging_utils.py: Structured logging setup for Hyperliquid integration.
Supports both standard and JSON log formatting for production use.
"""
import logging
import json
from typing import Any, Optional

class JsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Include any extra fields passed via logger.info(..., extra={...})
        extra_fields = getattr(record, 'extra_fields', None)
        if isinstance(extra_fields, dict):
            log_record.update(extra_fields)
        return json.dumps(log_record)

def setup_logger(name: str = 'hyperliquid', level: int = logging.INFO, json_logs: bool = False) -> logging.Logger:
    """
    Set up and return a logger with a standard or JSON format for the Hyperliquid integration.

    Args:
        name (str): Name of the logger.
        level (int): Logging level (e.g., logging.INFO).
        json_logs (bool): If True, use JSON log formatting.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        if json_logs:
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger