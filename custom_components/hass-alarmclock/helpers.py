from datetime import time, datetime, date, timedelta
import logging
import re
import dateparser
from dateutil import parser as dateutil_parser
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
            'at': 'at',
            'hour': 'hour',
            'morning': 'morning',
            'afternoon': 'afternoon',
            'evening': 'evening',
            'night': 'night'
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
            'at': 'om',
            'hour': 'uur',
            'morning': 'ochtend',
            'afternoon': 'middag',
            'evening': 'avond',
            'night': 'nacht'
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

    def normalize_time_string(self, time_str: str) -> str:
        """Normalize time string by removing language-specific words and noise."""
        # Convert to lowercase and strip whitespace
        text = time_str.lower().strip()
        
        # Remove all known time-related words
        for word in self.lang.time_words.values():
            text = text.replace(word, '').strip()
        
        # Remove multiple spaces
        text = ' '.join(text.split())
        
        # Remove any non-essential characters (keeping numbers, colons, am/pm)
        text = ''.join(c for c in text if c.isdigit() or c in ':apm ')
        
        _LOGGER.debug(f"Normalized '{time_str}' to '{text}'")
        return text.strip()

    def parse_time(self, time_str: str) -> time:
        """Parse time string and return time object."""
        if not time_str:
            raise ValueError("Empty time string")

        # First normalize the string
        cleaned = self.normalize_time_string(time_str)
        _LOGGER.debug(f"Parsing normalized time: {cleaned}")

        # Define patterns from simplest to most complex
        patterns = [
            # Basic patterns
            {
                'pattern': r'^(\d{1,2})$',  # Single number (7)
                'handler': lambda m: time(int(m.group(1)), 0)
            },
            {
                'pattern': r'^(\d{1,2}):(\d{2})$',  # HH:MM (7:30)
                'handler': lambda m: time(int(m.group(1)), int(m.group(2)))
            },
            {
                'pattern': r'^(\d{1,2})(\d{2})$',  # HHMM (730)
                'handler': lambda m: time(int(m.group(1)), int(m.group(2)))
            },
            
            # 12-hour patterns
            {
                'pattern': r'^(\d{1,2})\s*([ap])m?$',  # 7pm
                'handler': lambda m: time(
                    (int(m.group(1)) % 12) + (12 if m.group(2) == 'p' else 0), 
                    0
                )
            },
            {
                'pattern': r'^(\d{1,2}):(\d{2})\s*([ap])m?$',  # 7:30pm
                'handler': lambda m: time(
                    (int(m.group(1)) % 12) + (12 if m.group(2) == 'p' else 0),
                    int(m.group(2))
                )
            }
        ]

        # Try each pattern
        for p in patterns:
            match = re.match(p['pattern'], cleaned)
            if match:
                try:
                    result = p['handler'](match)
                    # Validate the resulting time
                    if 0 <= result.hour <= 23 and 0 <= result.minute <= 59:
                        _LOGGER.debug(f"Successfully parsed time: {result}")
                        return result
                except (ValueError, IndexError) as e:
                    _LOGGER.debug(f"Failed to handle match: {e}")
                    continue

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

        try:
            parsed_date = dateutil_parser.parse(date_str).date()
            return parsed_date
        except ValueError:
            raise ValueError(f"Could not parse date: {date_str}")

    def parse(self, text: str) -> tuple[date, time]:
        """Parse full date/time string."""
        text = text.lower().strip()
        
        # First try to parse as just a time
        try:
            time_obj = self.parse_time(text)
            _LOGGER.debug(f"Successfully parsed as time-only: {time_obj}")
            return dt_util.now().date(), time_obj
        except ValueError as e:
            _LOGGER.debug(f"Not a simple time: {e}")
        
        # Split date and time if present
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
        
        try:
            parsed_date = self.parse_date(date_str)
        except ValueError as e:
            if time_str:
                # If we found a time part but date parsing failed, use today
                parsed_date = self.reference_date
                _LOGGER.debug(f"Using today's date: {parsed_date}")
            else:
                _LOGGER.debug(f"Date parsing failed: {e}")
                raise

        try:
            parsed_time = self.parse_time(time_str if time_str else date_str)
        except ValueError as e:
            _LOGGER.debug(f"Time parsing failed: {e}")
            raise
        
        return parsed_date, parsed_time

def parse_string(text: str, hass: HomeAssistant = None) -> tuple[date, time]:
    """Parse date/time string using system language."""
    language = 'en'
    if hass:
        language = hass.config.language
        
    _LOGGER.debug(f"Parsing string: {text} with language: {language}")
    
    parser = DateTimeParser(language)
    return parser.parse(text)