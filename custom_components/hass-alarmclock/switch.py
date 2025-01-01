from homeassistant.config_entries import ConfigEntry"""Switch platform for Alarm Clock integration."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_ALARM_TIME,
    SERVICE_SET_ALARM,
    SERVICE_SNOOZE,
    SERVICE_STOP,
)
from .device import AlarmClockDevice

_LOGGER = logging.getLogger(__name__)

# Service schemas
SET_ALARM_SCHEMA = vol.Schema({
    vol.Required(CONF_ALARM_TIME): cv.string,
})

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the alarm clock switch."""
    device = hass.data[DOMAIN][entry.entry_id]["device"]

    entity = AlarmClockSwitch(device)
    async_add_entities([entity])

    # Get platform
    platform = async_get_current_platform()

    # Register services
    platform.async_register_entity_service(
        SERVICE_SET_ALARM,
        SET_ALARM_SCHEMA,
        "async_set_alarm",
    )

    platform.async_register_entity_service(
        SERVICE_SNOOZE,
        {},
        "async_snooze",
    )

    platform.async_register_entity_service(
        SERVICE_STOP,
        {},
        "async_stop",
    )

class AlarmClockSwitch(SwitchEntity):
    """Switch for enabling/disabling the alarm."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:alarm"

    def __init__(self, device: AlarmClockDevice) -> None:
        """Initialize the switch."""
        self._device = device
        self._attr_unique_id = f"{device.entry_id}_switch"
        self._attr_device_info = device.device_info
        device.register_update_callback(self.async_write_ha_state)

    @property
    def name(self) -> str:
        """Return the display name of this switch."""
        return self._device.name

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._device.is_active

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self._device.async_activate()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self._device.async_deactivate()

    async def async_set_alarm(self, **service_data) -> None:
        """Handle set_alarm service."""
        alarm_time = service_data[CONF_ALARM_TIME]
        await self._device.async_set_alarm(alarm_time)

    async def async_snooze(self) -> None:
        """Handle snooze service."""
        await self._device.async_snooze()

    async def async_stop(self) -> None:
        """Handle stop service."""
        await self._device.async_stop()