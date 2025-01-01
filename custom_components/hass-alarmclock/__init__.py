"""The Alarm Clock integration."""
from __future__ import annotations
import logging
import voluptuous as vol
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import Platform, CONF_NAME
from homeassistant.config_entries import ConfigEntry

DOMAIN = "alarm_clock"
_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SWITCH]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Alarm Clock component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Alarm Clock from a config entry."""
    hass.data[DOMAIN][entry.entry_id] = {}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok