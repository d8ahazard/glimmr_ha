"""Glimmr integration."""
import logging
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.switch import PLATFORM_SCHEMA
from homeassistant.const import CONF_HOST, CONF_NAME
from glimmr import Glimmr, SystemData

try:
    from homeassistant.components.switch import SwitchEntity
except ImportError:
    from homeassistant.components.switch import SwitchDevice as SwitchEntity

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_HOST): cv.string, vol.Required(CONF_NAME): cv.string}
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Glimmr switch platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    ip_address = config[CONF_HOST]
    switch = Glimmr(ip_address)

    async_add_entities([GlimmrPlug(switch, config[CONF_NAME])])


class GlimmrPlug(SwitchEntity):
    """Representation of Glimmr Switch."""

    def __init__(self, switch: Glimmr, name):
        """Initialize Glimmr."""
        self._switch = switch
        self._state = None
        self._name = name
        self._available = None
        self.async_update()

    @property
    def name(self):
        """Return the ip as name of the device if any."""
        return self._name

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state

    @property
    def should_poll(self):
        """Retrun True to add to poll."""
        return True

    def turn_on(self, **kwargs: Any) -> None:
        self._switch.mode(self._switch.device.previous_mode)

    async def async_turn_on(self, **kwargs):
        """Instruct the switch to turn on."""
        await self._switch.mode(self._switch.device.previous_mode)
        self._state = True
        self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Instruct the switch to turn off."""
        await self._switch.mode(0)
        self._state = False
        self.schedule_update_ha_state()

    @property
    def available(self):
        """Return if switch is available."""
        return self._available

    async def async_update(self):
        """Fetch new state data for this light."""
        await self.update_state()

    async def update_state_available(self):
        """Update the state if bulb is available."""
        self._state = self._switch.device.device_mode
        self._available = True
        _LOGGER.debug(
            "[Glimmr %s] updated state: %s; available: %s",
            self._switch.device.device_name,
            self._state,
            self._available,
        )

    async def update_state_unavailable(self):
        """Update the state if bulb is unavailable."""
        self._state = False
        self._available = False
        _LOGGER.debug(
            "[Glimmr %s] updated state: %s; available: %s",
            self._switch.device.device_name,
            self._state,
            self._available,
        )

    async def update_state(self):
        """Update the state."""
        try:
            _LOGGER.debug("[Glimmr %s] updating state", self._switch.device.device_name)
            await self._switch.update()
            if self._switch.device is None:
                await self.update_state_unavailable()
            else:
                await self.update_state_available()
        # pylint: disable=broad-except
        except Exception as ex:
            _LOGGER.error(ex)
            await self.update_state_unavailable()
        _LOGGER.debug("[Glimmr %s] updated state: %s", self._switch.device.device_name, self._state)
