"""Zodiac utilities."""

ZODIAC_SIGNS = [
    {"name_fr": "Bélier", "name_en": "Aries", "symbol": "♈", "start": (3, 21), "end": (4, 19)},
    {"name_fr": "Taureau", "name_en": "Taurus", "symbol": "♉", "start": (4, 20), "end": (5, 20)},
    {"name_fr": "Gémeaux", "name_en": "Gemini", "symbol": "♊", "start": (5, 21), "end": (6, 20)},
    {"name_fr": "Cancer", "name_en": "Cancer", "symbol": "♋", "start": (6, 21), "end": (7, 22)},
    {"name_fr": "Lion", "name_en": "Leo", "symbol": "♌", "start": (7, 23), "end": (8, 22)},
    {"name_fr": "Vierge", "name_en": "Virgo", "symbol": "♍", "start": (8, 23), "end": (9, 22)},
    {"name_fr": "Balance", "name_en": "Libra", "symbol": "♎", "start": (9, 23), "end": (10, 22)},
    {"name_fr": "Scorpion", "name_en": "Scorpio", "symbol": "♏", "start": (10, 23), "end": (11, 21)},
    {"name_fr": "Sagittaire", "name_en": "Sagittarius", "symbol": "♐", "start": (11, 22), "end": (12, 21)},
    {"name_fr": "Capricorne", "name_en": "Capricorn", "symbol": "♑", "start": (12, 22), "end": (1, 19)},
    {"name_fr": "Verseau", "name_en": "Aquarius", "symbol": "♒", "start": (1, 20), "end": (2, 18)},
    {"name_fr": "Poissons", "name_en": "Pisces", "symbol": "♓", "start": (2, 19), "end": (3, 20)},
]

ZODIAC_SYMBOLS = {
    "Bélier": "♈", "Taureau": "♉", "Gémeaux": "♊", "Cancer": "♋",
    "Lion": "♌", "Vierge": "♍", "Balance": "♎", "Scorpion": "♏",
    "Sagittaire": "♐", "Capricorne": "♑", "Verseau": "♒", "Poissons": "♓"
}


def resolve_sign(name: str) -> str:
    """Resolve sign name to standard French name."""
    for sign in ZODIAC_SIGNS:
        if name.lower() in [sign["name_fr"].lower(), sign["name_en"].lower()]:
            return sign["name_fr"]
    return name


def sign_for_date(date) -> str:
    """Get zodiac sign for a given date."""
    month, day = date.month, date.day
    for sign in ZODIAC_SIGNS:
        start_month, start_day = sign["start"]
        end_month, end_day = sign["end"]
        
        # Handle year wrap (Capricorn, Aquarius, Pisces)
        if start_month > end_month:
            # Sign spans year end
            if (month == start_month and day >= start_day) or (month == end_month and day <= end_day):
                return sign["name_en"]
            if month > start_month or month < end_month:
                return sign["name_en"]
        else:
            if (month == start_month and day >= start_day) or (month == end_month and day <= end_day):
                return sign["name_en"]
            if month > start_month and month < end_month:
                return sign["name_en"]
    return "Aries"


def get_sign_fr(sign_en: str) -> str:
    """Get French name from English name."""
    for sign in ZODIAC_SIGNS:
        if sign["name_en"].lower() == sign_en.lower():
            return sign["name_fr"]
    return sign_en
