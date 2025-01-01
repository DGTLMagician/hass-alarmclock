"""DateTime platform for Alarm Clock integration."""
from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt

from .const import DOMAIN, NAME_ALARM_TIME
from .device import AlarmClockDevice

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the alarm clock datetime entities."""
    device: AlarmClockDevice = hass.data[DOMAIN][entry.entry_id]["device"]
    async_add_entities([AlarmTimeEntity(device)])

class AlarmTimeEntity(DateTimeEntity):
    """DateTime entity for alarm time."""

    _attr_has_entity_name = True
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
        """Return the alarm time and date."""
        # Use actual alarm time or midnight as default
        alarm_time = self._device.alarm_time or time(0, 0)
        alarm_date = self._device.alarm_date or dt.now().date()
        
        return dt.now().replace(
            year=alarm_date.year,
            month=alarm_date.month,
            day=alarm_date.day,
            hour=alarm_time.hour,
            minute=alarm_time.minute,
            second=alarm_time.second,
            microsecond=0
        )

    async def async_set_value(self, value: datetime) -> None:
        """Set the alarm time and date."""
        await self._device.async_set_alarm(value)