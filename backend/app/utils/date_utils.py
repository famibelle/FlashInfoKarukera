"""Date utilities."""
from datetime import date


def format_horoscope_date_edition(target_date: date, edition: str) -> str:
    """Format date and edition for horoscope title."""
    day = target_date.day
    month = target_date.strftime("%B").lower()
    return f"ce {edition} du {day} {month}"
