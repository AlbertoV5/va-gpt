"""
System logger
"""
import logging
import json

# Logger
logging.basicConfig(
    filename=f"gpt-va.log",
    encoding="utf-8",
    level=logging.DEBUG,
    filemode="w",
)
logger = logging.getLogger(__name__)


def log_json(x: dict):
    """Log dict as JSON in DEBUG mode."""
    logger.debug(json.dumps(x, indent=4))
