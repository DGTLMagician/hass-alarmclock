"""Switch platform for Alarm Clock integration."""
from __future__ import annotations

import logging
from datetime import datetime, time, timedelta
import voluptuous as vol

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.config_entries import ConfigEntry
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_NAME, ATTR_TIME
from homeassistant.helpers import entity_platform

from .const import (
    DOMAIN,
    CONF_ALARM_TIME,
    CONF_SNOOZE_DURATION,
    SERVICE_SET_ALARM,
    SERVICE_SNOOZE,
    SERVICE_STOP,
    ATTR_ALARM_TIME,
    ATTR_SNOOZE_TIME,
)
from .device import AlarmClockDevice
from .helpers import parse_time_string

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
    """Representation of an Alarm Clock switch."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:alarm"
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, device: AlarmClockDevice) -> None:
        """Initialize the switch."""
        self._device = device
        self._attr_unique_id = f"{device.entry_id}_switch"
        self._attr_device_info = device.device_info
        self._attr_available = True
        device.register_update_callback(self.async_write_ha_state)

    @property
    def name(self) -> str:
        """Return the display name of this switch."""
        return self._device.name

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._device.is_active

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._attr_available

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        attrs = {
            ATTR_SNOOZE_TIME: str(self._device.snooze_duration),
        }
        if self._device.alarm_time:
            attrs[ATTR_ALARM_TIME] = self._device.alarm_time.isoformat()
        return attrs

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self._device.async_activate()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self._device.async_deactivate()
        self.async_write_ha_state()

    async def async_set_alarm(self, **service_data) -> None:
        """Handle set_alarm service."""
        alarm_time = service_data[CONF_ALARM_TIME]
        await self._device.async_set_alarm(alarm_time)
        self.async_write_ha_state()

    async def async_snooze(self) -> None:
        """Handle snooze service."""
        await self._device.async_snooze()
        self.async_write_ha_state()

    async def async_stop(self) -> None:
        """Handle stop service."""
        await self._device.async_stop()
        self.async_write_ha_state()