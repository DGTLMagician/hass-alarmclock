"""Alarm Clock device coordination."""
from __future__ import annotations

import logging
from datetime import datetime, time, timedelta
from typing import Any, Callable

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers import event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt

from .const import (
    DOMAIN,
    STATE_SET,
    STATE_UNSET,
    STATE_TRIGGERED,
    STATE_SNOOZED,
)
from .helpers import parse_time_string

_LOGGER = logging.getLogger(__name__)

class AlarmClockDevice:
    """Representation of an Alarm Clock device."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        name: str,
        snooze_duration: int,
    ) -> None:
        """Initialize the alarm clock device."""
        self.hass = hass
        self.entry_id = entry_id
        self.name = name
        self._snooze_duration = timedelta(minutes=snooze_duration)
        
        self._alarm_time = None
        self._alarm_date = None
        self._original_alarm_time = None  # Store original alarm time for reset after snooze
        self._original_alarm_date = None  # Store original alarm date for reset after snooze
        self._is_active = False
        self._status = STATE_UNSET
        self._remove_alarm_listener = None
        self._snooze_end_time = None  # Track when snooze will end
        
        # Store callbacks for entity updates
        self._update_callbacks: list[Callable[[], None]] = []
        
        # Setup countdown timer
        self._countdown_coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"{name} Countdown",
            update_method=self._async_countdown_update,
            update_interval=timedelta(seconds=1),
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry_id)},
            name=self.name,
            manufacturer="DGTLMagician",
            model="Alarm Clock",
            sw_version="1.0.0",
        )

    @property
    def is_active(self) -> bool:
        """Return if the alarm is active."""
        return self._is_active

    @property
    def alarm_time(self) -> time | None:
        """Return the alarm time."""
        return self._alarm_time

    @property
    def alarm_date(self) -> datetime | None:
        """Return the alarm date."""
        return self._alarm_date

    @property
    def status(self) -> str:
        """Return the alarm status."""
        return self._status

    @property
    def snooze_duration(self) -> timedelta:
        """Return the snooze duration."""
        return self._snooze_duration

    @property
    def next_alarm(self) -> datetime | None:
        """Return the next alarm datetime."""
        if self._alarm_time is None or self._alarm_date is None:
            return None
        return dt.as_local(datetime.combine(self._alarm_date, self._alarm_time))

    @property
    def snooze_end_time(self) -> datetime | None:
        """Return when the current snooze will end."""
        return self._snooze_end_time if self._status == STATE_SNOOZED else None

    def register_update_callback(self, callback: Callable[[], None]) -> None:
        """Register callback for entity updates."""
        self._update_callbacks.append(callback)

    def _notify_update(self) -> None:
        """Notify all registered callbacks of an update."""
        for callback in self._update_callbacks:
            callback()

    def _ensure_future_time(self, alarm_datetime: datetime) -> datetime:
        """Ensure the alarm time is in the future by at least 1 minute."""
        now = dt.now()
        min_future_time = now + timedelta(minutes=1)
        
        if alarm_datetime <= now:
            # Only add a day if the time is in the past
            while alarm_datetime <= now:
                alarm_datetime += timedelta(days=1)
        
        return alarm_datetime

    async def _async_countdown_update(self) -> dict[str, timedelta]:
        """Update countdown timer."""
        if not self._is_active or self.next_alarm is None:
            return {"time_left": timedelta(seconds=0)}
        
        now = dt.now()
        next_alarm = self.next_alarm
        
        # Ensure next_alarm is timezone-aware
        if next_alarm.tzinfo is None:
            next_alarm = dt.as_local(next_alarm)
        
        time_left = next_alarm - now
        
        if time_left.total_seconds() <= 0:
            await self._handle_alarm_trigger()
            time_left = timedelta(seconds=0)
            
        return {"time_left": time_left}

    async def _handle_alarm_trigger(self) -> None:
        """Handle alarm trigger."""
        self._status = STATE_TRIGGERED
        self._notify_update()
        
        # Fire alarm_triggered event
        self.hass.bus.async_fire(
            f"{DOMAIN}_triggered",
            {"alarm_id": f"alarm_clock_{self.name.lower().replace(' ', '_')}"}
        )

    async def async_set_alarm(self, value: datetime | time | str) -> None:
        """Set the alarm time and date."""
        try:
            # Convert string to time if needed
            if isinstance(value, str):
                value = parse_time_string(value)
            
            # Convert time to datetime if needed
            if isinstance(value, time):
                now = dt.now()
                value = datetime.combine(now.date(), value)
            
            # Ensure alarm is at least 1 minute in the future
            alarm_datetime = self._ensure_future_time(dt.as_local(value))
            
            # Store original alarm time and date
            self._original_alarm_time = alarm_datetime.time()
            self._original_alarm_date = alarm_datetime.date()
            
            # Set current alarm time and date
            self._alarm_time = self._original_alarm_time
            self._alarm_date = self._original_alarm_date
            
            # Reset snooze end time
            self._snooze_end_time = None
            
            # Activate alarm
            self._is_active = True
            self._status = STATE_SET
            self._notify_update()
            
        except ValueError as ex:
            raise HomeAssistantError(f"Invalid time format: {ex}")

    async def async_snooze(self) -> None:
        """Snooze the alarm."""
        if self._status != STATE_TRIGGERED:
            return

        now = dt.now()
        snooze_until = now + self._snooze_duration
        
        # Set the next alarm time
        self._alarm_time = snooze_until.time()
        self._alarm_date = snooze_until.date()
        self._snooze_end_time = snooze_until
        self._status = STATE_SNOOZED
        self._notify_update()

    async def async_stop(self) -> None:
        """Stop the alarm."""
        if self._status not in [STATE_TRIGGERED, STATE_SNOOZED]:
            return
            
        # Reset to original alarm time if it exists
        if self._original_alarm_time and self._original_alarm_date:
            self._alarm_time = self._original_alarm_time
            self._alarm_date = self._original_alarm_date
            self._status = STATE_SET
            self._is_active = True
        else:
            self._alarm_time = None
            self._alarm_date = None
            self._is_active = False
            self._status = STATE_UNSET
            
        # Reset snooze-related properties
        self._snooze_end_time = None
        self._notify_update()

    async def async_unset_alarm(self) -> None:
        """Unset the alarm."""
        self._alarm_time = None
        self._alarm_date = None
        self._original_alarm_time = None
        self._original_alarm_date = None
        self._snooze_end_time = None
        self._is_active = False
        self._status = STATE_UNSET
        self._notify_update()

    async def async_activate(self) -> None:
        """Activate the alarm."""
        if self._alarm_time is None:
            return
        self._is_active = True
        self._status = STATE_SET
        self._notify_update()

    async def async_deactivate(self) -> None:
        """Deactivate the alarm."""
        self._is_active = False
        self._status = STATE_UNSET
        self._notify_update()
