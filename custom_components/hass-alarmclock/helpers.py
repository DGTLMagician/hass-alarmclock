"""Helper functions for Alarm Clock integration."""
from datetime import time
import logging
from dateparser import parse
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

def parse_time_string(time_str: str) -> time:
    """Parse time string in various formats to time object.
    
    Uses dateparser for natural language processing in multiple languages.
    Falls back to basic parsing for standard formats.
    
    Args:
        time_str: Time string in any format (natural language or standard)
        
    Returns:
        time object
    """
    # Remove any whitespace
    time_str = time_str.strip()
    
    _LOGGER.debug(f"Parsing time string: {time_str}")

    try:
        # Get timezone string from Home Assistant
        timezone_str = str(dt_util.DEFAULT_TIME_ZONE)
        _LOGGER.debug(f"Using timezone: {timezone_str}")

        # Use dateparser with Home Assistant timezone
        parsed_dt = parse(
            time_str,
            settings={
                'RETURN_AS_TIMEZONE_AWARE': True,
                'TIMEZONE': timezone_str,
                'PREFER_DATES_FROM': 'current_period',
                'DATE_ORDER': 'DMY'
            }
        )
        
        if parsed_dt:
            _LOGGER.debug(f"Parsed with dateparser: {parsed_dt}")
            # Convert to local time if needed
            local_dt = dt_util.as_local(parsed_dt)
            return local_dt.time()
            
    except Exception as e:
        _LOGGER.debug(f"Dateparser failed: {e}")

    # Fall back to basic format parsing
    try:
        # Try ISO format (HH:MM:SS)
        return time.fromisoformat(time_str)
    except ValueError:
        pass

    # Final fallback for basic HH:MM format
    try:
        hour, minute = map(int, time_str.split(':'))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour, minute)
    except ValueError:
        pass

    raise ValueError(f"Could not parse time string: {time_str}")