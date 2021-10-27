"""Glimmr integration."""
import logging
from datetime import timedelta
from typing import List, Any, Tuple, Set

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from glimmr import Glimmr, SystemData
from glimmr.exceptions import GlimmrConnectionError, GlimmrError
# Import the device class from the component
from homeassistant.components.light import (
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    COLOR_MODE_RGB,
    PLATFORM_SCHEMA,
    SUPPORT_EFFECT,
    LightEntity,
)
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.util import slugify

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_HOST): cv.string, vol.Required(CONF_NAME): cv.string}
)

# set poll interval to 30 sec because of changes from external to the bulb
SCAN_INTERVAL = timedelta(seconds=15)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Glimmr platform from legacy config."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    ip_address = config[CONF_HOST]
    try:
        bulb = Glimmr(ip_address)
        # Add devices
        _LOGGER.debug("Creating light %s", ip_address)
        async_add_entities([GlimmrBulb(bulb)], update_before_add=True)
        return True
    except GlimmrConnectionError:
        _LOGGER.error("Can't add device with ip %s.", ip_address)
        return False


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Glimmr platform from config_flow."""
    # Assign configuration variables.
    bulb = hass.data[DOMAIN][entry.unique_id]
    _LOGGER.debug("Setting up glimmr: ")
    glimmr = GlimmrBulb(bulb)
    _LOGGER.debug("ASE", glimmr)
    # Add devices with defined name
    async_add_entities([glimmr], update_before_add=True)

    # Register services
    async def async_update(call=None):
        """Trigger update."""
        _LOGGER.debug("[glimmr light %s] update requested", entry.data.get(CONF_HOST))
        await glimmr.async_update()
        await glimmr.async_update_ha_state()

    service_name = slugify(f"{entry.data.get(CONF_NAME)} updateService")
    hass.services.async_register(DOMAIN, service_name, async_update)
    return True


class GlimmrBulb(LightEntity):
    _attr_icon = "mdi:led-strip-variant"
    """Representation of Glimmr device."""

    def turn_off(self, **kwargs: Any) -> None:
        self._glimmr.mode(0)

    def turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""
        if ATTR_RGB_COLOR in kwargs:
            self._glimmr.ambient_color(kwargs.get(ATTR_RGB_COLOR))

        if ATTR_EFFECT in kwargs:
            scene_id = self._light.get_id_from_scene_name(kwargs[ATTR_EFFECT])

            if scene_id == -2:  # rhythm
                _LOGGER.warning("Invalid scene specified: " + kwargs[ATTR_EFFECT])
            else:
                _LOGGER.debug(
                    "[glimmrlight %s] Setting ambient scene: %s",
                    self._light.device_name,
                    scene_id
                )
                self._glimmr.ambient_scene(scene_id)

        else:
            self._glimmr.mode(self._glimmr.device.previous_mode)

    def __init__(self, light: Glimmr):
        """Initialize an Glimmr."""
        self._glimmr: Glimmr = light
        self._light: SystemData = light.device
        self._state = self._light.device_mode
        self._brightness = 100
        self._name = self._light.device_name
        self.rgb_color = bytes.fromhex(self._light.ambient_color)
        self._available = None
        self._effect = self._light.ambient_scene
        self._scenes: List[str] = []
        self.update_scene_list()
        if self._light.auto_disabled:
            self._state = 0

    @property
    def brightness(self):
        """Unused."""
        return self._brightness

    @property
    def rgb_color(self) -> Tuple[int, int, int]:
        """Return the ambient color property."""
        return self._rgb_color

    @property
    def name(self):
        """Return the ip as name of the device if any."""
        return self._name

    @property
    def unique_id(self):
        """Return light unique_id."""
        return self._name

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state != 0

    async def async_turn_on(self, **kwargs):
        """Instruct the light to turn on."""

        if ATTR_RGB_COLOR in kwargs:

            _LOGGER.debug("Setting ambient color to $" + kwargs[ATTR_RGB_COLOR])
            await self._glimmr.ambient_color(kwargs[ATTR_RGB_COLOR])
            return

        if ATTR_EFFECT in kwargs:
            scene_id = self._light.get_id_from_scene_name(kwargs[ATTR_EFFECT])

            if scene_id == -2:  # rhythm
                _LOGGER.warning("Invalid scene specified: " + kwargs[ATTR_EFFECT])
            else:
                _LOGGER.debug(
                    "[glimmrlight %s] Setting ambient scene: %s",
                    self._light.device_name,
                    scene_id
                )
                await self._glimmr.ambient_scene(scene_id)

        else:
            _LOGGER.debug("Setting mode to %s", self._glimmr.device.previous_mode)
            await self._glimmr.mode(self._glimmr.device.previous_mode)

    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        await self._glimmr.mode(0)

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_EFFECT

    @property
    def supported_color_modes(self) -> Set[str]:
        return {COLOR_MODE_RGB}

    @property
    def effect(self):
        """Return the current effect."""
        return self._effect

    @property
    def effect_list(self):
        """Return the list of supported effects.

        URL: https://docs.pro.glimmrconnected.com/#light-modes
        """
        return self._scenes

    @property
    def available(self):
        """Return if light is available."""
        return self._available

    async def async_update(self):
        """Fetch new state data for this light."""
        await self.update_state()

        if self._state is not None and self._state is not False:
            self.update_color()
            self.update_effect()
            self.update_mode()
            await self.update_scene_list()

    @property
    def device_info(self):
        """Get device specific attributes."""
        _LOGGER.debug(
            "[glimmrlight %s] Call device info...",
            self._name
        )
        return {
            "identifiers": {(DOMAIN, self._name)},
            "name": self._name,
            "manufacturer": "D8ahazard",
            "model": "Glimmr",
        }

    def update_state_available(self):
        """Update the state if bulb is available."""
        self._state = self._light.device_mode
        self._available = True

    def update_state_unavailable(self):
        """Update the state if bulb is unavailable."""
        self._state = False
        self._available = False

    async def update_state(self):
        """Update the state."""
        try:
            await self._glimmr.update()
            self._light = self._glimmr.device
            self.update_state_available()
        except TimeoutError as ex:
            _LOGGER.debug(ex)
            self.update_state_unavailable()
        except GlimmrError as ex:
            _LOGGER.debug(ex)
            self.update_state_unavailable()
        _LOGGER.debug(
            "[glimmrlight %s] updated state: %s and available: %s",
            self._name,
            self._state,
            self._available,
        )

    def update_color(self):
        """Update the hs color."""
        self._rgb_color = self._light.ambient_color

    def update_effect(self):
        """Update the bulb scene."""
        self._effect = self._light.ambient_scene

    async def update_scene_list(self):
        """Update the scene list."""
        _value = await self._glimmr.update_scenes()
        self._scenes = list(_value.keys())
        _LOGGER.debug("Updating scene list: ", self._scenes)

    def update_mode(self):
        pass

    @rgb_color.setter
    def rgb_color(self, value):
        self._rgb_color = value
