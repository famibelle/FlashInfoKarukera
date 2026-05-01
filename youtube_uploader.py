#!/usr/bin/env python3
"""
YouTube Uploader — Flash Info Karukera
Parse le RSS, télécharge l'épisode courant, convertit en MP4 (ffmpeg),
uploade sur YouTube (non listé) et retourne le videoId.
Cache les uploads pour éviter les doublons.
"""

import os
import re
import json
import logging
import subprocess
import tempfile
import requests
from pathlib import Path
from xml.etree import ElementTree as ET
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

RSS_URL              = "https://famibelle.github.io/FlashInfoKarukera/podcast.xml"
ARTWORK_URL          = "https://famibelle.github.io/FlashInfoKarukera/artwork.jpg"
CACHE_FILE           = Path("playlists/youtube_cache.json")
PLAYLIST_ID_FILE     = Path("playlists/youtube_playlist_id.txt")

YOUTUBE_TOKEN_PATH = Path(os.getenv("YOUTUBE_TOKEN_PATH", "youtube_token.json"))
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

MODE_EDITION = {"morning": "matin", "midday": "midi", "evening": "soir"}
# Horoscopes n'ont pas d'édition midi — on utilise matin comme fallback
HOROSCOPE_EDITION = {"morning": "matin", "midday": "matin", "evening": "soir"}


# ── Auth ──────────────────────────────────────────────────────────────────────

def get_youtube_client():
    if not YOUTUBE_TOKEN_PATH.exists():
        raise FileNotFoundError(
            f"Token introuvable : {YOUTUBE_TOKEN_PATH}\n"
            "Lance : python3 youtube_setup.py"
        )
    creds = Credentials.from_authorized_user_file(str(YOUTUBE_TOKEN_PATH), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        YOUTUBE_TOKEN_PATH.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


# ── Cache ─────────────────────────────────────────────────────────────────────

def load_cache() -> dict:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict):
    CACHE_FILE.parent.mkdir(exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


# ── RSS ───────────────────────────────────────────────────────────────────────

def _fetch_rss_items() -> list:
    """Récupère et parse le RSS. Retourne la liste des items."""
    resp = requests.get(RSS_URL, timeout=15)
    resp.raise_for_status()
    # Escape bare & non entity (ex: "Flash Info & Horoscope")
    xml_text = re.sub(r'&(?![a-zA-Z#]\w*;)', '&amp;', resp.text)
    root = ET.fromstring(xml_text)
    return root.findall(".//item")


def _item_to_episode(item) -> dict | None:
    """Extrait les métadonnées d'un item RSS. Retourne None si pas d'enclosure."""
    ns = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}
    enclosure = item.find("enclosure")
    if enclosure is None:
        return None
    title_el   = item.find("title")
    pub_date_el = item.find("pubDate")
    duration_el = item.find("itunes:duration", ns)
    return {
        "title":    (title_el.text or "")    if title_el    is not None else "",
        "url":      enclosure.get("url", ""),
        "pub_date": (pub_date_el.text or "") if pub_date_el is not None else "",
        "duration": (duration_el.text or "") if duration_el is not None else "",
    }


def get_latest_episode(mode: str) -> dict | None:
    """Retourne le dernier Flash Info correspondant au mode (matin/midi/soir)."""
    edition = MODE_EDITION.get(mode, "")
    try:
        for item in _fetch_rss_items():
            ep = _item_to_episode(item)
            if ep is None:
                continue
            if "Flash Info" not in ep["title"]:
                continue
            if edition and edition not in ep["title"].lower():
                continue
            return ep
    except Exception as e:
        logger.warning(f"Erreur RSS (flash info) : {e}")
    return None


def get_latest_horoscope(mode: str) -> dict | None:
    """Retourne le dernier Horoscope correspondant au mode.
    Midi utilise l'édition matin (pas d'horoscope midi dans le RSS)."""
    edition = HOROSCOPE_EDITION.get(mode, "matin")
    try:
        for item in _fetch_rss_items():
            ep = _item_to_episode(item)
            if ep is None:
                continue
            if "horoscope" not in ep["title"].lower():
                continue
            if edition and edition not in ep["title"].lower():
                continue
            return ep
    except Exception as e:
        logger.warning(f"Erreur RSS (horoscope) : {e}")
    return None


# ── Conversion + Upload ───────────────────────────────────────────────────────

def _mp3_to_mp4(mp3: Path, artwork: Path, output: Path):
    """Combine MP3 + image fixe en MP4 via ffmpeg."""
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(artwork),
        "-i", str(mp3),
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(output),
    ], check=True, capture_output=True)


def _upload(yt, mp4: Path, title: str, tags: list) -> str:
    """Upload le MP4 sur YouTube (non listé). Retourne le videoId."""
    body = {
        "snippet": {
            "title": title,
            "description": (
                "Flash Info Karukera par Botiran\n"
                "https://famibelle.github.io/FlashInfoKarukera/"
            ),
            "tags": tags,
            "categoryId": "25",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(str(mp4), mimetype="video/mp4", resumable=True)
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.info(f"  Upload : {int(status.progress() * 100)}%")

    video_id = response["id"]
    logger.info(f"  Vidéo : https://youtu.be/{video_id}")
    return video_id


def _get_or_upload(episode: dict, label: str, tags: list) -> str:
    """Logique commune : cache → download → convert → upload."""
    cache = load_cache()
    key = episode["url"]

    if key in cache:
        logger.info(f"{label} déjà uploadé → {cache[key]}")
        return cache[key]

    logger.info(f"Upload {label} : {episode['title']}")
    yt = get_youtube_client()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)

        logger.info("  Téléchargement MP3...")
        mp3 = tmp / "episode.mp3"
        r = requests.get(episode["url"], timeout=60)
        r.raise_for_status()
        mp3.write_bytes(r.content)

        logger.info("  Téléchargement artwork...")
        artwork = tmp / "artwork.jpg"
        r = requests.get(ARTWORK_URL, timeout=30)
        r.raise_for_status()
        artwork.write_bytes(r.content)

        logger.info("  Conversion MP4...")
        mp4 = tmp / "episode.mp4"
        _mp3_to_mp4(mp3, artwork, mp4)

        video_id = _upload(yt, mp4, episode["title"], tags)

    cache[key] = video_id
    save_cache(cache)
    return video_id


# ── Gestion playlist YouTube classique ───────────────────────────────────────

def get_or_create_youtube_playlist(title: str) -> str:
    """Retourne l'ID de la playlist YouTube. La crée si elle n'existe pas."""
    if PLAYLIST_ID_FILE.exists():
        pid = PLAYLIST_ID_FILE.read_text().strip()
        if pid:
            return pid
    env_id = os.getenv("YOUTUBE_PLAYLIST_ID")
    if env_id:
        PLAYLIST_ID_FILE.parent.mkdir(exist_ok=True)
        PLAYLIST_ID_FILE.write_text(env_id)
        return env_id
    yt = get_youtube_client()
    resp = yt.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {"title": title, "description": "Radio caribéenne — Botiran News"},
            "status": {"privacyStatus": "public"},
        }
    ).execute()
    pid = resp["id"]
    PLAYLIST_ID_FILE.parent.mkdir(exist_ok=True)
    PLAYLIST_ID_FILE.write_text(pid)
    logger.info(f"Playlist YouTube créée : {pid}")
    logger.info(f"→ Ajoute ce secret GitHub : YOUTUBE_PLAYLIST_ID={pid}")
    return pid


def update_youtube_playlist(playlist_id: str, video_ids: list):
    """Vide la playlist YouTube puis la remplit dans l'ordre."""
    if not video_ids:
        logger.warning("Aucun videoId à ajouter")
        return
    yt = get_youtube_client()

    # Lister et supprimer les items existants
    existing = []
    try:
        next_page = None
        while True:
            resp = yt.playlistItems().list(
                part="id", playlistId=playlist_id,
                maxResults=50, pageToken=next_page
            ).execute()
            existing.extend(resp.get("items", []))
            next_page = resp.get("nextPageToken")
            if not next_page:
                break
    except Exception as e:
        logger.warning(f"  Impossible de lister les items (playlist vide ?) : {e}")
    for item in existing:
        yt.playlistItems().delete(id=item["id"]).execute()
    logger.info(f"  Supprimé {len(existing)} items")

    # Insérer les nouveaux items dans l'ordre
    for vid in video_ids:
        yt.playlistItems().insert(
            part="snippet",
            body={"snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": vid},
            }}
        ).execute()
    logger.info(f"  Ajouté {len(video_ids)} items")


# ── Points d'entrée publics ───────────────────────────────────────────────────

def get_or_upload_episode(mode: str) -> str | None:
    """Retourne le videoId YouTube du Flash Info pour le mode donné."""
    episode = get_latest_episode(mode)
    if not episode:
        logger.warning(f"Aucun épisode Flash Info trouvé pour le mode : {mode}")
        return None
    return _get_or_upload(
        episode,
        label="Flash Info",
        tags=["guadeloupe", "karukera", "flash info", "botiran", "antilles"],
    )


def get_or_upload_horoscope(mode: str) -> str | None:
    """Retourne le videoId YouTube de l'Horoscope pour le mode donné."""
    episode = get_latest_horoscope(mode)
    if not episode:
        logger.warning(f"Aucun horoscope trouvé pour le mode : {mode}")
        return None
    return _get_or_upload(
        episode,
        label="Horoscope",
        tags=["guadeloupe", "karukera", "horoscope", "botiran", "antilles"],
    )
