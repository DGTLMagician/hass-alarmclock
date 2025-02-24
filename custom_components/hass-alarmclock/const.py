"""Constants for the Alarm Clock integration."""
from datetime import timedelta
from homeassistant.const import Platform

# Domain
DOMAIN = "alarm_clock"

# Configuration and Services
CONF_SNOOZE_DURATION = "snooze_duration"
CONF_ALARM_TIME = "time"

# Attributes
ATTR_ALARM_TIME = "alarm_time"
ATTR_SNOOZE_TIME = "snooze_time"
DEFAULT_SNOOZE_TIME = timedelta(minutes=9)

# Entity names
NAME_ALARM_TIME = "Time"
NAME_COUNTDOWN = "Countdown"
NAME_STATUS = "Status"
NAME_SNOOZE_TIMER = "Snooze Timer"
NAME_SNOOZE_BUTTON = "Snooze Button"

# States
STATE_SET = "set"
STATE_UNSET = "unset"
STATE_TRIGGERED = "triggered"
STATE_SNOOZED = "snoozed"

# Services
SERVICE_SET_ALARM = "set_alarm"
SERVICE_SNOOZE = "snooze"
SERVICE_STOP = "stop"

# Platforms
PLATFORMS = ["switch", "sensor", "datetime", "button"]