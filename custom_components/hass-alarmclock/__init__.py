"""The Alarm Clock integration."""
from __future__ import annotations
import logging
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
        time_str = call.data.get("time")
        targets = call.get("target", {})
        entity_ids = targets.get("entity_id", [])
        device_ids = targets.get("device_id", [])
        area_ids = targets.get("area_id", [])
        
        _LOGGER.debug(f"Setting alarm with time {time_str} for targets: {targets}")

        target_entity_ids = []

        # Handle entity targets
        target_entity_ids.extend(entity_ids)
        
        # Handle device targets
        for device_id in device_ids:
            device = dr.async_get(hass).async_get(device_id)
            if device:
                for entity_id in device.entity_id:
                    if entity_id.startswith("datetime"):
                        target_entity_ids.append(entity_id)

        # Handle area targets
        for area_id in area_ids:
            area = ar.async_get(hass).async_get(area_id)
            if area:
                entities_in_area = ha.helpers.entity_registry.async_entries_for_area(
                    hass.data["entity_registry"], area.id
                )
                for entity in entities_in_area:
                    if entity.entity_id.startswith("datetime"):
                        target_entity_ids.append(entity.entity_id)
        
        for datetime_entity_id in target_entity_ids:
            # Convert datetime entity ID to entry_id
            # datetime.alarm_name_time -> alarm_name
            try:
                entry_id = datetime_entity_id.split(".")[1].replace("_time", "")
            except IndexError:
                _LOGGER.warning(f"Invalid entity ID format: {datetime_entity_id}")
                continue # Skip to the next entity if the format is invalid

            if entry_id in hass.data[DOMAIN]:
                device = hass.data[DOMAIN][entry_id]["device"]
                try:
                    # Set the alarm time
                    await device.async_set_alarm(time_str)
                    _LOGGER.debug(f"Successfully set alarm for {datetime_entity_id}")
                except Exception as e:
                    _LOGGER.error(f"Failed to set alarm: {e}")

    async def handle_snooze(call):
        """Handle the snooze service."""
        entity_ids = call.data.get("target", {}).get("entity_id", [])
        
        for entity_id in entity_ids:
            entry_id = entity_id.split("_")[2]
            if entry_id in hass.data[DOMAIN]:
                device = hass.data[DOMAIN][entry_id]["device"]
                await device.async_snooze()

    async def handle_stop(call):
        """Handle the stop service."""
        entity_ids = call.data.get("target", {}).get("entity_id", [])
        
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