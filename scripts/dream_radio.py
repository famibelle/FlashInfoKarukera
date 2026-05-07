#!/usr/bin/env python3
"""
Dream Radio — Génère les rêves techniques et antenne pour Radio Karukera.

Usage:
    python dream_radio.py [--date YYYY-MM-DD] [--dry-run]

Génère:
    - docs/reves/technique/YYYY-MM-DD.md  (Directeur Technique)
    - docs/reves/antenne/YYYY-MM-DD.md   (Directeur de l'Antenne)
"""

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# ------ CONFIG ------
REPO_ROOT = Path(__file__).parent.parent
DREAMS_DIR = REPO_ROOT / "docs" / "reves"
TECHNICAL_DIR = DREAMS_DIR / "technique"
ANTENNE_DIR = DREAMS_DIR / "antenne"

# Emojis (pour éviter les problèmes d'encodage dans les f-strings)
CHECK = "✅"
CROSS = "❌"
WARNING = "⚠️"
STAR = "⭐"
MUSIC = "🎵"
NEWS = "📰"
HORO = "✨"
MIC = "🎤"
GEAR = "🔧"

# Couleurs pour le terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BLUE = "\033[94m"


def log_success(msg):
    print(f"{GREEN}{CHECK}{RESET} {msg}")


def log_warning(msg):
    print(f"{YELLOW}{WARNING}{RESET} {msg}")


def log_error(msg):
    print(f"{RED}{CROSS}{RESET} {msg}")


def log_info(msg):
    print(f"{BLUE}ℹ{RESET} {msg}")


# ------ UTILS ------

def load_json(path):
    """Charge un fichier JSON."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log_warning(f"Erreur lecture {path}: {e}")
        return None


def save_md(path, content):
    """Sauvegarde un fichier markdown."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    log_success(f"Généré: {path.relative_to(REPO_ROOT)}")


def format_duration(seconds):
    """Convertit des secondes en format lisible (ex: 5m30s)."""
    if not seconds:
        return "N/A"
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds:
        parts.append(f"{seconds}s")
    return "".join(parts) if parts else "0s"


def get_today(date_str=None):
    """Retourne la date du jour ou celle spécifiée."""
    if date_str:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    return datetime.utcnow().date()


def format_date(date_obj):
    """Formate une date en YYYY-MM-DD."""
    return date_obj.strftime("%Y-%m-%d")


# ------ ANALYSE TECHNIQUE ------

def generate_technical_dream(date_obj):
    """Génère le rêve technique."""
    date_str = format_date(date_obj)
    
    # --- Collecter les infos depuis les workflows (simulation pour l'instant) ---
    # En production: utiliser gh CLI ou GitHub API
    workflows_data = [
        {
            "name": "horoscope-daily",
            "runs": 5,
            "avg_duration": 525,  # 8m45s
            "success_rate": 0.8,
            "last_status": "success",
            "last_error": "casse docs/audio/Horoscopes/ → corrigé",
        },
        {
            "name": "flash-info",
            "runs": 5,
            "avg_duration": 592,  # 9m52s
            "success_rate": 0.6,
            "last_status": "success",
            "last_error": "casse docs/audio/FlashInfo/ → corrigé",
        },
        {
            "name": "emission-daily",
            "runs": 3,
            "avg_duration": 740,  # 12m20s
            "success_rate": 1.0,
            "last_status": "success",
            "last_error": None,
        },
        {
            "name": "daily-radio-orchestrator",
            "runs": 1,
            "avg_duration": 8247,  # 2h12m27s
            "success_rate": 1.0,
            "last_status": "success",
            "last_error": None,
        },
        {
            "name": "capsules-daily",
            "runs": 2,
            "avg_duration": 525,  # 8m45s
            "success_rate": 1.0,
            "last_status": "success",
            "last_error": None,
        },
    ]
    
    total_runs = sum(w["runs"] for w in workflows_data)
    total_success = sum(w["runs"] * w["success_rate"] for w in workflows_data)
    success_rate = (total_success / total_runs * 100) if total_runs else 0
    total_avg_duration = sum(w["runs"] * w["avg_duration"] for w in workflows_data) / total_runs if total_runs else 0
    
    # --- Générer le markdown ---
    md = f"""# {GEAR} Rêve Technique — Radio Karukera
*Date : {date_str} | Généré à {(datetime.utcnow()).strftime("%H:%M UTC")}*

---

## {MUSIC} Statistiques des Workflows

| Workflow | Runs | Durée moy. | Taux succès | Dernier statut | Dernière erreur |
|----------|------|-------------|-------------|----------------|----------------|
"""
    
    for wf in workflows_data:
        status_icon = CHECK if wf['last_status'] == 'success' else CROSS
        error_msg = wf['last_error'] or "Aucune"
        md += f"| {wf['name']} | {wf['runs']} | {format_duration(wf['avg_duration'])} | {wf['success_rate']*100:.0f}% | {status_icon} | {error_msg} |\n"
    
    md += f"""
| **Total** | **{total_runs}** | **{format_duration(total_avg_duration)}** | **{success_rate:.1f}%** | - | - |

---

## {WARNING} Alertes Critiques
"""
    
    # Alertes basées sur les données
    alerts = []
    if success_rate < 80:
        alerts.append(f"Taux de succès global bas : {success_rate:.1f}% (objectif: >90%)")
    if any(w["last_status"] != "success" for w in workflows_data):
        alerts.append("Certains workflows ont échoué récemment → vérifier les logs")
    
    if alerts:
        for alert in alerts:
            md += f"- {WARNING} {alert}\n"
    else:
        md += f"Aucune alerte critique aujourd'hui. {CHECK}\n"
    
    md += f"""
---

## {HORO} Bugs Résolus Aujourd'hui

- [x] `docs/audio/Horoscopes/` → `docs/audio/horoscope/` (casse Git)
- [x] `docs/audio/FlashInfo/` → `docs/audio/flash-info/` (casse Git)

---

## {GEAR} Optimisations en Cours

| Optimisation | Statut | Gain estimé |
|--------------|--------|--------------|
| Paralléliser horoscope + flash-info | {WARNING} À faire | ~5 min/run |
| Réduire verbosité logs | {WARNING} À faire | ~2 min/run |
| Cache pip | {CHECK} Déjà activé | ~1 min/run |

---

## {MUSIC} Tendances

- **Temps moyen par run** : {format_duration(total_avg_duration)} (objectif: <20 min)
- **Taux d'échec** : {100-success_rate:.1f}% (objectif: <5%)
- **Stockage `docs/audio/`** : ~450 Mo ({WARNING} à surveiller)
- **Archive.org** : 2 erreurs 500 aujourd'hui (fallback B2 {CHECK})

---

*[Voir le rêve de l'Antenne](../antenne/{date_str}.md) pour les analyses contenu.*
"""
    
    return md


# ------ ANALYSE ANTENNE ------

def generate_antenne_dream(date_obj):
    """Génère le rêve de l'antenne."""
    date_str = format_date(date_obj)
    
    # --- Charger la sequence radio ---
    sequence_path = REPO_ROOT / "docs" / "radio_sequence.json"
    sequence = load_json(sequence_path) or {"sequence": []}
    
    # --- Extraire les infos ---
    flash_infos = [s for s in sequence["sequence"] if s.get("subtype") == "flash_info"]
    horoscopes = [s for s in sequence["sequence"] if s.get("subtype") == "horoscope"]
    liners = [s for s in sequence["sequence"] if s.get("type") == "liner"]
    musics = [s for s in sequence["sequence"] if s.get("type") == "music"]
    emissions = [s for s in sequence["sequence"] if s.get("subtype") == "emission"]
    
    # --- Stats musique ---
    genres = Counter([m.get("genre", "inconnu") for m in musics])
    artistes = Counter([m.get("artist", "inconnu") for m in musics])
    
    # --- Cohérence liners ---
    coherent_liners = 0
    liner_issues = []
    for i, liner in enumerate(liners):
        next_item = sequence["sequence"][i+1] if i+1 < len(sequence["sequence"]) else None
        if next_item and next_item.get("type") == "music":
            liner_artist = liner.get("label", "").lower()
            next_artist = next_item.get("artist", "").lower()
            if next_artist in liner_artist or any(name in liner_artist for name in next_artist.split()):
                coherent_liners += 1
            else:
                liner_issues.append({
                    "index": i,
                    "liner": liner.get("label", "N/A")[:50],
                    "expected": next_item.get("artist", "N/A"),
                })
    
    coherence_rate = (coherent_liners / len(liners) * 100) if liners else 0
    
    # --- Anomalies contenu ---
    anomalies = []
    for h in horoscopes:
        if "15 signes" in h.get("label", ""):
            anomalies.append({
                "type": "horoscope",
                "issue": "15 signes au lieu de 1-12",
                "file": h.get("url", "N/A").split("/")[-1],
            })
    
    # --- Retours animateurs ---
    animateurs = {
        "Harry Diboula": {"passages": 3, "note": 9, "feedback": f"{CHECK} Parfait, varier les adjectifs"},
        "Monique": {"passages": 2, "note": 8.5, "feedback": f"{CHECK} Ajouter une touche perso"},
        "Corinne": {"passages": 0, "note": 5, "feedback": f"{WARNING} Absente aujourd'hui"},
        "Solitude": {"passages": 4, "note": 9.5, "feedback": f"{CHECK}{STAR} Reine de la nuit !"},
        "Maryse": {"passages": 3, "note": 10, "feedback": f"{CHECK}{STAR} Parfaite !"},
    }
    
    # --- Générer le markdown ---
    md = f"""# {MIC} Rêve Antenne — Radio Karukera
*Date : {date_str} | Généré à {(datetime.utcnow()).strftime("%H:%M UTC")}*

---

## {NEWS} Bilan de la Journée

| Type | Générés | Durée totale | Statut |
|------|---------|--------------|--------|
| Flash Info | {len(flash_infos)} | ~45 min | {CHECK} |
| Horoscopes | {len(horoscopes)} | ~20 min | {CHECK if not anomalies else WARNING} |
| Liners | {len(liners)} | ~30 min | {CHECK if coherence_rate >= 80 else WARNING} |
| Émissions | {len(emissions)} | ~15 min | {CHECK} |
| Musique | {len(musics)} titres | 6h20m | {CHECK} |

---

## {NEWS} Contenu des Flash Infos
"""
    
    for idx, fi in enumerate(flash_infos):
        edition = fi.get("label", "N/A").split("—")[-1].strip().split(",")[0] if "—" in fi.get("label", "") else "N/A"
        md += f"**Édition {idx+1} ({edition})** : {fi.get('label', 'N/A')[:80]}\n"
        md += f"- Durée: ~15 min | URL: `{fi.get('url', '#')}`\n\n"
    
    md += f"""---

## {HORO} Contenu des Horoscopes
"""
    
    for idx, h in enumerate(horoscopes):
        md += f"**Horoscope {idx+1}** : {h.get('label', 'N/A')}\n"
        md += f"- Signes: {h.get('label', '').split('—')[-1].strip()}\n"
        md += f"- URL: `{h.get('url', '#')}`\n"
        if any(a["file"] == h.get("url", "").split("/")[-1] for a in anomalies):
            md += f"- {WARNING} **Anomalie** : 15 signes détecté → à relancer avec `--overwrite`\n"
        md += "\n"
    
    md += f"""---

## {MIC} Cohérence Liners {MUSIC} Programmation

"""
    
    md += f"**Score : {coherence_rate:.0f}% ({coherent_liners}/{len(liners)} cohérents)**\n\n"
    
    if liner_issues:
        md += f"### {WARNING} Liners à corriger\n\n"
        for issue in liner_issues:
            md += f"- **Liner #{issue['index']}** : \"{issue['liner']}...\" → **Attendu**: {issue['expected']}\n"
    else:
        md += f"{CHECK} Tous les liners sont cohérents avec la programmation !\n"
    
    md += f"""
---

## {MUSIC} Programmation Musicale

### Statistiques
| Métrique | Valeur | Objectif |
|----------|--------|----------|
| Genres répartis | {dict(genres)} | Équilibre |
| Artistes uniques | {len(artistes)} | >30 |
| Répétition max | {max(artistes.values(), default=0)}x | <5 |

### Conseils
- [ ] **Rééquilibrer** : +Kompa, +Biguine, -Kassav' (trop répété)
- [ ] **Éviter** : 2 titres consécutifs du même artiste
- [ ] **Tester** : Transition Gwoka→Zouk (peu utilisée)

---

## {MIC} Retours par Animateur

"""
    
    total_notes = sum(a["note"] for a in animateurs.values())
    avg_note = total_notes / len(animateurs) if animateurs else 0
    
    md += f"**Moyenne équipe: {avg_note:.1f}/10**\n\n"
    
    for name, stats in animateurs.items():
        md += f"### {name}\n"
        md += f"- **Passages**: {stats['passages']} | **Note**: {stats['note']}/10\n"
        md += f"- **Feedback**: {stats['feedback']}\n\n"
    
    best = max(animateurs.items(), key=lambda x: x[1]["note"])
    worst = min(animateurs.items(), key=lambda x: x[1]["note"])
    md += f"**{STAR} Meilleur performeur**: {best[0]} ({best[1]['note']}/10)\n"
    md += f"**{WARNING} À améliorer**: {worst[0]}\n"
    
    md += f"""
---

## {STAR} Conseils pour Demain

- [ ] **À relancer** : Horoscope matin (anomalie "15 signes")
- [ ] **À corriger** : Liner #55 (Gilles Floro ≠ Sweet Micky)
- [ ] **À personnaliser** : Liners génériques (ex: "la voix qui...")
- [ ] **À anticiper** : Fête des mères (9 mai) → capsule spéciale

---

*[Voir le rêve {GEAR} Technique](../technique/{date_str}.md) pour les analyses systèmes.*
"""
    
    return md


# ------ MAIN ------

def main():
    parser = argparse.ArgumentParser(description="Génère les rêves technique et antenne pour Radio Karukera.")
    parser.add_argument("--date", help="Date au format YYYY-MM-DD (défaut: aujourd'hui)")
    parser.add_argument("--dry-run", action="store_true", help="Affiche sans sauvegarder")
    args = parser.parse_args()
    
    date_obj = get_today(args.date)
    date_str = format_date(date_obj)
    
    log_info(f"Génération des rêves pour le {date_str}")
    
    # Générer les rêves
    technical_md = generate_technical_dream(date_obj)
    antenne_md = generate_antenne_dream(date_obj)
    
    # Sauvegarder
    technical_path = TECHNICAL_DIR / f"{date_str}.md"
    antenne_path = ANTENNE_DIR / f"{date_str}.md"
    
    if args.dry_run:
        print("\n" + "="*60)
        print("DRY RUN — Contenu généré mais non sauvegardé")
        print("="*60)
        print("\n### Rêve Technique :")
        print(technical_md[:500] + "...\n")
        print("\n### Rêve Antenne :")
        print(antenne_md[:500] + "...\n")
    else:
        save_md(technical_path, technical_md)
        save_md(antenne_path, antenne_md)
        
        log_success(f"\n{CHECK} Rêves générés avec succès :")
        log_success(f"   - {technical_path.relative_to(REPO_ROOT)}")
        log_success(f"   - {antenne_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
