"""Constants for the WiZ Light integration."""
import logging
from datetime import timedelta

DOMAIN = "glimmr"
DEFAULT_NAME = "Glimmr"
LOGGER = logging.getLogger(__package__)
SCAN_INTERVAL = timedelta(seconds=10)
SERVICE_EFFECT = "effect"
