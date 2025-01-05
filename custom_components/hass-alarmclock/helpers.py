"""Helper functions for Alarm Clock integration."""
from datetime import time
import logging
import re
from dateparser.date import DateDataParser
from homeassistant.util import dt as dt_util
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Cache the parser instances per language
_parsers = {}

# Define tokens to skip per language
SKIP_TOKENS = {
    'nl': ['uur'],
    'en': ['hour', 'hours'],
    'de': ['uhr'],
    'fr': ['heure', 'heures'],
    'es': ['hora', 'horas'],
    'it': ['ora', 'ore'],
}

def get_parser(language: str) -> DateDataParser:
    """Get or create a DateDataParser instance for the given language."""
    if language not in _parsers:
        _LOGGER.debug(f"Creating new DateDataParser for language: {language}")
        _parsers[language] = DateDataParser(languages=[language])
    return _parsers[language]

def parse_time_string(time_str: str, hass: HomeAssistant = None) -> time:
    """Parse time string in various formats to time object."""
    time_str = time_str.strip().lower()
    
    _LOGGER.debug(f"Parsing time string: {time_str}")

    try:
        timezone_str = str(dt_util.DEFAULT_TIME_ZONE)
        language = 'en'  # Default to English
        if hass:
            language = hass.config.language
        
        _LOGGER.debug(f"Using timezone: {timezone_str}, language: {language}")

        # Extract numbers from the string
        numbers = re.findall(r'\d+', time_str)
        
        # If we have exactly one number and the string doesn't contain ':'
        # assume it's an hour
        if len(numbers) == 1 and ':' not in time_str:
            hour = int(numbers[0])
            if 0 <= hour <= 23:
                _LOGGER.debug(f"Extracted hour value: {hour}:00")
                return time(hour, 0)

        # Get parser for more complex cases
        parser = get_parser(language)
        
        # Parse the date/time
        date_data = parser.get_date_data(time_str)
        
        if date_data and date_data.date_obj:
            _LOGGER.debug(f"Successfully parsed with DateDataParser: {date_data.date_obj}")
            local_dt = dt_util.as_local(date_data.date_obj)
            
            # If we got a full datetime but the original string only contained an hour,
            # force minutes to 00
            if len(numbers) == 1 and ':' not in time_str:
                local_dt = local_dt.replace(minute=0, second=0, microsecond=0)
                _LOGGER.debug(f"Forcing minutes to 00: {local_dt}")
            
            _LOGGER.debug(f"Final parsed time: {local_dt.time()}")
            return local_dt.time()
        else:
            _LOGGER.debug(f"DateDataParser could not parse string (locale detected: {date_data.locale if date_data else None})")
            
    except Exception as e:
        _LOGGER.debug(f"DateDataParser failed with error: {str(e)}")

    # Fall back to basic format parsing
    try:
        # Try ISO format (HH:MM:SS)
        return time.fromisoformat(time_str)
    except ValueError:
        pass

    # Final fallback for HH:MM format
    try:
        hour, minute = map(int, time_str.split(':'))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour, minute)
    except ValueError:
        pass

    raise ValueError(f"Could not parse time string: {time_str}")