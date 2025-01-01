"""Binary sensor platform for Alarm Clock."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, NAME_ALARM_ACTIVE, NAME_IS_SET
from .device import AlarmClockDevice

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the alarm clock binary sensors."""
    device: AlarmClockDevice = hass.data[DOMAIN][entry.entry_id]["device"]
    
    async_add_entities([
        AlarmActiveSwitch(device),
        AlarmSetSensor(device),
    ])

class AlarmActiveSwitch(BinarySensorEntity):
    """Binary sensor for alarm active state."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_icon = "mdi:alarm"

    def __init__(self, device: AlarmClockDevice) -> None:
        """Initialize the sensor."""
        self._device = device
        self._attr_unique_id = f"{device.entry_id}_active"
        self._attr_device_info = device.device_info
        self._attr_name = NAME_ALARM_ACTIVE
        device.register_update_callback(self.async_write_ha_state)

    @property
    def is_on(self) -> bool:
        """Return if alarm is active."""
        return self._device.is_active

class AlarmSetSensor(BinarySensorEntity):
    """Binary sensor indicating if an alarm is set."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_icon = "mdi:alarm-check"

    def __init__(self, device: AlarmClockDevice) -> None:
        """Initialize the sensor."""
        self._device = device
        self._attr_unique_id = f"{device.entry_id}_is_set"
        self._attr_device_info = device.device_info
        self._attr_name = NAME_IS_SET
        device.register_update_callback(self.async_write_ha_state)

    @property
    def is_on(self) -> bool:
        """Return if alarm is set."""
        return bool(self._device.next_alarm > datetime.now() if self._device.is_active else False)