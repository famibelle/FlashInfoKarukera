#!/usr/bin/env python3
"""
Affiche la playlist complète (musique, flash info, horoscope, interview, liners, capsules).

Usage:
    python show_playlist.py
    python show_playlist.py --json    # Affiche le JSON brut
    python show_playlist.py --stats   # Statistiques seulement
"""

import argparse
import json
from pathlib import Path

SEQUENCE_PATH = Path("docs/radio_sequence.json")

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
    args = parser.parse_args()
    
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
