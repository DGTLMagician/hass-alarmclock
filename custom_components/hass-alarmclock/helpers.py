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
        language = 'en'  # Default to English
        if hass:
            language = hass.config.language

        _LOGGER.debug(f"Using language: {language}")

        # Try direct HH:MM parsing first
        try:
            hour, minute = map(int, time_str.split(':'))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return time(hour, minute)
        except ValueError:
            pass

        # Use DateDataParser for more complex cases
        parser = get_parser(language)
        date_data = parser.get_date_data(time_str)

        if date_data and date_data.date_obj:
            _LOGGER.debug(f"Successfully parsed with DateDataParser: {date_data.date_obj}")
            local_dt = dt_util.as_local(date_data.date_obj)
            return local_dt.time()
        else:
            _LOGGER.debug(f"DateDataParser could not parse string (locale detected: {date_data.locale if date_data else None})")

        # Handle single number as hour after DateDataParser failed
        numbers = re.findall(r'\d+', time_str)
        if len(numbers) == 1:
            hour = int(numbers[0])
            if 0 <= hour <= 23:
                return time(hour, 0)
            else:
                raise ValueError(f"Invalid hour value: {hour}")

    except ValueError as ve:
        _LOGGER.debug(f"ValueError during parsing: {ve}")
        raise  # Re-raise the ValueError
    except Exception as e:
        _LOGGER.exception(f"Exception during parsing: {e}")
        raise ValueError(f"Could not parse time string: {time_str}")

    raise ValueError(f"Could not parse time string: {time_str}")