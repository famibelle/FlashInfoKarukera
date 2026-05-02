#!/usr/bin/env python3
"""
Playlist 24h — Botiran News Radio
Construit une playlist ~24h avec flash info et horoscopes positionnés à 6h, 12h, 18h.
Le pool musical est mis en cache une fois par jour pour éviter 200+ recherches à chaque run.
"""

import os
import sys
import json
import time
import random
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from ytmusicapi import YTMusic
from caribbean_db import CARIBBEAN_TRACKS
from youtube_uploader import get_or_upload_episode, get_or_upload_horoscope, get_or_upload_announcement

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BROWSER_JSON     = os.getenv("YTMUSIC_BROWSER_JSON_PATH", "browser.json")
POOL_CACHE_FILE  = Path("playlists/music_pool_cache.json")
PLAYLIST_ID_FILE = Path("playlists/playlist_24h_id.txt")

AVG_DURATION = 210  # secondes — fallback si duration_seconds absent

# 100 pistes max (limite YouTube Music API)
# 5 slots spéciaux (flash ×3 + horoscope ×2) → 95 pistes musicales
TRACKS_MORNING  = 31   # [4–34]  après flash matin + horoscope matin + annonce
TRACKS_MIDDAY   = 31   # [37–67] après flash midi + annonce
TRACKS_EVENING  = 30   # [71–100] après flash soir + horoscope soir + annonce

# Genres par bloc pour varier l'ambiance
BLOCK_GENRES = {
    "morning":   ["zouk", "zouk_retro", "gwoka", "chatta"],
    "midday":    ["kompa", "zouk", "chatta"],
    "evening":   ["gwoka", "bouillon", "zouk_retro", "kompa"],
}


# ── Auth ──────────────────────────────────────────────────────────────────────

def init_ytmusic() -> YTMusic:
    if not os.path.exists(BROWSER_JSON):
        logger.error(f"Auth file not found: {BROWSER_JSON}")
        sys.exit(1)
    return YTMusic(BROWSER_JSON)


# ── Pool musical ──────────────────────────────────────────────────────────────

def _search(yt: YTMusic, name: str, artist: str):
    """Retourne (videoId, duration_seconds) ou (None, 0)."""
    for query in [f"{name} {artist}", name]:
        try:
            results = yt.search(query, filter="songs", limit=10)
            for r in results:
                r_artists = ", ".join(a["name"] for a in (r.get("artists") or []))
                a = artist.lower()
                b = r_artists.lower()
                if a in b or b in a or any(w in b for w in a.split() if len(w) > 3):
                    dur = r.get("duration_seconds") or AVG_DURATION
                    return r["videoId"], dur
        except Exception as e:
            logger.warning(f"  Erreur recherche '{name}': {e}")
            break
    return None, 0


def resolve_music_pool(yt: YTMusic) -> list:
    """
    Résout tous les titres de la DB en videoIds.
    Résultat : [{"videoId": ..., "duration": ..., "genre": ..., "name": ..., "artist": ...}]
    Cache valide pour la journée (clé = date du jour).
    """
    today = datetime.now().strftime("%Y-%m-%d")

    if POOL_CACHE_FILE.exists():
        cached = json.loads(POOL_CACHE_FILE.read_text(encoding="utf-8"))
        tracks = cached.get("tracks", [])
        cache_has_metadata = tracks and "name" in tracks[0]
        if cached.get("date") == today and cache_has_metadata:
            logger.info(f"Pool musical depuis cache ({len(tracks)} pistes, {today})")
            return tracks
        elif cached.get("date") == today:
            logger.info("Cache du jour présent mais sans métadonnées — résolution complète")

    logger.info("Résolution du pool musical (200+ recherches YTMusic)...")
    pool = []
    seen = set()

    for genre, tracks in CARIBBEAN_TRACKS.items():
        for track in tracks:
            name   = track["name"]
            artist = track["artists"][0] if track["artists"] else ""
            vid, dur = _search(yt, name, artist)
            if vid and vid not in seen:
                pool.append({"videoId": vid, "duration": dur, "genre": genre, "name": name, "artist": artist})
                seen.add(vid)
                logger.info(f"  ✓ [{genre}] {name} — {artist}")
            else:
                logger.warning(f"  ✗ [{genre}] {name} — {artist}")

    POOL_CACHE_FILE.parent.mkdir(exist_ok=True)
    POOL_CACHE_FILE.write_text(
        json.dumps({"date": today, "tracks": pool}, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    logger.info(f"Pool : {len(pool)} pistes résolues — cache sauvegardé")
    return pool


# ── Construction des blocs ────────────────────────────────────────────────────

def fill_block(pool: list, genres: list, n: int) -> list:
    """
    Retourne exactement n entrées {videoId, artist} du pool filtrées par genre.
    Répète le sous-pool (shufflé) si nécessaire.
    """
    sub = [t for t in pool if t["genre"] in genres]
    if not sub:
        sub = pool

    result = []
    while len(result) < n:
        random.shuffle(sub)
        for track in sub:
            if len(result) >= n:
                break
            result.append({"videoId": track["videoId"], "artist": track.get("artist", "")})

    return result


def _add_special(playlist: list, label: str, fn):
    """Appelle fn(), ajoute le videoId à la playlist si disponible."""
    try:
        vid = fn()
        if vid:
            playlist.append(vid)
            logger.info(f"  {label} → https://youtu.be/{vid}")
    except Exception as e:
        logger.warning(f"  {label} ignoré : {e}")


# ── Playlist 24h ──────────────────────────────────────────────────────────────

def _block_artists(block: list, n: int = 3) -> list[str]:
    """Extrait les n premiers artistes uniques d'un bloc fill_block."""
    seen = []
    for t in block:
        a = t.get("artist", "").strip()
        if a and a not in seen:
            seen.append(a)
        if len(seen) >= n:
            break
    return seen


def build_24h_playlist(
    yt: YTMusic,
    *,
    no_flash: bool = False,
    no_horoscope: bool = False,
    no_announce: bool = False,
) -> List[str]:
    """
    Structure (100 pistes max — limite YouTube Music API) :
      [1]      Flash Info matin
      [2]      Horoscope matin
      [3]      Annonce matin (Solitude)
      [4–34]   31 pistes  zouk + zouk_retro + gwoka + chatta
      [35]     Flash Info midi
      [36]     Annonce midi (Solitude)
      [37–67]  31 pistes  kompa + zouk + chatta
      [68]     Flash Info soir
      [69]     Horoscope soir
      [70]     Annonce soirée (Solitude)
      [71–100] 30 pistes  gwoka + bouillon + zouk_retro + kompa
    """
    pool = resolve_music_pool(yt)
    if not pool:
        logger.error("Pool vide — abandon")
        sys.exit(1)

    playlist = []

    # Slots 1-2 — Flash Info matin + Horoscope matin
    logger.info("Slots 1-2 — Flash Info matin + Horoscope matin")
    if not no_flash:
        _add_special(playlist, "Flash Info matin", lambda: get_or_upload_episode("morning"))
    if not no_horoscope:
        _add_special(playlist, "Horoscope matin",  lambda: get_or_upload_horoscope("morning"))

    # Bloc matin [4-34]
    logger.info(f"Bloc matin ({TRACKS_MORNING} pistes)...")
    block_morning = fill_block(pool, BLOCK_GENRES["morning"], TRACKS_MORNING)
    artists_morning = _block_artists(block_morning)
    if not no_announce:
        _add_special(playlist, "Annonce matin",
                     lambda: get_or_upload_announcement("morning", artists_morning))
    playlist += [t["videoId"] for t in block_morning]

    # Slot 35 — Flash Info midi
    logger.info("Slot 35 — Flash Info midi")
    if not no_flash:
        _add_special(playlist, "Flash Info midi", lambda: get_or_upload_episode("midday"))

    # Bloc après-midi [37-67]
    logger.info(f"Bloc après-midi ({TRACKS_MIDDAY} pistes)...")
    block_midday = fill_block(pool, BLOCK_GENRES["midday"], TRACKS_MIDDAY)
    artists_midday = _block_artists(block_midday)
    if not no_announce:
        _add_special(playlist, "Annonce midi",
                     lambda: get_or_upload_announcement("midday", artists_midday))
    playlist += [t["videoId"] for t in block_midday]

    # Slots 68-69 — Flash Info soir + Horoscope soir
    logger.info("Slots 68-69 — Flash Info soir + Horoscope soir")
    if not no_flash:
        _add_special(playlist, "Flash Info soir",  lambda: get_or_upload_episode("evening"))
    if not no_horoscope:
        _add_special(playlist, "Horoscope soir",   lambda: get_or_upload_horoscope("evening"))

    # Bloc soirée [71-100]
    logger.info(f"Bloc soirée ({TRACKS_EVENING} pistes)...")
    block_evening = fill_block(pool, BLOCK_GENRES["evening"], TRACKS_EVENING)
    artists_evening = _block_artists(block_evening)
    if not no_announce:
        _add_special(playlist, "Annonce soirée",
                     lambda: get_or_upload_announcement("evening", artists_evening))
    playlist += [t["videoId"] for t in block_evening]

    special_count = sum([
        (0 if no_flash else 3),
        (0 if no_horoscope else 2),
        (0 if no_announce else 3),
    ])
    music_count = len(playlist) - special_count
    logger.info(f"Playlist : {len(playlist)} items ({music_count} pistes musicales, {special_count} slots spéciaux)")
    return playlist


# ── Gestion de la playlist YTMusic ───────────────────────────────────────────

def get_playlist_id(yt: YTMusic) -> str:
    """Retourne l'ID de la playlist 24h. La crée si elle n'existe pas encore."""
    if PLAYLIST_ID_FILE.exists():
        pid = PLAYLIST_ID_FILE.read_text().strip()
        if pid:
            return pid

    env_id = os.getenv("YTMUSIC_PLAYLIST_24H_ID")
    if env_id:
        PLAYLIST_ID_FILE.parent.mkdir(exist_ok=True)
        PLAYLIST_ID_FILE.write_text(env_id)
        return env_id

    logger.info("Création de la playlist 24h...")
    pid = yt.create_playlist(
        "Botiran News: La radio de la diaspora Guadeloupéenne au Luxembourg — 24h",
        "Playlist radio 24h — Flash Info, Horoscope & musique caribéenne",
        privacy_status="PUBLIC",
    )
    PLAYLIST_ID_FILE.parent.mkdir(exist_ok=True)
    PLAYLIST_ID_FILE.write_text(pid)
    logger.info(f"Playlist créée : {pid}")
    logger.info(f"→ Ajoute ce secret GitHub : YTMUSIC_PLAYLIST_24H_ID={pid}")
    return pid


def _get_removable(yt: YTMusic, playlist_id: str) -> list:
    try:
        tracks = yt.get_playlist(playlist_id, limit=200).get("tracks", [])
        return [t for t in tracks if t.get("setVideoId")]
    except Exception:
        return []


def _remove_all(yt: YTMusic, playlist_id: str, removable: list):
    if removable:
        yt.remove_playlist_items(playlist_id, removable)
        logger.info(f"  Supprimé {len(removable)} pistes")
        time.sleep(2)


def _add_items(yt: YTMusic, playlist_id: str, video_ids: list, label: str = ""):
    """Appelle add_playlist_items et logue le statut retourné."""
    status = yt.add_playlist_items(playlist_id, video_ids)
    tag = f" [{label}]" if label else ""
    logger.info(f"  add{tag} {len(video_ids)} items → status: {status}")
    if isinstance(status, dict) and status.get("status") not in (None, "STATUS_SUCCEEDED"):
        logger.warning(f"  Statut inattendu : {status}")
    return status


def update_playlist(yt: YTMusic, playlist_id: str, video_ids: List[str]):
    """
    Règle YouTube Music : après remove(N), un seul add(M) fonctionne si M ≤ 2×N.

    - Playlist vide (current=0)  : ajout direct, aucun remove préalable → pas de contrainte.
    - Run normal (current ≥ target//2) : remove tout → add tout en un appel.
    - Bootstrap (0 < current < target//2) : doublement 1→2→4→…→target
      (chaque remove libère N slots, le add suivant respecte M ≤ 2×N).
    """
    logger.info(f"Mise à jour playlist {playlist_id} ({len(video_ids)} items)...")

    removable = _get_removable(yt, playlist_id)
    current   = len(removable)
    target    = len(video_ids)
    logger.info(f"  État actuel : {current} pistes → cible : {target}")

    if current == 0:
        # Playlist vide : pas de remove préalable, ajout direct sans contrainte
        logger.info("  Playlist vide — ajout direct...")
        _add_items(yt, playlist_id, video_ids, "direct")

    elif current >= target // 2:
        # Run normal : remove tout → add tout en un seul appel
        _remove_all(yt, playlist_id, removable)
        _add_items(yt, playlist_id, video_ids, "normal")

    else:
        # Bootstrap : doublement strict pour respecter la règle M ≤ 2×N
        logger.info(f"  Bootstrap nécessaire ({current} < {target // 2})...")
        _remove_all(yt, playlist_id, removable)
        time.sleep(3)

        step = 1
        while step < target:
            _add_items(yt, playlist_id, video_ids[:step], f"step {step}")
            time.sleep(6)
            _remove_all(yt, playlist_id, _get_removable(yt, playlist_id))
            time.sleep(5)
            step = min(step * 2, target)

        # Ajout final de toutes les pistes (step vient d'atteindre target)
        _add_items(yt, playlist_id, video_ids, "final")

    # Vérification post-update
    actual = len(_get_removable(yt, playlist_id))
    if actual >= target:
        logger.info(f"  ✅ Vérification OK : {actual} pistes dans la playlist")
    else:
        logger.warning(f"  ⚠️ Vérification : {actual}/{target} pistes — ajout partiel ou délai API")


# ── Test pipeline annonces ───────────────────────────────────────────────────

def test_announce_pipeline(yt: YTMusic):
    """
    Teste la pipeline d'annonces Solitude sans upload YouTube.
    Pour chaque bloc (morning/midday/evening) :
      1. Tire les artistes depuis le pool musical (cache du jour si disponible)
      2. Génère le texte via Mistral
      3. Synthèse TTS fr_marie_happy → MP3 dans announce_tests/YYYY-MM-DD_HHMMSS/
    """
    from youtube_uploader import _mistral_chat, _load_prompt, ANNOUNCE_BLOC_LABEL
    from tts_utils import tts_call

    pool = resolve_music_pool(yt)
    if not pool:
        logger.error("Pool vide — abandon")
        sys.exit(1)

    out_dir = Path("announce_tests") / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Répertoire de sortie : {out_dir}")

    ok, ko = 0, 0
    for bloc in ["morning", "midday", "evening"]:
        block   = fill_block(pool, BLOCK_GENRES[bloc], 10)
        artists = _block_artists(block)
        label   = ANNOUNCE_BLOC_LABEL.get(bloc, bloc)

        logger.info(f"\n── Annonce {bloc} ({label}) ──")
        logger.info(f"  Artistes retenus : {', '.join(artists)}")

        try:
            system_prompt = (
                _load_prompt("solitude_ame.md")
                + "\n\n"
                + _load_prompt("kreyol_resistance_symbol.md")
            )
            brief = _load_prompt("solitude.md")
        except FileNotFoundError as e:
            logger.error(f"  Prompt manquant : {e}")
            ko += 1
            continue

        user_prompt = f"{brief}\n\nMoment : {label}\nArtistes : {', '.join(artists)}"
        try:
            text = _mistral_chat(system_prompt, user_prompt)
            logger.info(f"  Texte : {text!r}")
        except Exception as e:
            logger.error(f"  Mistral KO : {e}")
            ko += 1
            continue

        out_mp3 = out_dir / f"{bloc}.mp3"
        try:
            tts_call(text, out_mp3, voice_id="fr_marie_happy")
            logger.info(f"  TTS OK → {out_mp3} ({out_mp3.stat().st_size:,} bytes)")
            ok += 1
        except Exception as e:
            logger.error(f"  TTS KO : {e}")
            ko += 1

    logger.info(f"\n{'✅' if ko == 0 else '⚠️'} Test annonces : {ok}/3 OK, {ko} KO — {out_dir}")


# ── Affichage ─────────────────────────────────────────────────────────────────

def show_playlist(yt: YTMusic, playlist_id: str):
    pl     = yt.get_playlist(playlist_id, limit=500)
    url    = f"https://music.youtube.com/playlist?list={playlist_id}"
    tracks = pl.get("tracks", [])
    print(f"\n{pl['title']}")
    print(f"{url}\n")
    for i, t in enumerate(tracks, 1):
        artists = ", ".join(a["name"] for a in (t.get("artists") or []))
        print(f"  {i:3d}. {t['title']} — {artists}")
    print(f"\n{len(tracks)} piste(s)")


# ── Point d'entrée ────────────────────────────────────────────────────────────

def run(
    show: bool = False,
    dry_run: bool = False,
    no_flash: bool = False,
    no_horoscope: bool = False,
    no_announce: bool = False,
):
    yt          = init_ytmusic()
    playlist_id = get_playlist_id(yt)

    if show:
        show_playlist(yt, playlist_id)
        return

    video_ids = build_24h_playlist(
        yt,
        no_flash=no_flash,
        no_horoscope=no_horoscope,
        no_announce=no_announce,
    )

    if dry_run:
        logger.info(f"[dry-run] {len(video_ids)} items — playlist non mise à jour")
        for i, vid in enumerate(video_ids, 1):
            logger.info(f"  {i:3d}. https://youtu.be/{vid}")
        return

    update_playlist(yt, playlist_id, video_ids)

    logger.info("✅ Playlist 24h mise à jour !")
    logger.info(f"   https://music.youtube.com/playlist?list={playlist_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Botiran News — playlist 24h")
    parser.add_argument("--show", action="store_true",
                        help="Affiche la playlist YouTube Music sans la mettre à jour")
    parser.add_argument("--dry-run", action="store_true",
                        help="Construit la playlist sans la mettre à jour")
    parser.add_argument("--no-flash", action="store_true",
                        help="Ignore les épisodes Flash Info")
    parser.add_argument("--no-horoscope", action="store_true",
                        help="Ignore les épisodes Horoscope")
    parser.add_argument("--no-announce", action="store_true",
                        help="Ignore les annonces Solitude (TTS Mistral)")
    parser.add_argument("--test-announce", action="store_true",
                        help="Teste la pipeline Mistral+TTS des annonces Solitude (MP3 locaux, pas d'upload)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Logging DEBUG (ytmusicapi, requêtes, détails internes)")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.test_announce:
        yt = init_ytmusic()
        test_announce_pipeline(yt)
    else:
        run(
            show=args.show,
            dry_run=args.dry_run,
            no_flash=args.no_flash,
            no_horoscope=args.no_horoscope,
            no_announce=args.no_announce,
        )
