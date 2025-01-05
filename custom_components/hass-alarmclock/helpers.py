"""Helper functions for Alarm Clock integration."""
from datetime import time
import logging
from dateparser import parse
from homeassistant.util import dt as dt_util
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

def parse_time_string(time_str: str, hass: HomeAssistant = None) -> time:
    """Parse time string in various formats to time object.
    
    Uses dateparser with the system language from Home Assistant.
    Falls back to basic parsing for standard formats.
    
    Args:
        time_str: Time string in any format (natural language or standard)
        hass: HomeAssistant instance for language detection
        
    Returns:
        time object
    """
    # Remove any whitespace
    time_str = time_str.strip()
    
    _LOGGER.debug(f"Parsing time string: {time_str}")

    try:
        # Get timezone string from Home Assistant
        timezone_str = str(dt_util.DEFAULT_TIME_ZONE)
        
        # Get language from Home Assistant
        language = None
        if hass:
            language = hass.config.language
        
        _LOGGER.debug(f"Using timezone: {timezone_str}, language: {language}")

        # Prepare dateparser settings
        settings = {
            'RETURN_AS_TIMEZONE_AWARE': True,
            'TIMEZONE': timezone_str,
            'PREFER_DATES_FROM': 'current_period',
            'DATE_ORDER': 'DMY',
            'PREFER_DAY_OF_MONTH': 'current',
            'STRICT_PARSING': False
        }
        
        # Add language if available
        if language:
            settings['LANGUAGES'] = [language]
            
        # Use dateparser with settings
        parsed_dt = parse(
            time_str,
            settings=settings
        )
        
        if parsed_dt:
            _LOGGER.debug(f"Successfully parsed with dateparser: {parsed_dt}")
            # Convert to local time if needed
            local_dt = dt_util.as_local(parsed_dt)
            _LOGGER.debug(f"Converted to local time: {local_dt}")
            return local_dt.time()
        else:
            _LOGGER.debug("Dateparser returned None")
            
    except Exception as e:
        _LOGGER.debug(f"Dateparser failed with error: {str(e)}")

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