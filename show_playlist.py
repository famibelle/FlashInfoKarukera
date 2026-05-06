#!/usr/bin/env python3
"""
Affiche la playlist complète (musique, flash info, horoscope, interview, liners, capsules).

Usage:
    python show_playlist.py
    python show_playlist.py --json    # Affiche le JSON brut
    python show_playlist.py --stats   # Statistiques seulement
    python show_playlist.py --url "https://music.youtube.com/playlist?list=PL..."  # YouTube playlist
    python show_playlist.py           # Lit YTMUSIC_PLAYLIST_24H_ID du .env si défini
"""

import argparse
import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from ytmusicapi import YTMusic

load_dotenv()

SEQUENCE_PATH = Path("docs/radio_sequence.json")
BROWSER_JSON = Path("browser.json")


def extract_playlist_id(url: str) -> str | None:
    """Extrait l'ID de playlist d'une URL YouTube Music."""
    # Match https://music.youtube.com/playlist?list=PLwzi3ZXU6pu-M_41dNvTNOXTtz14uv8Rn
    match = re.search(r'(?:list=|/playlist/)([a-zA-Z0-9_-]{11,})', url)
    return match.group(1) if match else None


def fetch_youtube_playlist(playlist_id: str, browser_path: Path = BROWSER_JSON) -> dict | None:
    """Récupère une playlist YouTube Music via l'API."""
    if not browser_path.exists():
        print(f"❌ Fichier browser.json introuvable : {browser_path}")
        print("   Nécessaire pour l'authentification YouTube Music API")
        return None
    
    try:
        yt = YTMusic(str(browser_path))
        playlist = yt.get_playlist(playlist_id, limit=500)
        # Ajouter la date de publication depuis YouTube Data API si disponible
        try:
            playlist['publishedAt'] = get_playlist_published_at(playlist_id)
        except Exception:
            pass  # Ne pas échouer si l'API YouTube Data n'est pas disponible
        return playlist
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de la playlist : {e}")
        return None


def get_playlist_published_at(playlist_id: str) -> str | None:
    """Récupère la date de publication/modification de la playlist via YouTube Data API."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from pathlib import Path
    
    youtube_token_path = Path("youtube_token.json")
    if not youtube_token_path.exists():
        return None
    
    try:
        import json
        with open(youtube_token_path) as f:
            token_data = json.load(f)
        creds = Credentials.from_authorized_user_info(token_data)
        youtube = build('youtube', 'v3', credentials=creds)
        
        pl_resp = youtube.playlists().list(
            part='snippet',
            id=playlist_id
        ).execute()
        
        if pl_resp.get('items'):
            return pl_resp['items'][0]['snippet'].get('publishedAt')
        return None
    except Exception:
        return None


def display_youtube_playlist(playlist: dict, use_colors: bool = True) -> None:
    """Affiche une playlist YouTube Music."""
    from datetime import datetime
    tracks = playlist.get("tracks", [])
    title = playlist.get("title", "Playlist YouTube")
    author = playlist.get("author", {}).get("name", "Inconnu")
    track_count = playlist.get("trackCount", len(tracks))
    duration = playlist.get("duration", "")
    playlist_id = playlist.get("id", "")
    published_at = playlist.get("publishedAt")
    
    color = COLORS["music"] if use_colors else ""
    reset = COLORS["reset"] if use_colors else ""
    
    url = f"https://music.youtube.com/playlist?list={playlist_id}"
    
    # Formater la date de publication
    published_str = ""
    if published_at:
        try:
            dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            published_str = f"Modifiée le : {dt.strftime('%Y-%m-%d %H:%M:%S')}"
        except:
            published_str = f"Modifiée le : {published_at}"
    
    print(f"\n{'=' * 80}")
    print(f"{color}🎵 PLAYLIST YOUTUBE MUSIC — {title}{reset}")
    print(f"{color}Par : {author}{reset}")
    print(f"{color}Pistes : {track_count} | Durée : {duration}{reset}")
    print(f"{color}Lien : {url}{reset}")
    if published_str:
        print(f"{color}{published_str}{reset}")
    print(f"{'=' * 80}\n")
    
    for i, track in enumerate(tracks, 1):
        if not track:
            continue
        
        video_title = track.get("title", "Inconnu")
        artists = track.get("artists", [{"name": "Inconnu"}])
        artist_names = ", ".join(a.get("name", "") for a in artists if a)
        duration_str = track.get("duration", "--:--")
        
        # Convertir durée ISO en mm:ss si nécessaire
        if duration_str and ":" in duration_str and not duration_str.startswith("PT"):
            pass  # déjà au format mm:ss ou hh:mm:ss
        elif duration_str and duration_str.startswith("PT"):
            # Convertir ISO 8601 duration
            duration_str = format_iso_duration(duration_str)
        
        print(f"{color}{i:3d}. {video_title} — {artist_names} ({duration_str}){reset}")
    
    print(f"\n{'=' * 80}\n")


def format_iso_duration(iso_duration: str) -> str:
    """Convertit une durée ISO 8601 (PT...H...M...S) en mm:ss."""
    import re
    try:
        # Parser manuellement PT#H#M#S
        match = re.match(r'^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$', iso_duration)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            total_seconds = hours * 3600 + minutes * 60 + seconds
            return format_duration(total_seconds)
        return "--:--"
    except:
        return "--:--"


def display_youtube_stats(playlist: dict) -> None:
    """Affiche les statistiques d'une playlist YouTube."""
    from datetime import datetime
    tracks = playlist.get("tracks", [])
    title = playlist.get("title", "Playlist YouTube")
    author = playlist.get("author", {}).get("name", "Inconnu")
    track_count = playlist.get("trackCount", len(tracks))
    playlist_id = playlist.get("id", "")
    published_at = playlist.get("publishedAt")
    
    url = f"https://music.youtube.com/playlist?list={playlist_id}"
    
    # Formater la date de publication
    published_str = ""
    if published_at:
        try:
            dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            published_str = f"Modifiée le : {dt.strftime('%Y-%m-%d %H:%M:%S')}"
        except:
            published_str = f"Modifiée le : {published_at}"
    
    print("\n" + "=" * 60)
    print("📊 STATISTIQUES DE LA PLAYLIST YOUTUBE")
    print("=" * 60)
    print(f"Titre : {title}")
    print(f"Auteur : {author}")
    print(f"Nombre de pistes : {track_count}")
    print(f"Lien : {url}")
    if published_str:
        print(f"{published_str}")
    print("=" * 60 + "\n")


# Couleurs ANSI pour un affichage plus lisible
COLORS = {
    "reset": "\033[0m",
    "music": "\033[94m",      # Bleu
    "transition": "\033[93m", # Jaune
    "liner": "\033[96m",      # Cyan
    "capsule": "\033[95m",    # Magenta
    "header": "\033[92m",     # Vert
    "dim": "\033[2m",         # Gris
}

# Icons par type/subtype
ICONS = {
    "music": "🎵",
    "transition": {
        "flash_info": "📰",
        "horoscope": "🔮",
        "interview": "🎙️",
    },
    "liner": "🎤",
    "capsule": "🌺",
}


def get_icon(item: dict) -> str:
    """Retourne l'icon pour un item."""
    if item["type"] == "transition":
        return ICONS["transition"].get(item.get("subtype", ""), "➡️")
    return ICONS.get(item["type"], "❓")


def get_color(item: dict) -> str:
    """Retourne la couleur ANSI pour un item."""
    return COLORS.get(item["type"], COLORS["reset"])


def format_duration(seconds: int | None) -> str:
    """Formate une durée en secondes en mm:ss."""
    if seconds is None:
        return "--:--"
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def display_playlist(data: dict, use_colors: bool = True) -> None:
    """Affiche la playlist complète."""
    sequence = data.get("sequence", [])
    
    print(f"\n{'=' * 80}")
    print(f"📻 PLAYLIST COMPLÈTE — {data.get('generated', 'N/A')}")
    print(f"{'=' * 80}")
    print(f"📊 Statistiques: {data.get('music', 0)} morceaux | {data.get('liners', 0)} liners | "
          f"{data.get('capsules', 0)} capsules | {data.get('transitions', 0)} transitions")
    print(f"{'=' * 80}\n")
    
    for i, item in enumerate(sequence, 1):
        color = get_color(item) if use_colors else ""
        reset = COLORS["reset"] if use_colors else ""
        icon = get_icon(item)
        
        # Formatage selon le type
        if item["type"] == "music":
            title = item.get("title", "Inconnu")
            artist = item.get("artist", "Inconnu")
            genre = item.get("genre", "")
            duration = format_duration(item.get("duration"))
            print(f"{color}{i:3d}. {icon} {title} — {artist} {f'[{genre}]' if genre else ''} ({duration}){reset}")
            
        elif item["type"] == "transition":
            subtype = item.get("subtype", "")
            label = item.get("label", "Transition")
            icon = ICONS["transition"].get(subtype, "➡️")
            print(f"{color}{i:3d}. {icon} {label}{reset}")
            
        elif item["type"] == "liner":
            label = item.get("label", "Annonce")
            print(f"{color}{i:3d}. 🎤 {label}{reset}")
            
        elif item["type"] == "capsule":
            label = item.get("label", "Capsule culturelle")
            print(f"{color}{i:3d}. 🌺 {label}{reset}")
        else:
            print(f"{color}{i:3d}. ❓ {item}{reset}")
    
    print(f"\n{'=' * 80}")


def display_stats(data: dict) -> None:
    """Affiche uniquement les statistiques."""
    print("\n" + "=" * 60)
    print("📊 STATISTIQUES DE LA PLAYLIST")
    print("=" * 60)
    print(f"Généré le : {data.get('generated', 'N/A')}")
    print(f"Total éléments : {len(data.get('sequence', []))}")
    print(f"  🎵 Musiques : {data.get('music', 0)}")
    print(f"  🎤 Liners : {data.get('liners', 0)}")
    print(f"  🌺 Capsules : {data.get('capsules', 0)}")
    print(f"  ➡️  Transitions : {data.get('transitions', 0)}")
    
    # Compter par subtype de transition
    transitions = [i for i in data.get('sequence', []) if i.get('type') == 'transition']
    subtype_counts = {}
    for t in transitions:
        subtype = t.get('subtype', 'unknown')
        subtype_counts[subtype] = subtype_counts.get(subtype, 0) + 1
    
    print(f"\n  Transitions par type:")
    for subtype, count in subtype_counts.items():
        icon = ICONS["transition"].get(subtype, "➡️")
        print(f"    {icon} {subtype}: {count}")
    print("=" * 60 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Affiche la playlist complète")
    parser.add_argument("--json", action="store_true", help="Affiche le JSON brut")
    parser.add_argument("--stats", action="store_true", help="Affiche uniquement les statistiques")
    parser.add_argument("--no-colors", action="store_true", help="Désactive les couleurs")
    parser.add_argument("--sequence", metavar="FICHIER", 
                        help="Chemin vers radio_sequence.json (défaut: docs/radio_sequence.json)")
    parser.add_argument("--url", metavar="URL", 
                        help="URL d'une playlist YouTube Music (ex: https://music.youtube.com/playlist?list=PL...)")
    parser.add_argument("--browser", metavar="FICHIER", 
                        help="Chemin vers browser.json (défaut: browser.json)")
    args = parser.parse_args()
    
    # Mode YouTube playlist
    playlist_id = None
    
    # 1. Priorité à --url
    if args.url:
        playlist_id = extract_playlist_id(args.url)
        if not playlist_id:
            print(f"❌ URL invalide : {args.url}")
            print("   Format attendu : https://music.youtube.com/playlist?list=PL...")
            return
    # 2. Sinon, vérifier YTMUSIC_PLAYLIST_24H_ID dans .env ou variables d'environnement
    elif os.getenv("YTMUSIC_PLAYLIST_24H_ID"):
        playlist_id = os.getenv("YTMUSIC_PLAYLIST_24H_ID")
    
    if playlist_id:
        browser_path = Path(args.browser) if args.browser else BROWSER_JSON
        playlist = fetch_youtube_playlist(playlist_id, browser_path)
        
        if not playlist:
            return
        
        if args.json:
            print(json.dumps(playlist, indent=2, ensure_ascii=False))
        elif args.stats:
            display_youtube_stats(playlist)
        else:
            display_youtube_playlist(playlist, use_colors=not args.no_colors)
        return
    
    # Mode local (radio_sequence.json)
    sequence_path = Path(args.sequence) if args.sequence else SEQUENCE_PATH
    
    if not sequence_path.exists():
        print(f"❌ Fichier introuvable : {sequence_path}")
        print("   Génère d'abord la séquence avec : python generate_radio_sequence.py")
        return
    
    with open(sequence_path, encoding="utf-8") as f:
        data = json.load(f)
    
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif args.stats:
        display_stats(data)
    else:
        display_playlist(data, use_colors=not args.no_colors)


if __name__ == "__main__":
    main()
