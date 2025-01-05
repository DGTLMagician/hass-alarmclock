"""Helper functions for Alarm Clock integration."""
from datetime import time
import logging
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
    # Add more languages as needed
}

def get_parser(language: str) -> DateDataParser:
    """Get or create a DateDataParser instance for the given language."""
    if language not in _parsers:
        _LOGGER.debug(f"Creating new DateDataParser for language: {language}")
        _parsers[language] = DateDataParser(languages=[language])
    return _parsers[language]

def parse_time_string(time_str: str, hass: HomeAssistant = None) -> time:
    """Parse time string in various formats to time object."""
    time_str = time_str.strip()
    
    _LOGGER.debug(f"Parsing time string: {time_str}")

    try:
        timezone_str = str(dt_util.DEFAULT_TIME_ZONE)
        language = 'en'  # Default to English
        if hass:
            language = hass.config.language
        
        _LOGGER.debug(f"Using timezone: {timezone_str}, language: {language}")

        # Get parser for this language
        parser = get_parser(language)
        
        # Get tokens to skip for this language
        tokens_to_skip = SKIP_TOKENS.get(language, [])
        _LOGGER.debug(f"Skipping tokens for language {language}: {tokens_to_skip}")
        
        # Add settings for the parser
        settings = {
            'PREFER_LANGUAGE_DATE_ORDER': True,
            'PREFER_DAY_OF_MONTH': 'current',
            'PREFER_DATES_FROM': 'current_period',
            'REQUIRE_PARTS': ['hour'],
            'SKIP_TOKENS': tokens_to_skip,
            'NORMALIZE': True,
        }
        
        # Parse the date/time
        date_data = parser.get_date_data(time_str, settings=settings)
        
        if date_data and date_data.date_obj:
            _LOGGER.debug(f"Successfully parsed with DateDataParser: {date_data.date_obj}")
            local_dt = dt_util.as_local(date_data.date_obj)
            _LOGGER.debug(f"Converted to local time: {local_dt}")
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

    # Final fallback for basic HH:MM format
    try:
        hour, minute = map(int, time_str.split(':'))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour, minute)
    except ValueError:
        pass

    raise ValueError(f"Could not parse time string: {time_str}")