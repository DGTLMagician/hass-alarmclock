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
        self._is_active = False
        self._status = STATE_UNSET
        self._remove_alarm_listener = None
        
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
        # Ensure the combined datetime is in the local timezone
        return dt.as_local(datetime.combine(self._alarm_date, self._alarm_time))

    def register_update_callback(self, callback: Callable[[], None]) -> None:
        """Register callback for entity updates."""
        self._update_callbacks.append(callback)

    def _notify_update(self) -> None:
        """Notify all registered callbacks of an update."""
        for callback in self._update_callbacks:
            callback()

    async def _async_countdown_update(self) -> dict[str, timedelta]:
        """Update countdown timer."""
        if not self._is_active or self.next_alarm is None:
            return {"time_left": timedelta(seconds=0)}
        
        now = dt.now()  # This is already timezone-aware
        next_alarm = self.next_alarm
        
        # Ensure next_alarm is timezone-aware by converting if needed
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
ƒ        value = dt.as_local(value)
        try:
            if isinstance(value, str):
                value = parse_time_string(value)
            
            # If we got a datetime, split it into date and time
            if isinstance(value, datetime):
                self._alarm_time = value.time()
                self._alarm_date = value.date()
            else:  # We got a time object
                self._alarm_time = value
                self._alarm_date = dt.now().date()
                
                # If alarm time has passed today, set for tomorrow
                if datetime.combine(self._alarm_date, self._alarm_time) < dt.now():
                    self._alarm_date = self._alarm_date + timedelta(days=1)
            
            # Reset status and ensure active
            self._is_active = True
            self._status = STATE_SET
            self._notify_update()
            
        except ValueError as ex:
            raise HomeAssistantError(f"Invalid time format: {ex}")

    async def async_unset_alarm(self) -> None:
        """Unset the alarm."""
        self._alarm_time = None
        self._alarm_date = None
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

    async def async_snooze(self) -> None:
        """Snooze the alarm."""
        if self._status != STATE_TRIGGERED:
            return

        now = dt.now()
        snooze_until = now + self._snooze_duration
        
        self._alarm_time = snooze_until.time()
        self._alarm_date = snooze_until.date()
        self._status = STATE_SNOOZED
        self._notify_update()

    async def async_stop(self) -> None:
        """Stop the alarm."""
        if self._status not in [STATE_TRIGGERED, STATE_SNOOZED]:
            return
            
        self._alarm_time = None
        self._alarm_date = None
        self._is_active = False
        self._status = STATE_UNSET
        self._notify_update()