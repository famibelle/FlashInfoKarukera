"""
Configuration settings for FlashInfo Karukera API.
Uses pydantic-settings for type-safe environment variables.
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional, List


class Settings(BaseSettings):
    # ---- Chemins (modifiables via .env) ----
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent

    # Chemins publics (OK)
    ARCHIVES_DIR: Path = PROJECT_ROOT / "archives" / "horoscope"
    DOCS_DIR: Path = PROJECT_ROOT / "docs"
    PODCAST_XML_PATH: Path = DOCS_DIR / "podcast.xml"
    DATA_DIR: Path = PROJECT_ROOT / "data"

    # Clés API (via .env uniquement)
    MISTRAL_API_KEY: Optional[str] = None

    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    # Buzzsprout
    BUZZSPROUT_API_TOKEN: Optional[str] = None
    BUZZSPROUT_PODCAST_ID: Optional[str] = None

    # Backblaze B2
    B2_KEY_ID: Optional[str] = None
    B2_APPLICATION_KEY: Optional[str] = None
    B2_BUCKET_NAME: Optional[str] = None
    B2_ENDPOINT: Optional[str] = "https://s3.us-west-004.backblazeb2.com"

    # GitHub
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_REPO: str = "famibelle/FlashInfoKarukera"

    # Sécurité
    API_KEY: Optional[str] = None  # Pour protéger les endpoints de publication
    CORS_ORIGINS: List[str] = ["*"]

    # Paramètres LLM
    DEFAULT_LLM_MODEL: str = "mistral-tiny-latest"
    DEFAULT_LLM_TEMPERATURE: float = 0.7
    MAX_TOKENS_TITLE: int = 150

    # Zodiaque (données publiques)
    ZODIAC_SYMBOLS: dict = {
        "Belier": "\u2648", "Taureau": "\u2649", "Gemeaux": "\u264A", "Cancer": "\u264B",
        "Lion": "\u264C", "Vierge": "\u264D", "Balance": "\u264E", "Scorpion": "\u264F",
        "Sagittaire": "\u2650", "Capricorne": "\u2651", "Verseau": "\u2652", "Poissons": "\u2653"
    }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore les variables non définies dans le modèle


settings = Settings()
