"""Config flow for Alarm Clock integration."""
from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_SNOOZE_DURATION

_LOGGER = logging.getLogger(__name__)

class AlarmClockConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Alarm Clock."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Create unique ID from name
            await self.async_set_unique_id(
                f"alarm_clock_{user_input[CONF_NAME].lower().replace(' ', '_')}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): str,
                    vol.Optional(CONF_SNOOZE_DURATION, default=9): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=60)
                    ),
                }
            ),
            errors=errors,
        )