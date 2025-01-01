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
from homeassistant.const import CONF_NAME

from .const import (
    DOMAIN,
    STATE_TRIGGERED,
    STATE_SNOOZED,
    STATE_DORMANT,
    DEFAULT_SNOOZE_TIME,
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
        alarm_time: time,
        snooze_duration: int,
    ) -> None:
        """Initialize the alarm clock device."""
        self.hass = hass
        self.entry_id = entry_id
        self.name = name
        self._alarm_time = alarm_time
        self._snooze_duration = timedelta(minutes=snooze_duration)
        
        self._alarm_date = datetime.now().date()
        if datetime.combine(self._alarm_date, self._alarm_time) < datetime.now():
            self._alarm_date = self._alarm_date + timedelta(days=1)
            
        self._is_active = False
        self._status = STATE_DORMANT
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
    def alarm_time(self) -> time:
        """Return the alarm time."""
        return self._alarm_time

    @property
    def alarm_date(self) -> datetime:
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
    def next_alarm(self) -> datetime:
        """Return the next alarm datetime."""
        return datetime.combine(self._alarm_date, self._alarm_time)

    async def async_added_to_hass(self) -> None:
        """Run when device is added."""
        await self._countdown_coordinator.async_config_entry_first_refresh()

    def register_update_callback(self, callback: Callable[[], None]) -> None:
        """Register callback for entity updates."""
        self._update_callbacks.append(callback)

    def _notify_update(self) -> None:
        """Notify all registered callbacks of an update."""
        for callback in self._update_callbacks:
            callback()

    async def _async_countdown_update(self) -> dict[str, Any]:
        """Update countdown timer."""
        now = datetime.now()
        next_alarm = self.next_alarm
        
        if next_alarm < now and self._is_active:
            # Alarm should trigger
            await self._handle_alarm_trigger()
        
        if self._is_active:
            time_left = next_alarm - now
            if time_left.total_seconds() < 0:
                time_left = timedelta(seconds=0)
        else:
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

    async def async_set_alarm(self, alarm_time: str | time) -> None:
        """Set the alarm time."""
        try:
            if isinstance(alarm_time, str):
                alarm_time = parse_time_string(alarm_time)
            
            self._alarm_time = alarm_time
            self._alarm_date = datetime.now().date()
            
            # If alarm time has passed today, set for tomorrow
            if datetime.combine(self._alarm_date, self._alarm_time) < datetime.now():
                self._alarm_date = self._alarm_date + timedelta(days=1)
            
            self._status = STATE_DORMANT
            self._notify_update()
            
        except ValueError as ex:
            raise HomeAssistantError(f"Invalid time format: {ex}")

    async def async_activate(self) -> None:
        """Activate the alarm."""
        self._is_active = True
        self._status = STATE_DORMANT
        self._notify_update()

    async def async_deactivate(self) -> None:
        """Deactivate the alarm."""
        self._is_active = False
        self._status = STATE_DORMANT
        self._notify_update()

    async def async_snooze(self) -> None:
        """Snooze the alarm."""
        if self._status != STATE_TRIGGERED:
            return

        now = datetime.now()
        snooze_until = now + self._snooze_duration
        
        self._alarm_time = snooze_until.time()
        self._alarm_date = snooze_until.date()
        self._status = STATE_SNOOZED
        self._notify_update()

    async def async_stop(self) -> None:
        """Stop the alarm."""
        if self._status not in [STATE_TRIGGERED, STATE_SNOOZED]:
            return
            
        self._status = STATE_DORMANT
        # Move alarm to next day
        self._alarm_date = self._alarm_date + timedelta(days=1)
        self._notify_update()