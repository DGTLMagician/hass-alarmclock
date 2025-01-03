"""Sensor platform for Alarm Clock integration."""
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
from homeassistant.util import dt

from .const import (
    DOMAIN,
    NAME_STATUS,
    NAME_COUNTDOWN,
    NAME_SNOOZE_TIMER,
    STATE_UNSET,
    STATE_SNOOZED,
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
        SnoozeTimerSensor(device),
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

class SnoozeTimerSensor(CoordinatorEntity, SensorEntity):
    """Sensor for snooze countdown."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "s"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:timer-snooze"

    def __init__(self, device: AlarmClockDevice) -> None:
        """Initialize the sensor."""
        super().__init__(device._countdown_coordinator)
        self._device = device
        self._attr_unique_id = f"{device.entry_id}_snooze_timer"
        self._attr_device_info = device.device_info
        self._attr_name = NAME_SNOOZE_TIMER

    @property
    def native_value(self) -> int | None:
        """Return the snooze countdown value in seconds."""
        if self._device.status != STATE_SNOOZED:
            return None

        snooze_end = self._device.snooze_end_time
        if not snooze_end:
            return None

        time_left = snooze_end - dt.now()
        return max(0, int(time_left.total_seconds()))

    @property
    def extra_state_attributes(self) -> dict[str, str | int]:
        """Return the state attributes."""
        if self._device.status != STATE_SNOOZED:
            return {}

        value = self.native_value
        if value is not None:
            minutes = value // 60
            seconds = value % 60
            return {
                "minutes": minutes,
                "seconds": seconds,
                "formatted": f"{minutes:02d}:{seconds:02d}"
            }
        return {}