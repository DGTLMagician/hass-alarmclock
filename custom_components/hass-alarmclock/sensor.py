"""Sensor platform for Alarm Clock."""
from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    NAME_STATUS,
    NAME_COUNTDOWN,
    NAME_SNOOZE_TIME,
    STATE_DORMANT,
)
from .device import AlarmClockDevice

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the alarm clock sensors."""
    device: AlarmClockDevice = hass.data[DOMAIN][entry.entry_id]["device"]
    
    async_add_entities([
        AlarmStatusSensor(device),
        AlarmCountdownSensor(device),
        AlarmSnoozeDurationSensor(device),
    ])

class AlarmStatusSensor(SensorEntity):
    """Sensor for alarm status."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:alarm-panel"

    def __init__(self, device: AlarmClockDevice) -> None:
        """Initialize the sensor."""
        self._device = device
        self._attr_unique_id = f"{device.entry_id}_status"
        self._attr_device_info = device.device_info
        self._attr_name = NAME_STATUS
        device.register_update_callback(self.async_write_ha_state)

    @property
    def native_value(self) -> str:
        """Return the status."""
        return self._device.status

class AlarmCountdownSensor(CoordinatorEntity, SensorEntity):
    """Sensor for countdown until alarm."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "s"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:timer-outline"

    def __init__(self, device: AlarmClockDevice) -> None:
        """Initialize the sensor."""
        super().__init__(device._countdown_coordinator)
        self._device = device
        self._attr_unique_id = f"{device.entry_id}_countdown"
        self._attr_device_info = device.device_info
        self._attr_name = NAME_COUNTDOWN

    @property
    def native_value(self) -> int | None:
        """Return the countdown value in seconds."""
        if not self._device.is_active:
            return None

        data = self.coordinator.data
        if data and "time_left" in data:
            return int(data["time_left"].total_seconds())
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str | int]:
        """Return the state attributes."""
        if not self._device.is_active:
            return {}

        data = self.coordinator.data
        if data and "time_left" in data:
            total_seconds = int(data["time_left"].total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return {
                "hours": hours,
                "minutes": minutes,
                "formatted": f"{hours:02d}:{minutes:02d}"
            }
        return {}

class AlarmSnoozeDurationSensor(SensorEntity):
    """Sensor for snooze duration."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "min"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:sleep"

    def __init__(self, device: AlarmClockDevice) -> None:
        """Initialize the sensor."""
        self._device = device
        self._attr_unique_id = f"{device.entry_id}_snooze_duration"
        self._attr_device_info = device.device_info
        self._attr_name = NAME_SNOOZE_TIME
        device.register_update_callback(self.async_write_ha_state)

    @property
    def native_value(self) -> int:
        """Return the snooze duration in minutes."""
        return int(self._device.snooze_duration.total_seconds() / 60)