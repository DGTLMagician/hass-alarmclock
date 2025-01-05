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
                 relative_words: dict[str, str | list[str]],
                 time_words: dict[str, str | list[str]],
                 prepositions: list[str]):
        self.name = name
        self.weekdays = weekdays
        self.months = months
        self.relative_words = relative_words
        self.time_words = time_words
        self.prepositions = prepositions

# Define supported languages
LANGUAGES = {
    'en': Language(
        name='English',
        weekdays=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
        months=['january', 'february', 'march', 'april', 'may', 'june', 'july', 
                'august', 'september', 'october', 'november', 'december'],
        relative_words={
            'today': 'today',
            'tomorrow': 'tomorrow',
            'days_offset': {  # Map words to number of days
                'day after tomorrow': 2,
                'in 2 days': 2,
                'in two days': 2,
            },
            'in': ['in', 'after'],
            'days': ['day', 'days'],
            'number_words': {  # For parsing written numbers
                'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
            }
        },
        time_words={
            'at': 'at',
            'hour': ['hour', 'hours'],
            'minute': ['minute', 'minutes'],
            'morning': 'morning',
            'afternoon': 'afternoon',
            'evening': 'evening',
            'night': 'night'
        },
        prepositions=['for', 'on', 'at', 'in']
    ),
    'nl': Language(
        name='Dutch',
        weekdays=['maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag', 'zondag'],
        months=['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli',
                'augustus', 'september', 'oktober', 'november', 'december'],
        relative_words={
            'today': 'vandaag',
            'tomorrow': 'morgen',
            'days_offset': {
                'overmorgen': 2,
                'over 2 dagen': 2,
                'over twee dagen': 2,
            },
            'in': ['over', 'na'],
            'days': ['dag', 'dagen'],
            'number_words': {
                'een': 1, 'twee': 2, 'drie': 3, 'vier': 4, 'vijf': 5,
                'zes': 6, 'zeven': 7, 'acht': 8, 'negen': 9, 'tien': 10
            }
        },
        time_words={
            'at': 'om',
            'hour': ['uur', 'uren'],
            'minute': ['minuut', 'minuten'],
            'morning': 'ochtend',
            'afternoon': 'middag',
            'evening': 'avond',
            'night': 'nacht'
        },
        prepositions=['voor', 'op', 'om', 'in']
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

    def normalize_date_string(self, date_str: str) -> tuple[str, str]:
        """Normalize date string and extract time part."""
        text = date_str.lower().strip()
        
        # Extract time part if present
        time_part = None
        date_part = text
        
        # Look for time indicators
        at_word = self.lang.time_words['at']
        hour_words = self.lang.time_words['hour']
        
        # Convert to list if not already
        at_patterns = [at_word] if isinstance(at_word, str) else at_word
        hour_patterns = [hour_words] if isinstance(hour_words, str) else hour_words
        
        # First try with explicit 'at' word
        for pattern in at_patterns:
            if f" {pattern} " in text:
                parts = text.split(f" {pattern} ")
                date_part = parts[0]
                if len(parts) > 1:
                    time_part = parts[1]
                    break
        
        # If no explicit 'at', look for time with hour words
        if not time_part:
            for hour_word in hour_patterns:
                match = re.search(rf'(\d+(?:[:\.]\d+)?)\s*{hour_word}', text)
                if match:
                    time_part = match.group(0)
                    date_part = text.replace(time_part, '').strip()
                    break
        
        # Clean up date part by removing prepositions
        for prep in self.lang.prepositions:
            date_part = re.sub(rf'\b{prep}\b', ' ', date_part)
        
        # Remove multiple spaces
        date_part = ' '.join(date_part.split())
        return date_part.strip(), time_part

    def normalize_time_string(self, time_str: str) -> str:
        """Normalize time string by removing language-specific words."""
        text = time_str.lower().strip()
        
        # Remove all time-related words
        for word_list in self.lang.time_words.values():
            if isinstance(word_list, list):
                for word in word_list:
                    text = text.replace(word, '').strip()
            else:
                text = text.replace(word_list, '').strip()
        
        # Remove multiple spaces
        text = ' '.join(text.split())
        
        # Keep only relevant characters
        text = ''.join(c for c in text if c.isdigit() or c in ':apm ')
        
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

    def parse_relative_date(self, text: str) -> date | None:
        """Parse relative date expressions using language configuration."""
        # Check direct matches (today, tomorrow)
        if text == self.lang.relative_words['today']:
            return self.reference_date
        if text == self.lang.relative_words['tomorrow']:
            return self.reference_date + timedelta(days=1)
        
        # Check predefined offsets
        for expr, days in self.lang.relative_words.get('days_offset', {}).items():
            if expr in text:
                return self.reference_date + timedelta(days=days)
        
        # Parse "in X days" pattern using both numeric and word numbers
        number_words = self.lang.relative_words.get('number_words', {})
        in_words = self.lang.relative_words['in']
        day_words = self.lang.relative_words['days']
        
        if isinstance(in_words, str):
            in_words = [in_words]
        if isinstance(day_words, str):
            day_words = [day_words]
        
        for in_word in in_words:
            for day_word in day_words:
                # Try numeric pattern
                pattern = fr'{in_word}\s+(\d+)\s+{day_word}'
                match = re.search(pattern, text)
                if match:
                    days = int(match.group(1))
                    return self.reference_date + timedelta(days=days)
                
                # Try word pattern
                pattern = fr'{in_word}\s+(\w+)\s+{day_word}'
                match = re.search(pattern, text)
                if match and match.group(1) in number_words:
                    days = number_words[match.group(1)]
                    return self.reference_date + timedelta(days=days)
        
        return None

    def parse_date(self, date_str: str) -> date:
        """Parse date string and return date object."""
        date_str = date_str.lower().strip()
        
        # First try relative date parsing
        relative_date = self.parse_relative_date(date_str)
        if relative_date:
            return relative_date
        
        # Check for specific date (e.g., "5 january" or "january 5")
        for i, month in enumerate(self.lang.months, 1):
            # Pattern for both "5 january" and "january 5"
            patterns = [
                fr"(\d{{1,2}})\s+{month}",
                fr"{month}\s+(\d{{1,2}})"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, date_str)
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
        
        # Check for numeric date (8-1 or 8/1 or 8-01 etc)
        patterns = [
            r'(\d{1,2})[-/\s](\d{1,2})(?:[-/\s](\d{2,4}))?',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, date_str)
            if match:
                day = int(match.group(1))
                month = int(match.group(2))
                year = int(match.group(3)) if match.group(3) else self.reference_date.year
                if year < 100:
                    year += 2000
                try:
                    result = date(year, month, day)
                    if result < self.reference_date:
                        result = date(year + 1, month, day)
                    return result
                except ValueError:
                    continue
        
        raise ValueError(f"Could not parse date: {date_str}")

    def parse(self, text: str) -> tuple[date, time]:
        """Parse full date/time string."""
        text = text.lower().strip()
        
        # Split into date and time components
        date_str, time_str = self.normalize_date_string(text)
        
        # First try to parse the date part
        try:
            date_obj = self.parse_date(date_str)
        except ValueError:
            # If parsing as date fails, try parsing the entire string as just a time
            try:
                time_obj = self.parse_time(text)
                return self._get_appropriate_date(time_obj), time_obj
            except ValueError:
                # If that fails too, re-raise the original date parsing error
                raise ValueError(f"Could not parse date: {text}")
        
        # Parse the time part if present, otherwise use default
        try:
            if time_str:
                time_obj = self.parse_time(time_str)
            else:
                # If no time specified but we have a relative date, use current time
                if date_obj > self.reference_date:
                    time_obj = dt_util.now().time()
                else:
                    time_obj = time(0, 0)  # Default to midnight
        except ValueError as e:
            _LOGGER.debug(f"Time parsing failed: {e}")
            time_obj = time(0, 0)  # Default to midnight
        
        return date_obj, time_obj

    def _get_appropriate_date(self, time_obj: time) -> date:
        """Get appropriate date based on the time (today or tomorrow)."""
        now = dt_util.now()
        date_obj = now.date()
        
        # If the time is earlier than now, use tomorrow
        if time_obj.hour < now.hour or (time_obj.hour == now.hour and time_obj.minute <= now.minute):
            date_obj += timedelta(days=1)
        
        return date_obj

def parse_string(text: str, hass: HomeAssistant = None) -> tuple[date, time]:
    """Parse date/time string using system language."""
    language = 'en'
    if hass:
        language = hass.config.language
        
    _LOGGER.debug(f"Parsing string: {text} with language: {language}")
    
    parser = DateTimeParser(language)
    return parser.parse(text)