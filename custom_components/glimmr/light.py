"""Support for LED lights."""
from __future__ import annotations

from collections import Set
from typing import Any, List

import voluptuous as vol

from homeassistant.components.light import (
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    COLOR_MODE_RGB,
    SUPPORT_EFFECT,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import (
    ATTR_INTENSITY,
    ATTR_PALETTE,
    ATTR_PRESET,
    ATTR_REVERSE,
    ATTR_SPEED,
    DOMAIN,
    LOGGER,
    SERVICE_EFFECT,
    SERVICE_PRESET,
)
from .coordinator import GlimmrDataUpdateCoordinator
from .helpers import glimmr_exception_handler
from .models import GlimmrEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Glimmr light based on a config entry."""
    coordinator: GlimmrDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_EFFECT,
        {
            vol.Optional(ATTR_EFFECT): vol.Any(cv.positive_int, cv.string),
            vol.Optional(ATTR_INTENSITY): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=255)
            ),
            vol.Optional(ATTR_PALETTE): vol.Any(cv.positive_int, cv.string),
            vol.Optional(ATTR_REVERSE): cv.boolean,
            vol.Optional(ATTR_SPEED): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=255)
            ),
        },
        "async_effect",
    )

    platform.async_register_entity_service(
        SERVICE_PRESET,
        {
            vol.Required(ATTR_PRESET): vol.All(
                vol.Coerce(int), vol.Range(min=-1, max=65535)
            ),
        },
        "async_preset",
    )

    if coordinator.keep_master_light:
        async_add_entities([GlimmrBulb(coordinator=coordinator)])


class GlimmrBulb(GlimmrEntity, LightEntity):
    """Representation of Glimmr device."""
    _attr_icon = "mdi:led-strip-variant"
    _attr_color_mode = COLOR_MODE_RGB
    _attr_supported_features = SUPPORT_EFFECT

    def __init__(self, coordinator: GlimmrDataUpdateCoordinator) -> None:
        """Initialize Glimmr master light."""
        super().__init__(coordinator=coordinator)
        self._attr_name = f"{coordinator.data.device_name} Master"
        self._attr_unique_id = coordinator.data.device_id
        self._attr_supported_color_modes = {COLOR_MODE_RGB}
        self._scenes: List[str] = []
        self.update_scene_list()
        if (
                not self.coordinator.glimmr.connected
                and not self.coordinator.unsub
        ):
            LOGGER.debug("Starting websocket.")
            self.coordinator._use_websocket()

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 1..255."""
        return 255

    @property
    def is_on(self) -> bool:
        """Return the state of the light."""
        return bool(self.coordinator.data.device_mode == 0)

    @property
    def available(self) -> bool:
        """Return if this master light is available or not."""
        return self.coordinator.glimmr.connected and super().available

    @glimmr_exception_handler
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""        
        await self.coordinator.glimmr.mode(0)

    @glimmr_exception_handler
    async def async_turn_on(self, **kwargs: Any) -> None:
        if ATTR_RGB_COLOR in kwargs:
            rgb = kwargs[ATTR_RGB_COLOR]
            color = '#%02x%02x%02x' % rgb
            LOGGER.debug("Setting ambient color to " + color)
            await self.coordinator.glimmr.ambient_color(color)
            return

        if ATTR_EFFECT in kwargs:
            scene_id = kwargs[ATTR_EFFECT]
            s_id = self.coordinator.data.get_id_from_scene_name(scene_id)
            if s_id < -1:
                mode = self.coordinator.data.previous_mode
                if s_id == -2:
                    mode = 1
                if s_id == -3:
                    mode = 2
                if s_id == -4:
                    mode = 3
                if s_id == -5:
                    mode = 4
                if s_id == -6:
                    mode = 5
                if s_id == -7:
                    mode = 6
                await self.coordinator.glimmr.mode(mode)
                return
            else:
                LOGGER.debug(
                    "[glimmrlight %s] Setting ambient scene: %s",
                    self.coordinator.data.device_name,
                    s_id
                )
                await self.coordinator.glimmr.ambient_scene(s_id)

        else:
            LOGGER.debug("Setting mode to %s", self.coordinator.data.previous_mode)
            await self.coordinator.glimmr.mode(self.coordinator.data.previous_mode)

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_EFFECT

    @property
    def supported_color_modes(self) -> Set[str]:
        return {COLOR_MODE_RGB}

    @property
    def effect_list(self):
        """Return the list of supported effects.

        URL: https://docs.pro.glimmrconnected.com/#light-modes
        """
        return self._scenes

    async def async_effect(
        self,
        effect: int | None = None
    ) -> None:
        """Set the effect of a Glimmr light."""
        await self.coordinator.glimmr.ambient_scene(effect)

    async def update_scene_list(self):
        """Update the scene list."""
        _value = await self.coordinator.glimmr.update_scenes()
        self._scenes = list(_value.keys())
        LOGGER.debug("Updating scene list: ", self._scenes)


