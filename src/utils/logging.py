"""Logging utilities for the democratic decision-making system."""

import logging
from typing import Optional


def get_logger(name: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Get a configured logger.

    Args:
        name: Logger name (default: 'democratic_ml')
        level: Logging level

    Returns:
        Configured logger instance
    """
    if name is None:
        name = "democratic_ml"

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
