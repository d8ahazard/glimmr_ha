"""Glimmr integration."""
from glimmr import Glimmr
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .const import DOMAIN, LOGGER

PLATFORMS = {LIGHT_DOMAIN}


async def async_setup(hass: HomeAssistant, config: dict):
    """Old way of setting up the glimmr_light component."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the glimmr_light integration from a config entry."""
    ip_address = entry.data.get(CONF_HOST)
    LOGGER.debug("Creating glimmr from async_setup_entry: %s", ip_address)
    bulb = Glimmr(ip_address)
    await bulb.update()
    hass.data[DOMAIN][entry.unique_id] = bulb

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    # unload glimmr_light bulb
    hass.data[DOMAIN][entry.unique_id] = None
    # Remove config entry
    await hass.config_entries.async_forward_entry_unload(entry, "light")

    return True
