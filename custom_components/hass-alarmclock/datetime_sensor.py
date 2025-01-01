"""DateTime platform for Alarm Clock."""
from __future__ import annotations

from datetime import datetime, time

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, NAME_ALARM_TIME, NAME_ALARM_DATE
from .device import AlarmClockDevice

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the alarm clock datetime entities."""
    device: AlarmClockDevice = hass.data[DOMAIN][entry.entry_id]["device"]
    
    async_add_entities([
        AlarmTimeEntity(device),
        AlarmDateEntity(device),
    ])

class AlarmTimeEntity(DateTimeEntity):
    """DateTime entity for alarm time."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:calendar-clock"
    _attr_icon = "mdi:clock-time-four-outline"

    def __init__(self, device: AlarmClockDevice) -> None:
        """Initialize the entity."""
        self._device = device
        self._attr_unique_id = f"{device.entry_id}_time"
        self._attr_device_info = device.device_info
        self._attr_name = NAME_ALARM_TIME
        device.register_update_callback(self.async_write_ha_state)

    @property
    def native_value(self) -> datetime:
        """Return the alarm time."""
        return datetime.combine(
            datetime.now().date(),
            self._device.alarm_time
        )

    async def async_set_value(self, value: datetime) -> None:
        """Set the alarm time."""
        await self._device.async_set_alarm(value.time())

class AlarmDateEntity(DateTimeEntity):
    """DateTime entity for alarm date."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, device: AlarmClockDevice) -> None:
        """Initialize the entity."""
        self._device = device
        self._attr_unique_id = f"{device.entry_id}_date"
        self._attr_device_info = device.device_info
        self._attr_name = NAME_ALARM_DATE
        device.register_update_callback(self.async_write_ha_state)

    @property
    def native_value(self) -> datetime:
        """Return the alarm date."""
        return datetime.combine(
            self._device.alarm_date,
            time(0, 0)
        )

    async def async_set_value(self, value: datetime) -> None:
        """Set the alarm date."""
        self._device._alarm_date = value.date()
        self._device._notify_update()