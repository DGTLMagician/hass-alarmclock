"""The Alarm Clock integration."""
from __future__ import annotations
import logging
import json
import voluptuous as vol
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import Platform, CONF_NAME
from homeassistant.config_entries import ConfigEntry
import homeassistant.helpers.device_registry as dr
import homeassistant.helpers.area_registry as ar
import homeassistant.helpers as ha

from .const import (
    DOMAIN,
    CONF_SNOOZE_DURATION,
    PLATFORMS,
)
from .device import AlarmClockDevice

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Alarm Clock component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Alarm Clock from a config entry."""
    name = entry.data[CONF_NAME]
    snooze_duration = entry.data.get(CONF_SNOOZE_DURATION, 9)

    # Create device
    device = AlarmClockDevice(
        hass,
        entry.entry_id,
        name,
        snooze_duration,
    )
    
    # Store device reference
    hass.data[DOMAIN][entry.entry_id] = {
        "device": device,
    }

    # Set up all platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register services
    async def handle_set_alarm(call):
        """Handle the set_alarm service."""
        _LOGGER.debug(f"Service call data: {json.dumps(call.data, indent=2)}")
        
        time_str = call.data.get("time")
        entity_id = call.data.get("entity_id")
        
        _LOGGER.debug(f"Processing set_alarm: time={time_str}, entity_id={entity_id}")
        
        if entity_id:
            try:
                # Zoek door alle entries voor de juiste device
                found = False
                for entry_id, entry_data in hass.data[DOMAIN].items():
                    device = entry_data["device"]
                    # Check of dit de juiste device is voor deze entity_id
                    if entity_id == f"switch.{device.name.lower()}_{device.name.lower()}":
                        _LOGGER.debug(f"Found matching device with entry_id: {entry_id}")
                        await device.async_set_alarm(time_str)
                        _LOGGER.debug(f"Successfully set alarm for {entity_id}")
                        found = True
                        break
                
                if not found:
                    _LOGGER.error(f"No matching device found for entity {entity_id}")
                    _LOGGER.debug(f"Available devices: {[f'switch.{data['device'].name.lower()}_{data['device'].name.lower()}' for data in hass.data[DOMAIN].values()]}")
            
            except Exception as e:
                _LOGGER.error(f"Failed to set alarm: {e}", exc_info=True)

    async def handle_snooze(call):
        """Handle the snooze service."""
        entity_id = call.data.get("entity_id")
        
        if entity_id:
            try:
                for entry_id, entry_data in hass.data[DOMAIN].items():
                    device = entry_data["device"]
                    if entity_id == f"switch.{device.name.lower()}_{device.name.lower()}":
                        await device.async_snooze()
                        break
                else:
                    _LOGGER.error(f"No matching device found for entity {entity_id}")
            except Exception as e:
                _LOGGER.error(f"Failed to snooze: {e}", exc_info=True)

    async def handle_stop(call):
        """Handle the stop service."""
        entity_id = call.data.get("entity_id")
        
        if entity_id:
            try:
                for entry_id, entry_data in hass.data[DOMAIN].items():
                    device = entry_data["device"]
                    if entity_id == f"switch.{device.name.lower()}_{device.name.lower()}":
                        await device.async_stop()
                        break
                else:
                    _LOGGER.error(f"No matching device found for entity {entity_id}")
            except Exception as e:
                _LOGGER.error(f"Failed to stop: {e}", exc_info=True)

    # Register services if not already registered
    if not hass.services.has_service(DOMAIN, "set_alarm_time"):
        hass.services.async_register(DOMAIN, "set_alarm_time", handle_set_alarm)
        hass.services.async_register(DOMAIN, "snooze", handle_snooze)
        hass.services.async_register(DOMAIN, "stop", handle_stop)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok