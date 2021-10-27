"""Models for Glimmr."""
from homeassistant.const import (
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_NAME,
    ATTR_SW_VERSION,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GlimmrDataUpdateCoordinator


class GlimmrEntity(CoordinatorEntity):
    """Defines a base Glimmr entity."""

    coordinator: GlimmrDataUpdateCoordinator

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Glimmr device."""
        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self.coordinator.data.device_name)},
            ATTR_NAME: self.coordinator.data.device_name,
            ATTR_MANUFACTURER: "d8ahazard",
            ATTR_MODEL: "glimmr",
            ATTR_SW_VERSION: self.coordinator.data.version,
        }
