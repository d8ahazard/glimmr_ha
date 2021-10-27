"""DataUpdateCoordinator for Glimmr."""
from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from glimmr import Glimmr, SystemData, GlimmrError, GlimmrConnectionError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC, CONF_HOST, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import (
    CONF_KEEP_MASTER_LIGHT,
    DEFAULT_KEEP_MASTER_LIGHT,
    DOMAIN,
    LOGGER,
    SCAN_INTERVAL,
)


class GlimmrDataUpdateCoordinator(DataUpdateCoordinator[SystemData]):
    """Class to manage fetching Glimmr data from single endpoint."""

    keep_master_light: bool

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        entry: ConfigEntry,
    ) -> None:
        """Initialize global Glimmr data updater."""
        self.keep_master_light = entry.options.get(
            CONF_KEEP_MASTER_LIGHT, DEFAULT_KEEP_MASTER_LIGHT
        )
        LOGGER.debug("Creating glimmr with coord: " + entry.data[CONF_HOST])
        self.glimmr = Glimmr(entry.data[CONF_HOST], session=async_get_clientsession(hass))
        self.glimmr.set_logger(LOGGER)
        self.unsub: Callable | None = None
        self.hass = hass

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    @property
    def has_master_light(self) -> bool:
        """Return if the coordinated device has an master light."""
        return True

    def update_listeners(self) -> None:
        """Call update on all listeners."""
        for update_callback in self._listeners:
            update_callback()
            
    def load_data(self, data: SystemData):
        LOGGER.debug("Loading data!")
        self.data = data
        
    @callback
    def _use_websocket(self) -> None:
        """Use WebSocket for updates, instead of polling."""
        LOGGER.debug("Using websocket.")

        async def listen() -> None:
            """Listen for state changes via WebSocket."""
            LOGGER.debug("Listening")
            try:
                LOGGER.debug("Awaiting connection...")
                await self.glimmr.connect()
                LOGGER.debug("Connected!")
            except GlimmrConnectionError as ce:
                self.logger.info(ce)
            except GlimmrError as err:
                self.logger.info(err)
                if self.unsub:
                    self.unsub()
                    self.unsub = None
                return

            try:
                self.glimmr.add_callback("olo", self.load_data)
                while self.glimmr.connected:
                    time.sleep(0.1)
            except GlimmrConnectionError as err:
                self.last_update_success = False
                self.logger.info(err)
            except GlimmrError as err:
                self.last_update_success = False
                self.update_listeners()
                self.logger.error(err)

            # Ensure we are disconnected
            await self.glimmr.disconnect()
            if self.unsub:
                self.unsub()
                self.unsub = None

        async def close_websocket(_) -> None:
            """Close WebSocket connection."""
            LOGGER.debug("Socket closed.")
            await self.glimmr.disconnect()

        # Clean disconnect WebSocket on Home Assistant shutdown
        self.unsub = self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, close_websocket
        )

        # Start listening
        asyncio.create_task(listen())

    async def _async_update_data(self) -> SystemData:
        """Fetch data from Glimmr."""
        LOGGER.debug("Updating async")
        try:
            device = await self.glimmr.update()
            self.glimmr.LOGGER = LOGGER
            LOGGER.debug("Done")
        except GlimmrError as error:
            raise UpdateFailed(f"Invalid response from API: {error}") from error

        return device
