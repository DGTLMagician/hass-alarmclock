"""Constants for the Alarm Clock integration."""
from datetime import timedelta

# Domain
DOMAIN = "alarm_clock"

# Configuration
CONF_ALARM_TIME = "alarm_time"
CONF_SNOOZE_DURATION = "snooze_duration"

# Attributes
ATTR_ALARM_TIME = "alarm_time"
ATTR_SNOOZE_TIME = "snooze_time"
DEFAULT_SNOOZE_TIME = timedelta(minutes=9)
DEFAULT_ALARM_TIME = "07:00:00"

# Entity names
NAME_ALARM_ACTIVE = "Active"
NAME_ALARM_DATE = "Date"
NAME_ALARM_TIME = "Time"
NAME_SNOOZE_TIME = "Snooze Duration"
NAME_COUNTDOWN = "Countdown"
NAME_STATUS = "Status"
NAME_IS_SET = "Is Set"

# States
STATE_TRIGGERED = "triggered"
STATE_SNOOZED = "snoozed"
STATE_DORMANT = "dormant"

# Services
SERVICE_SET_ALARM = "set_alarm"
SERVICE_SNOOZE = "snooze"
SERVICE_STOP = "stop"

# Platforms
PLATFORMS = ["switch", "sensor", "binary_sensor", "datetime"]