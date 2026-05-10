"""Date utilities."""
from datetime import date

# French month names
MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]


def format_horoscope_date_edition(target_date: date, edition: str) -> str:
    """Format date and edition for horoscope title."""
    day = target_date.day
    month = MONTHS_FR[target_date.month - 1]
    return f"ce {edition} du {day} {month}"
