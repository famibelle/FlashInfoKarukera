#!/usr/bin/env python3
"""
Copie les MP3 générés depuis /tmp vers docs/audio/TYPE/YYYY-MM/
et réécrit les URLs GitHub Releases dans docs/podcast.xml
en URLs GitHub Pages (même origine → compatible iOS Safari).

Usage:
    python patch_podcast_audio.py flash-info
    python patch_podcast_audio.py horoscope
"""
import re
import shutil
import sys
from pathlib import Path

REPO       = "famibelle/FlashInfoKarukera"
PAGES_BASE = "https://famibelle.github.io/FlashInfoKarukera"
XML_PATH   = Path("docs/podcast.xml")


def year_month_from_filename(name: str) -> str:
    """Extrait YYYY-MM depuis flash-info-YYYYMMDD-*.mp3 ou horoscope-YYYYMMDD-*.mp3."""
    m = re.search(r"-(\d{4})(\d{2})\d{2}-", name)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    from datetime import date
    return date.today().strftime("%Y-%m")


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: patch_podcast_audio.py <flash-info|horoscope>")

    audio_type = sys.argv[1]

    copied: list[tuple[str, str]] = []
    for mp3 in sorted(Path("/tmp").glob(f"{audio_type}-*.mp3")):
        ym   = year_month_from_filename(mp3.name)
        dest = Path(f"docs/audio/{audio_type}/{ym}")
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mp3, dest / mp3.name)
        copied.append((mp3.name, ym))
        print(f"✅  Copié : {mp3.name} → {dest}/")

    if not copied:
        print(f"⚠️  Aucun MP3 {audio_type} trouvé dans /tmp — podcast.xml non modifié")
        return

    if not XML_PATH.exists():
        print("⚠️  docs/podcast.xml introuvable")
        return

    content   = XML_PATH.read_text(encoding="utf-8")
    pages_url = f"{PAGES_BASE}/audio/{audio_type}"

    def rewrite(m: re.Match) -> str:
        tag   = m.group(1)                    # ex: flash-info-2026-05
        fname = m.group(2)                    # ex: flash-info-20260503-midi.mp3
        ym    = tag[len(audio_type) + 1:]     # ex: 2026-05
        return f"{pages_url}/{ym}/{fname}"

    pattern = (
        rf"https://github\.com/{re.escape(REPO)}/releases/download/"
        rf"({re.escape(audio_type)}-[\d-]+)/([^\s\"<]+)"
    )
    new_content = re.sub(pattern, rewrite, content)

    if new_content != content:
        XML_PATH.write_text(new_content, encoding="utf-8")
        print(f"✅  podcast.xml : URLs {audio_type} → GitHub Pages")
    else:
        print(f"ℹ️   podcast.xml : aucune URL {audio_type} à réécrire")


if __name__ == "__main__":
    main()
