"""Button platform for Alarm Clock integration."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, NAME_SNOOZE_BUTTON, STATE_TRIGGERED
from .device import AlarmClockDevice

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the alarm clock button."""
    device = hass.data[DOMAIN][entry.entry_id]["device"]
    async_add_entities([SnoozeButton(device)])

class SnoozeButton(ButtonEntity):
    """Button to snooze the alarm."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:snooze"

    def __init__(self, device: AlarmClockDevice) -> None:
        """Initialize the button."""
        self._device = device
        self._attr_unique_id = f"{device.entry_id}_snooze_button"
        self._attr_device_info = device.device_info
        self._attr_name = NAME_SNOOZE_BUTTON
        device.register_update_callback(self.async_write_ha_state)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._device.status == STATE_TRIGGERED

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._device.async_snooze()