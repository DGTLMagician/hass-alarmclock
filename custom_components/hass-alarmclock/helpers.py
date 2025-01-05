"""Helper functions for Alarm Clock integration."""
from datetime import time, datetime, date, timedelta
import logging
import re
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

class Language:
    """Language specific parsing configuration."""
    def __init__(self, 
                 name: str,
                 weekdays: list[str],
                 months: list[str],
                 relative_words: dict[str, str],
                 time_words: dict[str, str]):
        self.name = name
        self.weekdays = weekdays
        self.months = months
        self.relative_words = relative_words
        self.time_words = time_words

# Define supported languages
LANGUAGES = {
    'en': Language(
        name='English',
        weekdays=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
        months=['january', 'february', 'march', 'april', 'may', 'june', 'july', 
                'august', 'september', 'october', 'november', 'december'],
        relative_words={
            'next': 'next',
            'last': 'last',
            'in': 'in',
            'day': 'day',
            'days': 'days',
            'week': 'week',
            'weeks': 'weeks',
            'today': 'today',
            'tomorrow': 'tomorrow',
            'on': 'on'
        },
        time_words={
            'am': 'am',
            'pm': 'pm',
            'noon': 'noon',
            'midnight': 'midnight',
            'at': 'at'
        }
    ),
    'nl': Language(
        name='Dutch',
        weekdays=['maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag', 'zondag'],
        months=['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli',
                'augustus', 'september', 'oktober', 'november', 'december'],
        relative_words={
            'next': 'volgende',
            'last': 'vorige|afgelopen',
            'in': 'over',
            'day': 'dag',
            'days': 'dagen',
            'week': 'week',
            'weeks': 'weken',
            'today': 'vandaag',
            'tomorrow': 'morgen',
            'on': 'op'
        },
        time_words={
            'am': 'vm',
            'pm': 'nm',
            'noon': 'middag',
            'midnight': 'middernacht',
            'at': 'om'
        }
    )
}

class DateTimeParser:
    """Parser for date and time strings."""
    def __init__(self, language: str = 'en'):
        """Initialize the parser with language."""
        if language not in LANGUAGES:
            _LOGGER.warning(f"Unsupported language: {language}, falling back to English")
            language = 'en'
            
        self.lang = LANGUAGES[language]
        self.reference_date = dt_util.now().date()

    def parse_time(self, time_str: str) -> time:
        """Parse time string and return time object."""
        time_str = time_str.lower().strip()

        # Time patterns
        patterns = {
            # 24-hour format (13:45, 09:30)
            r'(\d{1,2}):(\d{2})(?!\s*[ap]m)': self._parse_24h_time,
            # 12-hour format (1:45pm, 9:30am)
            r'(\d{1,2}):(\d{2})\s*(am|pm)': self._parse_12h_time,
            # Simple 12-hour (3pm, 11am)
            r'(\d{1,2})\s*(am|pm)': self._parse_simple_12h,
            # Simple hour only (15, 09, 9)
            r'^(\d{1,2})(?:\s+|$)': self._parse_simple_24h,
            self.lang.time_words['noon']: lambda _: (12, 0),
            self.lang.time_words['midnight']: lambda _: (0, 0),
        }
        
        for pattern, parser in patterns.items():
            match = re.match(f'^{pattern}$', time_str)
            if match:
                hour, minute = parser(match)
                return time(hour, minute)

        raise ValueError(f"Could not parse time: {time_str}")

    def parse_date(self, date_str: str) -> date:
        """Parse date string and return date object."""
        date_str = date_str.lower().strip()

        # Check for relative dates
        if date_str == self.lang.relative_words['today']:
            return self.reference_date
        if date_str == self.lang.relative_words['tomorrow']:
            return self.reference_date + timedelta(days=1)

        # Check for "in X days/weeks"
        in_pattern = f"{self.lang.relative_words['in']}\\s+(\\d+)\\s+({self.lang.relative_words['days']}|{self.lang.relative_words['weeks']})"
        match = re.match(in_pattern, date_str)
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            if unit == self.lang.relative_words['weeks']:
                amount *= 7
            return self.reference_date + timedelta(days=amount)

        # Check for next weekday
        for i, day in enumerate(self.lang.weekdays):
            if date_str == day or date_str == f"{self.lang.relative_words['next']} {day}":
                days_ahead = (i - self.reference_date.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                return self.reference_date + timedelta(days=days_ahead)

        # Check for specific date (e.g., "5 january")
        for i, month in enumerate(self.lang.months, 1):
            pattern = f"(\\d{{1,2}})\\s+{month}"
            match = re.match(pattern, date_str)
            if match:
                day = int(match.group(1))
                year = self.reference_date.year
                try:
                    result = date(year, i, day)
                    # If the date is in the past, use next year
                    if result < self.reference_date:
                        result = date(year + 1, i, day)
                    return result
                except ValueError as e:
                    raise ValueError(f"Invalid date: {e}")

        raise ValueError(f"Could not parse date: {date_str}")

    def parse(self, text: str) -> tuple[date, time]:
        """Parse full date/time string."""
        text = text.lower().strip()
        
        # First try to parse as just a time
        try:
            time_obj = self.parse_time(text)
            _LOGGER.debug(f"Parsed as time only: {time_obj}")
            return self.reference_date, time_obj
        except ValueError:
            pass
        
        # If that fails, try to split date and time
        date_str = text
        time_str = None
        
        at_word = self.lang.time_words['at']
        on_word = self.lang.relative_words['on']
        
        # Try to extract time part
        if f" {at_word} " in text:
            parts = text.split(f" {at_word} ")
            if len(parts) == 2:
                date_str, time_str = parts
        
        # Clean up date string if it starts with 'on'
        if date_str.startswith(f"{on_word} "):
            date_str = date_str[len(f"{on_word} "):]
        
        _LOGGER.debug(f"Parsing date: '{date_str}' and time: '{time_str}'")
        
        # Parse date and time
        try:
            parsed_date = self.parse_date(date_str)
        except ValueError:
            # If no valid date found and we have a time, use today
            if time_str:
                parsed_date = self.reference_date
            else:
                raise
        
        parsed_time = self.parse_time(time_str) if time_str else time(0, 0)
        
        return parsed_date, parsed_time
    
    def _parse_24h_time(self, match) -> tuple[int, int]:
        hour = int(match.group(1))
        minute = int(match.group(2))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError(f"Invalid time: {hour}:{minute}")
        return hour, minute

    def _parse_12h_time(self, match) -> tuple[int, int]:
        hour = int(match.group(1))
        minute = int(match.group(2))
        meridiem = match.group(3)
        
        if hour > 12 or minute > 59:
            raise ValueError(f"Invalid time: {hour}:{minute} {meridiem}")
            
        if meridiem == self.lang.time_words['pm'] and hour != 12:
            hour += 12
        elif meridiem == self.lang.time_words['am'] and hour == 12:
            hour = 0
            
        return hour, minute

    def _parse_simple_12h(self, match) -> tuple[int, int]:
        hour = int(match.group(1))
        meridiem = match.group(2)
        
        if hour > 12:
            raise ValueError(f"Invalid hour: {hour}")
            
        if meridiem == self.lang.time_words['pm'] and hour != 12:
            hour += 12
        elif meridiem == self.lang.time_words['am'] and hour == 12:
            hour = 0
            
        return hour, 0

    def _parse_simple_24h(self, match) -> tuple[int, int]:
        hour = int(match.group(1))
        if not 0 <= hour <= 23:
            raise ValueError(f"Invalid hour: {hour}")
        return hour, 0

def parse_string(text: str, hass: HomeAssistant = None) -> tuple[date, time]:
    """Parse date/time string using system language."""
    language = 'en'
    if hass:
        language = hass.config.language
        
    _LOGGER.debug(f"Parsing string: {text} with language: {language}")
    
    parser = DateTimeParser(language)
    return parser.parse(text)
