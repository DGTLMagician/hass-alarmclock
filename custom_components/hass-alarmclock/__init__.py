"""The Alarm Clock integration."""
from __future__ import annotations
import logging
import voluptuous as vol
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import Platform, CONF_NAME
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    CONF_ALARM_TIME,
    CONF_SNOOZE_DURATION,
    PLATFORMS,
)
from .device import AlarmClockDevice
from .helpers import parse_time_string

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Alarm Clock component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Alarm Clock from a config entry."""
    name = entry.data[CONF_NAME]
    alarm_time = parse_time_string(entry.data[CONF_ALARM_TIME])
    snooze_duration = entry.data.get(CONF_SNOOZE_DURATION, 9)

    # Create device
    device = AlarmClockDevice(
        hass,
        entry.entry_id,
        name,
        alarm_time,
        snooze_duration,
    )
    
    # Store device reference
    hass.data[DOMAIN][entry.entry_id] = {
        "device": device,
    }

    # Set up all platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register services
    async def handle_set_alarm(service_call):
        """Handle the set_alarm service."""
        alarm_time = service_call.data.get("time")
        entity_ids = service_call.data.get("entity_id")
        
        for entity_id in entity_ids:
            entry_id = entity_id.split("_")[2]  # Get entry_id from entity_id
            if entry_id in hass.data[DOMAIN]:
                device = hass.data[DOMAIN][entry_id]["device"]
                await device.async_set_alarm(alarm_time)

    async def handle_snooze(service_call):
        """Handle the snooze service."""
        entity_ids = service_call.data.get("entity_id")
        
        for entity_id in entity_ids:
            entry_id = entity_id.split("_")[2]
            if entry_id in hass.data[DOMAIN]:
                device = hass.data[DOMAIN][entry_id]["device"]
                await device.async_snooze()

    async def handle_stop(service_call):
        """Handle the stop service."""
        entity_ids = service_call.data.get("entity_id")
        
        for entity_id in entity_ids:
            entry_id = entity_id.split("_")[2]
            if entry_id in hass.data[DOMAIN]:
                device = hass.data[DOMAIN][entry_id]["device"]
                await device.async_stop()

    # Register services if not already registered
    if not hass.services.has_service(DOMAIN, "set_alarm"):
        hass.services.async_register(DOMAIN, "set_alarm", handle_set_alarm)
        hass.services.async_register(DOMAIN, "snooze", handle_snooze)
        hass.services.async_register(DOMAIN, "stop", handle_stop)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok