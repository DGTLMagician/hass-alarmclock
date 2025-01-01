"""Switch platform for Alarm Clock integration."""
from __future__ import annotations
import logging
from datetime import datetime, time, timedelta
import voluptuous as vol

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers import event
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_NAME, ATTR_TIME
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    ATTR_ALARM_TIME,
    ATTR_SNOOZE_TIME,
    CONF_ALARM_TIME,
    CONF_SNOOZE_DURATION,
    SERVICE_SET_ALARM,
    SERVICE_SNOOZE,
    SERVICE_STOP,
)
from .helpers import parse_time_string

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Alarm Clock switch from a config entry."""
    name = entry.data[CONF_NAME]
    alarm_time = entry.data[CONF_ALARM_TIME]
    snooze_duration = entry.data.get(CONF_SNOOZE_DURATION, 9)

    async_add_entities(
        [AlarmClockSwitch(hass, entry.entry_id, name, alarm_time, snooze_duration)]
    )

class AlarmClockSwitch(SwitchEntity):
    """Representation of an Alarm Clock switch."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        name: str,
        alarm_time: str,
        snooze_duration: int,
    ) -> None:
        """Initialize the Alarm Clock switch."""
        self.hass = hass
        self.entry_id = entry_id
        self._name = name
        self._state = False
        self._alarm_time = parse_time_string(alarm_time)
        self._snooze_time = timedelta(minutes=snooze_duration)
        self._remove_alarm_listener = None
        self._attr_unique_id = f"alarm_clock_{name}"
        self._attr_should_poll = False

    @property
    def name(self) -> str:
        """Return the display name of this switch."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._state

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ALARM_TIME: self._alarm_time.isoformat(),
            ATTR_SNOOZE_TIME: str(self._snooze_time),
        }

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        self._state = True
        await self._setup_alarm()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        self._state = False
        if self._remove_alarm_listener:
            self._remove_alarm_listener()
            self._remove_alarm_listener = None
        self.async_write_ha_state()

    async def _setup_alarm(self) -> None:
        """Set up the alarm listener."""
        if self._remove_alarm_listener:
            self._remove_alarm_listener()

        now = datetime.now()
        alarm_dt = datetime.combine(now.date(), self._alarm_time)

        # If alarm time has passed, schedule for next day
        if alarm_dt < now:
            alarm_dt = alarm_dt + timedelta(days=1)

        @callback
        async def alarm_triggered(now) -> None:
            """Handler for alarm trigger."""
            self._state = False
            self.async_write_ha_state()
            # Fire alarm_triggered event with the alarm ID
            self.hass.bus.async_fire(
                f"{DOMAIN}_triggered",
                {"alarm_id": self._attr_unique_id}
            )

        self._remove_alarm_listener = event.async_track_point_in_time(
            self.hass, alarm_triggered, alarm_dt
        )

    async def async_set_alarm(self, alarm_time: str) -> None:
        """Set the alarm time."""
        try:
            self._alarm_time = parse_time_string(alarm_time)
            if self._state:
                await self._setup_alarm()
            self.async_write_ha_state()
        except ValueError as ex:
            _LOGGER.error("Invalid time format: %s", ex)

    async def async_snooze(self) -> None:
        """Snooze the alarm."""
        if not self._state:
            return

        now = datetime.now()
        snooze_time = now + self._snooze_time
        await self.async_set_alarm(snooze_time.time().isoformat())