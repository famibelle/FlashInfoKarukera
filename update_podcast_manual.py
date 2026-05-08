#!/usr/bin/env python3
"""
Script pour mettre à jour manuellement podcast.xml avec les fichiers audio existants.
Utilise GitHub Pages comme URL pour les épisodes.
"""
import re
from pathlib import Path
from datetime import datetime

# Constants
PAGES_BASE = "https://famibelle.github.io/FlashInfoKarukera"
PODCAST_RSS_PATH = Path(__file__).parent / "docs" / "podcast.xml"
AUDIO_DIR = Path(__file__).parent / "docs" / "audio"

def _rfc2822(dt: datetime) -> str:
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")

def _update_podcast_rss(
    rss_path: Path,
    channel_title: str,
    channel_desc: str,
    episode_title: str,
    episode_desc: str,
    audio_url: str,
    audio_size: int,
    duration_s: float,
    guid: str,
    pub_date: datetime,
) -> None:
    """Insère un épisode en tête du flux RSS podcast (iTunes-compatible)."""
    def _xe(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    existing: list[str] = []
    if rss_path.exists():
        existing = re.findall(r"<item>.*?</item>", rss_path.read_text(encoding="utf-8"), re.DOTALL)

    mins, secs = divmod(int(duration_s), 60)
    new_item = (
        f"    <item>\n"
        f"      <title>{_xe(episode_title)}</title>\n"
        f"      <description><![CDATA[{episode_desc}]]></description>\n"
        f"      <pubDate>{_rfc2822(pub_date)}</pubDate>\n"
        f"      <enclosure url=\"{audio_url}\" length=\"{audio_size}\" type=\"audio/mpeg\"/>\n"
        f"      <guid isPermaLink=\"false\">{guid}</guid>\n"
        f"      <itunes:duration>{mins:02d}:{secs:02d}</itunes:duration>\n"
        f"    </item>"
    )
    artwork = "https://famibelle.github.io/FlashInfoKarukera/artwork.jpg"
    items_block = "\n\n".join([new_item] + existing[:199])
    rss_path.parent.mkdir(parents=True, exist_ok=True)
    rss_path.write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">\n'
        f'  <channel>\n'
        f'    <title>{_xe(channel_title)}</title>\n'
        f'    <link>https://famibelle.github.io/FlashInfoKarukera/</link>\n'
        f'    <description>{_xe(channel_desc)}</description>\n'
        f'    <language>fr</language>\n'
        f'    <copyright>© Botiran</copyright>\n'
        f'    <itunes:author>Botiran</itunes:author>\n'
        f'    <itunes:owner><itunes:name>Botiran</itunes:name><itunes:email>medhi.famibelle@outlook.fr</itunes:email></itunes:owner>\n'
        f'    <itunes:image href="{artwork}"/>\n'
        f'    <image><url>{artwork}</url><title>{_xe(channel_title)}</title><link>https://famibelle.github.io/FlashInfoKarukera/</link></image>\n'
        f'    <itunes:category text="News"><itunes:category text="Daily News"/></itunes:category>\n'
        f'    <itunes:explicit>no</itunes:explicit>\n\n'
        f'{items_block}\n\n'
        f'  </channel>\n'
        f'</rss>\n',
        encoding="utf-8",
    )
    print(f"   📻 RSS mis à jour → {rss_path.name} ({len(existing) + 1} épisodes)")


def get_file_date(filename: str) -> tuple[str, str]:
    """Extrait la date et l'édition/moment depuis le nom de fichier."""
    # Flash Info
    fi_match = re.match(r'flash-info-(\d{4})(\d{2})(\d{2})-(matin|midi|soir)', filename)
    if fi_match:
        year, month, day = fi_match.groups()[:3]
        edition = fi_match.group(4)
        return f"{year}{month}{day}", edition
    
    # Horoscope
    ho_match = re.match(r'horoscope-(\d{4})(\d{2})(\d{2})-(matin|midi|soir)', filename)
    if ho_match:
        year, month, day = ho_match.groups()[:3]
        moment = ho_match.group(4)
        return f"{year}{month}{day}", moment
    
    # Émission culturelle
    em_match = re.match(r'emission-(\d{4})-(\d{2})-(\d{2})', filename)
    if em_match:
        year, month, day = em_match.groups()
        return f"{year}{month}{day}", "culturelle"
    
    return None, None


def _is_in_podcast(filename: str) -> bool:
    """Vérifie si un fichier est déjà référencé dans podcast.xml."""
    if not PODCAST_RSS_PATH.exists():
        return False
    content = PODCAST_RSS_PATH.read_text(encoding="utf-8")
    return filename in content


def _estimate_duration(mp3_file: Path) -> float:
    """Estime la durée à partir de la taille du fichier (approximation)."""
    size_mb = mp3_file.stat().st_size / (1024 * 1024)
    duration_min = size_mb / 1.5
    return duration_min * 60


def update_flash_info_podcast():
    """Met à jour podcast.xml avec les Flash Info manquants."""
    flash_dir = AUDIO_DIR / "flash-info"
    if not flash_dir.exists():
        print(f"⚠️  {flash_dir} n'existe pas")
        return
    
    for month_dir in sorted(flash_dir.iterdir()):
        if not month_dir.is_dir():
            continue
        for mp3_file in sorted(month_dir.glob("*.mp3")):
            filename = mp3_file.name
            date_str, edition = get_file_date(filename)
            if not date_str or not edition:
                continue
            if _is_in_podcast(filename):
                print(f"✅ {filename} déjà dans podcast.xml")
                continue
            
            date_obj = datetime.strptime(date_str, "%Y%m%d")
            title = f"Flash Info Guadeloupe — {date_obj.strftime('%A %d %B %Y')}, édition du {edition}"
            description = f"Flash info Guadeloupe du {date_obj.strftime('%d %B %Y')} — édition du {edition}"
            audio_url = f"{PAGES_BASE}/audio/flash-info/{date_obj.strftime('%Y-%m')}/{filename}"
            audio_size = mp3_file.stat().st_size
            duration_s = _estimate_duration(mp3_file)
            guid = mp3_file.stem
            
            _update_podcast_rss(
                rss_path=PODCAST_RSS_PATH,
                channel_title="Karukera — Flash Info & Horoscope",
                channel_desc="Flash info et horoscope de la Guadeloupe — matin, midi et soir par Botiran",
                episode_title=title,
                episode_desc=description,
                audio_url=audio_url,
                audio_size=audio_size,
                duration_s=duration_s,
                guid=guid,
                pub_date=datetime.utcnow(),
            )
            print(f"✅ Ajouté : {filename}")


def update_horoscope_podcast():
    """Met à jour podcast.xml avec les Horoscopes manquants."""
    horoscope_dir = AUDIO_DIR / "horoscope"
    if not horoscope_dir.exists():
        print(f"⚠️  {horoscope_dir} n'existe pas")
        return
    
    for month_dir in sorted(horoscope_dir.iterdir()):
        if not month_dir.is_dir():
            continue
        for mp3_file in sorted(month_dir.glob("*.mp3")):
            filename = mp3_file.name
            date_str, moment = get_file_date(filename)
            if not date_str or not moment:
                continue
            if _is_in_podcast(filename):
                print(f"✅ {filename} déjà dans podcast.xml")
                continue
            
            date_obj = datetime.strptime(date_str, "%Y%m%d")
            day_name = date_obj.strftime('%A')
            title = f"Horoscope {moment} — {day_name} {date_obj.strftime('%d %B %Y')}"
            description = f"Horoscope du {day_name} {date_obj.strftime('%d %B %Y')} — {moment}"
            audio_url = f"{PAGES_BASE}/audio/horoscope/{date_obj.strftime('%Y-%m')}/{filename}"
            audio_size = mp3_file.stat().st_size
            duration_s = _estimate_duration(mp3_file)
            guid = mp3_file.stem
            
            _update_podcast_rss(
                rss_path=PODCAST_RSS_PATH,
                channel_title="Karukera — Flash Info & Horoscope",
                channel_desc="Flash info et horoscope de la Guadeloupe — matin, midi et soir par Botiran",
                episode_title=title,
                episode_desc=description,
                audio_url=audio_url,
                audio_size=audio_size,
                duration_s=duration_s,
                guid=guid,
                pub_date=datetime.utcnow(),
            )
            print(f"✅ Ajouté : {filename}")


def update_emission_podcast():
    """Met à jour podcast.xml avec les Émissions culturelles manquantes."""
    emission_dir = AUDIO_DIR / "Emissions"
    if not emission_dir.exists():
        print(f"⚠️  {emission_dir} n'existe pas")
        return
    
    for mp3_file in sorted(emission_dir.glob("*.mp3")):
        filename = mp3_file.name
        date_str, _ = get_file_date(filename)
        if not date_str:
            continue
        if _is_in_podcast(filename):
            print(f"✅ {filename} déjà dans podcast.xml")
            continue
        
        date_obj = datetime.strptime(date_str.replace('-', ''), "%Y%m%d")
        title = f"Émission culturelle — {date_obj.strftime('%Y-%m-%d')}"
        description = "Émission culturelle quotidienne sur les symboles, l'histoire et la nature de la Guadeloupe."
        audio_url = f"{PAGES_BASE}/audio/Emissions/{filename}"
        audio_size = mp3_file.stat().st_size
        duration_s = _estimate_duration(mp3_file)
        guid = mp3_file.stem
        
        _update_podcast_rss(
            rss_path=PODCAST_RSS_PATH,
            channel_title="Karukera — Flash Info & Horoscope",
            channel_desc="Flash info et horoscope de la Guadeloupe — matin, midi et soir par Botiran",
            episode_title=title,
            episode_desc=description,
            audio_url=audio_url,
            audio_size=audio_size,
            duration_s=duration_s,
            guid=guid,
            pub_date=datetime.utcnow(),
        )
        print(f"✅ Ajouté : {filename}")


def main():
    print("🎙️  Mise à jour manuelle de podcast.xml")
    print("=" * 60)
    
    print("\n📰 Mise à jour Flash Info...")
    update_flash_info_podcast()
    
    print("\n✨ Mise à jour Horoscope...")
    update_horoscope_podcast()
    
    print("\n🌺 Mise à jour Émissions culturelles...")
    update_emission_podcast()
    
    print("\n" + "=" * 60)
    print("✅ Mise à jour terminée !")


if __name__ == "__main__":
    main()
