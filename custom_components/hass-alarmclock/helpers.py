"""Helper functions for Alarm Clock integration."""
from datetime import time
import re

def parse_time_string(time_str: str) -> time:
    """Parse time string in various formats to time object.
    
    Accepts:
    - HH:MM:SS
    - HH:MM
    - H:MM
    - HMM
    - HHMM
    """
    # Remove any whitespace
    time_str = time_str.strip()
    
    # Try to parse standard format first
    try:
        return time.fromisoformat(time_str)
    except ValueError:
        pass
    
    # Try to parse HH:MM format
    match = re.match(r'^(\d{1,2}):(\d{2})$', time_str)
    if match:
        hour, minute = map(int, match.groups())
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour, minute)
    
    # Try to parse HHMM format
    match = re.match(r'^(\d{2})(\d{2})$', time_str)
    if match:
        hour, minute = map(int, match.groups())
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour, minute)
    
    # Try to parse HMM format
    match = re.match(r'^(\d{1})(\d{2})$', time_str)
    if match:
        hour, minute = map(int, match.groups())
        if 0 <= hour <= 9 and 0 <= minute <= 59:
            return time(hour, minute)
    
    raise ValueError(f"Invalid time format: {time_str}")