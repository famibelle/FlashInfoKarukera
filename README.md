# Flash Info Karukera

> **Bulletin audio quotidien de l'actualité guadeloupéenne + horoscope créole**, lu par Botiran, généré automatiquement. Diffusé sur Telegram, Apple Podcasts, et **radio 24h/24** avec interviews, liners et capsules culturelles.

**Site web :** https://famibelle.github.io/FlashInfoKarukera/
**Canal Telegram :** https://t.me/botiran_news_971
**Podcast RSS :** https://famibelle.github.io/FlashInfoKarukera/podcast.xml
**Radio 24h :** https://famibelle.github.io/FlashInfoKarukera/radio_sequence.json

---

## 📻 Sommaire

1. [🎯 À quoi ça sert ?](#-à-quoi-ça-sert-)
2. [📊 Architecture complète](#-architecture-complète)
3. [🎙️ La voix de Botiran](#️-la-voix-de-botiran)
4. [📅 Les cinq éditions quotidiennes](#-les-cinq-éditions-quotidiennes)
5. [📻 La Radio 24h — Playlist automatique](#-la-radio-24h--playlist-automatique)
6. [🎤 Interviews — Symboles de la Résistance Créole](#-interviews--symboles-de-la-résistance-créole)
7. [🎙️ Liners — Annonces des artistes](#️-liners--annonces-des-artistes)
8. [🌺 Capsules culturelles](#-capsules-culturelles)
9. [⚙️ Orchestration — Workflows GitHub Actions](#️-orchestration--workflows-github-actions)
10. [🔧 Ce qu'il faut installer sur votre ordinateur](#-ce-quil-faut-installer-sur-votre-ordinateur)
11. [🔐 Les comptes à créer en ligne](#-les-comptes-à-créer-en-ligne)
12. [📦 Installation pas à pas](#-installation-pas-à-pas)
13. [⚙️ Configuration — le fichier .env](#️-configuration--le-fichier-env)
14. [📁 Les dossiers nécessaires](#-les-dossiers-nécessaires)
15. [▶️ Lancer les scripts à la main](#️-lancer-les-scripts-à-la-main)
16. [🤖 Automatisation complète](#-automatisation-complète)
17. [📅 Ce qui se passe chaque jour automatiquement](#-ce-qui-se-passe-chaque-jour-automatiquement)
18. [🛠️ Configurer les comptes tiers](#-configurer-les-comptes-tiers)
19. [✏️ Personnaliser le contenu](#️-personnaliser-le-contenu)
20. [🗂️ Structure complète du projet](#-structure-complète-du-projet)
21. [🔄 Pipeline technique détaillé](#-pipeline-technique-détaillé)
22. [❓ Questions fréquentes](#-questions-fréquentes)

---

## 🎯 À quoi ça sert ?

**Flash Info Karukera** est une **plateforme complète de radio automatisée** pour la Guadeloupe, combinant :

| Composant | Fréquence | Description |
|-----------|-----------|-------------|
| **Flash Info** | 3×/jour | Actualités locales (RSS) + météo + prénoms |
| **Horoscope** | 2×/jour | Horoscope créole avec 12 signes |
| **Interview** | 1×/jour | Interview radio sur les symboles de résistance créole |
| **Liners** | 15×/jour | Annonces des artistes à venir |
| **Capsules** | 12×/jour | Capsules culturelles guadeloupéennes |
| **Playlist Radio** | 24h/24 | Séquence musicale complète avec tous les éléments |

**Karukera**, c'est le nom amérindien de la Guadeloupe — "l'île aux belles eaux".

---

## 📊 Architecture complète

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLASH INFO KARUKERA                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐      │
│  │  Flash Info     │    │  Horoscope       │    │  Interview       │      │
│  │  3×/jour        │    │  2×/jour         │    │  1×/jour         │      │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘      │
│           │                      │                      │                │
│           └──────────────────────┼──────────────────────┘                │
│                                  │                                        │
│                                  ▼                                        │
│           ┌─────────────────────────────────────────────────────┐           │
│           │                    ORCHESTRATEUR                     │           │
│           │              (generate-all.yml)                       │           │
│           │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐  │           │
│           │  │ Horoscope │→│Flash Info│→│  Liners  │→│Capsules │→│Interview│  │           │
│           │  └──────────┘ └──────────┘ └──────────┘ └─────────┘  │           │
│           │                           │                       │           │
│           │                           ▼                       ▼           │
│           │                    ┌──────────────────────────┐         │
│           │                    │   PLAYLIST RADIO 24h       │         │
│           │                    │ (radio_sequence.json)     │         │
│           │                    └──────────────────────────┘         │
│           │                                           │                   │
│           └───────────────────────────────┼───────────────────┘           │
│                                           ▼                                       │
│                              ┌─────────────────────────────┐                │
│                              │       DIFFUSION              │                │
│                              ├─────────────────────────────┤                │
│                              │ • Telegram (@botiran_news)  │                │
│                              │ • Apple Podcasts (RSS)      │                │
│                              │ • GitHub Pages (audio)      │                │
│                              │ • YouTube Music (playlist)  │                │
│                              └─────────────────────────────┘                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎙️ La voix de Botiran

**Botiran** est la voix IA de ce projet — inspirée de **Maryse Condé** (1934–2024), romancière guadeloupéenne, lauréate du prix Nobel alternatif de littérature en 2018. Elle a écrit *Ségou*, *Moi, Tituba, sorcière...*, *La Migration des cœurs*.

La voix est **directe, chaleureuse, ancrée dans le quotidien guadeloupéen**, sans langue de bois. Elle parle de Karukera pour les Guadeloupéens et la diaspora.

- **Son identité** → `prompts/maryse_ame.md`
- **La structure du flash** → `prompts/maryse.md`
- **Le style oral** → `prompts/styliste.md`
- **L'ancrage guadeloupéen** → `prompts/ancrage.md`

---

## 📅 Les cinq éditions quotidiennes

Le programme publie **trois flash infos** et **deux horoscopes** par jour :

| Édition | Heure (Paris, été) | Heure (Guadeloupe) | Contenu |
|---------|-------------------|---------------------|---------|
| **Flash info matin** | 5h30 | 1h30 | Intro · Actualités (24h) · Météo · Prénom du jour |
| **Horoscope matin** | 6h00 | 2h00 | Formule d'éveil · 12 signes · Intention du jour |
| **Flash info midi** | 13h00 | 9h00 | Intro · Actualités (8h) |
| **Horoscope soir** | 19h00 | 15h00 | Formule de clôture · 12 signes · Bilan du jour |
| **Flash info soir** | 20h00 | 16h00 | Intro · Actualités (8h) · Prénom de demain |

> **Décalage horaire :** La Guadeloupe a **4h de retard** sur Paris en hiver, **5h** en été (la Guadeloupe ne change pas d'heure).

### Anti-répétition entre les éditions

Pour éviter de répéter les mêmes nouvelles, le programme utilise :
- `data/used_articles_AAAA-MM-JJ.json` — articles déjà utilisés dans la journée
- `playlists/youtube_cache.json` — cache des appels LLM pour éviter les doublons

---

## 📻 La Radio 24h — Playlist automatique

### 🎯 Concept

Une **playlist radio complète de 24h** est générée automatiquement, combinant :
- **80 titres musicaux** (zouk, gwoka, kompa, bouillon, etc.)
- **15 liners** — annonces des artistes
- **12 capsules culturelles** — symboles de la Guadeloupe
- **5 transitions** — flash info matin/midi/soir + horoscope matin/soir
- **1 interview** — symbole de résistance créole (après flash info midi)

**Total : ~86 éléments** pour une diffusion continue.

### 📄 Fichier principal : `docs/radio_sequence.json`

```json
{
  "generated": "2026-05-03T20:18:14.141699+00:00",
  "music": 80,
  "liners": 15,
  "capsules": 12,
  "transitions": 6,
  "sequence": [
    {
      "type": "transition",
      "subtype": "flash_info",
      "url": ".../flash-info-20260503-matin.mp3",
      "label": "Flash Info Guadeloupe — matin",
      "icon": "📰"
    },
    {
      "type": "liner",
      "url": ".../liner-matin-2026-W17-artistes.mp3",
      "label": "Dans un moment : Artiste1, Artiste2, Artiste3",
      "icon": "🎙️"
    },
    {
      "type": "music",
      "videoId": "ABC123",
      "title": "Titre",
      "artist": "Artiste",
      "genre": "zouk",
      "duration": 180
    },
    {
      "type": "capsule",
      "url": ".../capsule-2026-05-03-matin-6.mp3",
      "label": "Capsule culturelle Guadeloupe",
      "icon": "🌺"
    },
    {
      "type": "transition",
      "subtype": "interview",
      "url": ".../interview-resistance-creole-2026-05-03.mp3",
      "label": "Interview — Creole Resistance Symbols",
      "icon": "🎙️"
    }
  ]
}
```

### 🎼 Structure des blocs

| Bloc | Taille | Contenu |
|------|--------|---------|
| **Matin** | 27 pistes | Flash info matin → Horoscope matin → 27 musiques avec liners/capsules |
| **Midi** | 27 pistes | Flash info midi → **Interview** → 27 musiques avec liners/capsules |
| **Soir** | 26 pistes | Flash info soir → Horoscope soir → 26 musiques avec liners/capsules |

### 📊 Statistiques

- **Durée totale estimée :** ~24 heures
- **Durée musique :** ~18-20 heures (80 pistes × ~13-15 min)
- **Durée transitions :** ~30-45 minutes (6 transitions)
- **Durée liners :** ~15-20 minutes (15 liners × ~1-1.5 min)
- **Durée capsules :** ~12-15 minutes (12 capsules × ~1-1.25 min)
- **Durée interview :** ~3 minutes

### 🔧 Génération

```bash
# Générer la playlist complète
python generate_radio_sequence.py

# Générer uniquement les liners
python generate_radio_sequence.py --generate-liners-only

# Générer uniquement les capsules
python generate_radio_sequence.py --generate-capsules-only

# Afficher la playlist avec statistiques
python show_playlist.py

# Afficher la playlist en mode compact
python show_playlist.py --compact
```

### 📺 Intégration YouTube Music

La playlist est synchronisée avec **YouTube Music** via `playlist_24h.py` :
- Crée une playlist de 80 titres musicaux
- Insère automatiquement les transitions (flash info, horoscope, interview, liners, capsules)
- Met à jour 3 fois par jour (après chaque session de génération)

---

## 🎤 Interviews — Symboles de la Résistance Créole

### 🎯 Concept

Une **interview radio de 3 minutes** est générée quotidiennement entre **Paul** (journaliste) et **Oliver** (expert culturel) sur les **symboles vivants de la résistance créole en Guadeloupe** : animaux, plantes et arbres utilisés par les Arawaks, Marrons et esclaves comme emblèmes de survie, liberté et identité.

### 📝 Génération

```bash
# Générer l'interview
python generate_interview.py

# Options
python generate_interview.py --verbose      # Affiche les prompts LLM
python generate_interview.py --dry-run       # Texte seul, pas de TTS
python generate_interview.py --dialogue foo.json  # Réutilise un dialogue existant
```

### 🎭 Structure du dialogue

- **Durée :** ~3 minutes (400-430 mots)
- **Alternance :** 8+ tours (Paul / Oliver)
- **Style :** Naturel, captivant, éducatif (pas de lecture)
- **Langue :** Anglais (pour une audience internationale)
- **Voix :**
  - Paul (journaliste) → `en_paul_*` (Voxtral)
  - Oliver (expert) → `gb_oliver_*` (Voxtral)

### 🎯 Contenu source

L'interview puise aléatoirement dans 3 fichiers de référence (tables Markdown) :
- `private/prompts/kreyol_resistance_symbol_ref.md` — symboles de résistance
- `private/prompts/faune_guadeloupe_ref.md` — faune locale
- `private/prompts/flore_guadeloupe_ref.md` — flore locale

**Sélection :** 10-15 lignes aléatoires par fichier, mélangées pour garantir la variété.

### 📁 Sortie

- **Fichier audio :** `docs/audio/Emissions/interview-resistance-creole-YYYY-MM-DD.mp3`
- **Fichier JSON :** `docs/audio/Emissions/interview-resistance-creole-YYYY-MM-DD.json`
- **Intégration :** Automatiquement insérée dans `radio_sequence.json` après le flash info midi

### ⚙️ Anti-répétition

Pour éviter que l'LLM ne génère toujours les mêmes interviews :
1. **UNIQUE_RUN_ID** — identifiant unique par exécution
2. **Sélection aléatoire** des lignes sources
3. **Contexte dynamique** — météo du jour + horoscope du jour intégrés au prompt
4. **Instructions SYSTEM_PROMPT** explicites : "CRITICAL: Generate a DIFFERENT interview each time"

---

## 🎙️ Liners — Annonces des artistes

### 🎯 Concept

Les **liners** sont de courtes annonces (20-30 secondes) qui présentent les artistes à venir dans la playlist radio.

Exemple : *"Dans un moment : Kassav', Zouk Machine, et Princess Caroline"*

### 📝 Génération

```python
# Dans generate_radio_sequence.py
from youtube_uploader import get_announcement_mp3_url
url = get_announcement_mp3_url(bloc, artists[:5])
```

### 🎤Voix

- Utilise les mêmes voix Voxtral que Botiran
- Ton adapté : généralement `neutral` ou `happy`

### 📁 Sortie

- **Fichiers :** `docs/liners/liner-{bloc}-{YYYY}-W{WW}-{artists}.mp3`
- **Exemple :** `liner-matin-2026-W17-kassav_zouk-machine_princess-caroline.mp3`

### 🔄 Fréquence

- **15 liners par jour** (5 par bloc : matin, midi, soir)
- **1 liner toutes les 6 pistes** musicales

---

## 🌺 Capsules culturelles

### 🎯 Concept

Les **capsules culturelles** sont de courtes présentations (45-90 secondes) sur des symboles de la culture guadeloupéenne :
- Faune locale (colibri, iguane, etc.)
- Flore locale (hibiscus, flamboyant, etc.)
- Résistance créole (symboles historiques)

### 📝 Génération

```python
# Dans generate_radio_sequence.py
from youtube_uploader import get_capsule_mp3_url
url = get_capsule_mp3_url(slot_id)
```

### 🎤 Voix

- Utilise les voix Voxtral
- Style narratif et éducatif

### 📁 Sortie

- **Fichiers :** `docs/capsules/capsule-{YYYY}-{MM}-{DD}-{position}.mp3`
- **Exemple :** `capsule-2026-05-03-matin-6.mp3`

### 🔄 Fréquence

- **12 capsules par jour** (4 par bloc)
- **1 capsule toutes les 6 pistes** musicales

---

## ⚙️ Orchestration — Workflows GitHub Actions

### 🎯 Architecture

L'orchestration repose sur **6 workflows séquentiels** déclenchés par `generate-all.yml` :

```yaml
# .github/workflows/generate-all.yml
jobs:
  1. horoscope:      # Génère l'horoscope du jour
     needs: none
     
  2. flash-info:      # Génère les 3 flash infos
     needs: horoscope
     
  3. liners:          # Génère les 15 liners
     needs: flash-info
     
  4. capsules:        # Génère les 12 capsules
     needs: liners
     
  5. interview:       # Génère l'interview (NON BLOQUANT)
     needs: capsules
     continue-on-error: true  # ⭐ Failure toléré
     
  6. playlist:        # Génère la playlist finale
     needs: capsules   # ⭐ Ne dépend PAS de interview
```

### 🕐 Planification (Cron)

Le workflow principal `generate-all.yml` s'exécute **3 fois par jour** :

| Heure UTC | Heure Paris (été) | Heure Guadeloupe | Blocs générés |
|-----------|-------------------|-------------------|----------------|
| 04:00 | 06:00 | 02:00 | Matin (flash + horoscope + liners + capsules + interview + playlist) |
| 11:00 | 13:00 | 09:00 | Midi (flash + liners + capsules + interview + playlist) |
| 17:00 | 19:00 | 15:00 | Soir (flash + horoscope + liners + capsules + interview + playlist) |

> **Note :** Les heures sont en UTC. Paris = UTC+2 (été) ou UTC+1 (hiver). Guadeloupe = UTC-4 (toute l'année).

### 🎯 Workflows individuels

| Workflow | Trigger | Fréquence | Rôle |
|----------|---------|-----------|------|
| `horoscope-daily.yml` | `workflow_dispatch` | 1×/jour | Génère l'horoscope |
| `flash-info.yml` | `workflow_dispatch` | 3×/jour | Génère les flash infos |
| `liners-daily.yml` | `workflow_dispatch` | 3×/jour | Génère les liners |
| `capsules-daily.yml` | `workflow_dispatch` | 3×/jour | Génère les capsules |
| `interview-daily.yml` | `workflow_dispatch` | 3×/jour | Génère l'interview |
| `botiran-radio-daily.yml` | `workflow_dispatch` / `workflow_run` | 3×/jour | Génère la playlist radio |
| `generate-all.yml` | `schedule` + `workflow_dispatch` | 3×/jour | **Orchestrateur** |

### ⚡ Non-bloquant — Interview

**Problème résolu :** Si l'interview échoue (ex: API Mistral indisponible), la playlist doit **toujours** être générée.

**Solution :**
```yaml
# Dans generate-all.yml
interview:
  needs: capsules
  continue-on-error: true  # ⭐ Ne bloque pas la suite
  steps:
    - run: gh run watch "$RUN_ID" --interval 20 --repo "$REPO" || true

playlist:
  needs: capsules  # ⭐ Ne dépend PAS de interview
```

**Résultat :** Même si l'interview échoue, les jobs 1-4 et 6 s'exécutent normalement.

### 🔄 Séquentialité

Tous les jobs s'exécutent **séquentiellement** pour éviter :
1. Les **conflits Git** (plusieurs workflows qui pushent simultanément)
2. Les **limites de taux** de l'API Mistral
3. L'**incohérence** des données (ex: playlist générée avant les liners)

---

## 🔧 Ce qu'il faut installer sur votre ordinateur

### Python (le moteur du programme)

Version **3.11 ou plus récente** (3.12 recommandé).

**Sur Windows :**
1. Aller sur [python.org/downloads](https://www.python.org/downloads/)
2. Télécharger Python 3.12.x
3. **Important :** cocher "Add Python to PATH" avant d'installer
4. Vérifier : `python --version` → doit afficher `Python 3.12.x`

**Sur Mac :** `brew install python@3.12`

**Sur Linux :** `sudo apt install python3.12 python3.12-venv python3-pip`

### FFmpeg (pour créer les vidéos et assembler l'audio)

**Sur Windows :**
1. Aller sur [ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Télécharger la version "essentials" pour Windows
3. Extraire dans `C:\ffmpeg\` et ajouter `C:\ffmpeg\bin` au PATH
4. Vérifier : `ffmpeg -version`

**Sur Mac :** `brew install ffmpeg`

**Sur Linux :** `sudo apt install ffmpeg fonts-noto-color-emoji`

### Git

**Sur Windows :** [git-scm.com](https://git-scm.com/)
**Sur Mac :** `brew install git`
**Sur Linux :** `sudo apt install git`

### mpg123 (pour écouter les fichiers audio — optionnel)

**Sur Mac :** `brew install mpg123`
**Sur Linux :** `sudo apt install mpg123`

---

## 🔐 Les comptes à créer en ligne

### 🎯 Services obligatoires

| Service | À quoi ça sert | Coût | Secret GitHub |
|---------|----------------|------|---------------|
| [Mistral AI](https://console.mistral.ai/) | Rédige le texte + synthèse vocale (Voxtral) | Payant | `MISTRAL_API_KEY` |
| [Telegram](https://telegram.org/) | Canal de diffusion audio/vidéo | Gratuit | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| [GitHub](https://github.com/) | Hébergement code + audio public | Gratuit | `PAT_SUBMODULE` |

### 🔧 Services optionnels

| Service | À quoi ça sert | Coût | Secrets |
|---------|----------------|------|---------|
| [OpenAI](https://platform.openai.com/) | Génère les thumbnails (GPT-Image-2) | Payant | `OPENAI_API_KEY` |
| [YouTube Data API](https://console.cloud.google.com/) | Upload vidéos | Gratuit (quotas) | `YOUTUBE_*` |
| [YouTube Music API](https://console.cloud.google.com/) | Gestion playlist | Gratuit | `YTMUSIC_*` |

---

## 📦 Installation pas à pas

### Étape 1 — Cloner le projet

```bash
git clone https://github.com/famibelle/FlashInfoKarukera.git
cd FlashInfoKarukera
```

### Étape 2 — Initialiser les submodules (prompts privés)

```bash
git submodule update --init --recursive
```

### Étape 3 — Créer un environnement Python isolé

```bash
python -m venv .venv

# Sur Windows :
.venv\Scripts\activate

# Sur Mac ou Linux :
source .venv/bin/activate
```

### Étape 4 — Installer les dépendances

```bash
pip install -r requirements.txt
```

### Étape 5 — Créer le fichier de configuration

```bash
# Sur Mac ou Linux :
touch .env

# Sur Windows :
copy NUL .env
```

### Étape 6 — Créer les dossiers nécessaires

```bash
mkdir -p Stingers Media docs/liners docs/capsules docs/audio/Emissions playlists
```

---

## ⚙️ Configuration — le fichier .env

Le fichier `.env` contient toutes vos clés d'accès. **Ce fichier est privé** — il est exclu de Git via `.gitignore`.

### 🔑 Clés obligatoires

```env
# ─────────────────────────────────────────────────
# Mistral AI — cerveau du projet
# https://console.mistral.ai/
# ─────────────────────────────────────────────────
MISTRAL_API_KEY=votre-clé-mistral-ici

# ─────────────────────────────────────────────────
# Telegram — canal de diffusion
# TELEGRAM_CHAT_ID : ID numérique (commence par -100)
# Trouver avec : curl "https://api.telegram.org/bot<TOKEN>/getChat?chat_id=@votre_canal"
# ─────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN=123456789:ABCdef-votre-token-ici
TELEGRAM_CHAT_ID=-100XXXXXXXXXX

# ─────────────────────────────────────────────────
# GitHub — accès aux submodules privés et push
# PAT_SUBMODULE : Personal Access Token avec permissions "repo" + "submodule"
# ─────────────────────────────────────────────────
PAT_SUBMODULE=ghp_votre-token-github
```

### 🔑 Clés optionnelles — YouTube Music (Playlist Radio)

```env
# YouTube Music API — pour la playlist 24h
YTMUSIC_PLAYLIST_24H_ID=PLxxxxxxxxxxxxxxxxxxxx
YOUTUBE_TOKEN_JSON={"access_token": "...", "refresh_token": "...", ...}
```

### 🔑 Clés optionnelles — Thumbnail OpenAI

```env
# OpenAI GPT-Image-2 — génération du thumbnail illustré
OPENAI_API_KEY=sk-votre-clé-openai
```

---

## 📁 Les dossiers nécessaires

### 🎵 `Stingers/` — Les jingles musicaux

Petites musiques insérées entre chaque segment. Formats : `.mp3` ou `.wav`.
Si le dossier est vide, un bip simple est généré automatiquement.

### 🖼️ `Media/` — Les images

```
Media/
├── botiran_profile.jpg              # Portrait de référence
├── botiran_news_default_thumbnail.png  # Image de secours
└── botiran_news_banner.png           # Bannière pour interstitiels
```

### 📝 `private/prompts/` — Les instructions pour l'IA

```
private/prompts/
├── maryse_ame.md          # L'âme de Botiran
├── maryse.md              # Comment rédiger le flash info
├── styliste.md            # Révision du style oral
├── ancrage.md             # Ancrage géographique
├── tones.md               # Classification des tonalités
├── prenom.md              # Prénoms du jour
├── horoscope.md           # Structure de l'horoscope
├── kreyol_resistance_symbol_ref.md  # Symboles de résistance (tables)
├── faune_guadeloupe_ref.md # Faune locale (tables)
└── flore_guadeloupe_ref.md # Flore locale (tables)
```

### 📊 `data/` — Les données et la mémoire

```
data/
├── sources.py                    # Flux RSS locaux et noms
├── tts_normalize.py              # Prononciations locales
├── fetes_patronales.py           # Fêtes des communes
├── marroniers.py                 # Événements récurrents
├── geography.py                  # Lieux et géographie
├── weather_codes.py              # Codes météo
├── rss.xml                       # Cache actualités (auto)
└── used_articles_AAAA-MM-JJ.json # Anti-répétition (auto)
```

### 📻 `docs/` — Site web GitHub Pages + Radio

```
docs/
├── index.html                    # Page d'accueil
├── favicon.svg                   # Favicon lambi 🐚
├── artwork.jpg                   # Pochette podcast
├── podcast.xml                   # Flux RSS unifié
├── radio_sequence.json           # Playlist radio 24h
├── liners/                       # Liners audio
│   └── liner-{bloc}-{date}-{artists}.mp3
├── capsules/                    # Capsules culturelles
│   └── capsule-{date}-{position}.mp3
└── audio/                       # Flash info + Horoscope + Interview
    ├── Emissions/
    │   └── interview-resistance-creole-{date}.mp3
    ├── flash-info/
    │   └── flash-info-{date}-{edition}.mp3
    └── horoscope/
        └── horoscope-{date}-{edition}.mp3
```

### 📊 `playlists/` — Caches et IDs

```
playlists/
├── youtube_cache.json           # Cache des appels LLM (anti-répétition)
├── music_pool_cache.json         # Cache du pool musical
├── playlist_24h_id.txt           # ID playlist YouTube Music
└── youtube_playlist_id.txt       # ID playlist YouTube
```

---

## ▶️ Lancer les scripts à la main

### 📰 Flash Info

```bash
python flash-info-gwada.py [OPTIONS]
```

| Option | Description | Exemple |
|--------|-------------|---------|
| `--edition` | matin/midi/soir | `--edition soir` |
| `--date AAAA-MM-JJ` | Rejouer une date | `--date 2026-04-17` |
| `--dry-run` | Génère sans publier | `--dry-run` |
| `--no-send` | Génère MP3 seulement | `--no-send` |
| `--tiktok` | Génère vidéo verticale | `--tiktok` |
| `--verbose` | Affiche les détails | `--verbose` |

### ✨ Horoscope

```bash
python horoscope-gwada.py [OPTIONS]
```

| Option | Description | Exemple |
|--------|-------------|---------|
| `--edition` | matin/soir | `--edition soir` |
| `--horoscope-signs N` | Nombre de signes | `--horoscope-signs 3` |
| `--tiktok` | Génère vidéo | `--tiktok` |
| `--verbose` | Affiche le texte | `--verbose` |

### 🎤 Interview

```bash
python generate_interview.py [OPTIONS]
```

| Option | Description | Exemple |
|--------|-------------|---------|
| `--verbose` | Affiche prompts LLM | `--verbose` |
| `--dry-run` | Texte seul, pas TTS | `--dry-run` |
| `--dialogue FILE` | Réutilise un dialogue | `--dialogue dialog.json` |

### 📻 Playlist Radio

```bash
python generate_radio_sequence.py [OPTIONS]
```

| Option | Description | Exemple |
|--------|-------------|---------|
| `--generate-liners-only` | Génère seulement les liners | `--generate-liners-only` |
| `--generate-capsules-only` | Génère seulement les capsules | `--generate-capsules-only` |
| `--dry-run` | Affiche sans écrire | `--dry-run` |
| `--programme` | Affiche le programme détaillé avec horaires | `--programme` |
| `--skip-liners` | Pas de liners | `--skip-liners` |

### 📺 Afficher la playlist

```bash
python show_playlist.py [OPTIONS]
```

| Option | Description | Exemple |
|--------|-------------|---------|
| `--compact` | Mode compact | `--compact` |
| `--json` | Export JSON | `--json` |
| `--stats` | Statistiques seulement | `--stats` |

---

## 🤖 Automatisation complète

### 🎯 Workflow principal : `generate-all.yml`

Ce workflow **orchestre** l'exécution séquentielle de tous les autres workflows :

```
1️⃣ Horoscope → 2️⃣ Flash Info → 3️⃣ Liners → 4️⃣ Capsules → 5️⃣ Interview → 6️⃣ Playlist
                       ↓ (non-bloquant) ↓ (dépend de capsules)
```

**Caractéristiques :**
- ✅ **Séquentiel** — évite les conflits Git
- ✅ **Non-bloquant** — l'interview peut échouer sans bloquer la playlist
- ✅ **3 exécutions/jour** — via cron (4h, 11h, 17h UTC)
- ✅ **Manuel** — déclenchable via `workflow_dispatch`

### 📅 Planification

| Workflow | Trigger | Cron (UTC) | Heure Paris (été) | Heure Guadeloupe |
|----------|---------|------------|-------------------|-------------------|
| `generate-all.yml` | schedule + manual | 0 4,11,17 * * * | 6h, 13h, 19h | 2h, 9h, 15h |

### 🔧 Secrets GitHub obligatoires

| Secret | Description | Exemple |
|--------|-------------|---------|
| `MISTRAL_API_KEY` | Clé API Mistral AI | `sk-...` |
| `TELEGRAM_BOT_TOKEN` | Token du bot Telegram | `123456:ABC-...` |
| `TELEGRAM_CHAT_ID` | ID du canal Telegram | `-100123456789` |
| `PAT_SUBMODULE` | PAT GitHub pour submodules | `ghp_...` |

### 🚀 Déclencher manuellement

1. Aller sur : https://github.com/famibelle/FlashInfoKarukera/actions
2. Sélectionner **🚀 Génération complète — Orchestrateur séquentiel**
3. Cliquer sur **Run workflow**
4. Choisir la branche `main`
5. Optionnel : cocher `verbose` pour plus de détails
6. Cliquer sur **Run workflow**

---

## 📅 Ce qui se passe chaque jour automatiquement

### ⏰ 4h UTC (6h Paris / 2h Guadeloupe) — Session Matin

```
1. horoscope-daily.yml → Génère horoscope matin
2. flash-info.yml → Génère flash info matin
3. liners-daily.yml → Génère 5 liners matin
4. capsules-daily.yml → Génère 4 capsules matin
5. interview-daily.yml → Génère interview (non-bloquant)
6. botiran-radio-daily.yml → Génère playlist radio complète
   └─> radio_sequence.json contient :
       • Flash info matin + Horoscope matin
       • 27 musiques + 5 liners + 4 capsules
       • Interview après flash info midi (si générée)
```

### ⏰ 11h UTC (13h Paris / 9h Guadeloupe) — Session Midi

```
1. horoscope-daily.yml → Déjà généré, passe
2. flash-info.yml → Génère flash info midi
3. liners-daily.yml → Génère 5 liners midi
4. capsules-daily.yml → Génère 4 capsules midi
5. interview-daily.yml → Génère interview (non-bloquant)
6. botiran-radio-daily.yml → Met à jour playlist
   └─> radio_sequence.json contient maintenant :
       • Flash info matin + midi + Horoscope matin
       • 54 musiques + 10 liners + 8 capsules
       • Interview après flash info midi
```

### ⏰ 17h UTC (19h Paris / 15h Guadeloupe) — Session Soir

```
1. horoscope-daily.yml → Génère horoscope soir
2. flash-info.yml → Génère flash info soir
3. liners-daily.yml → Génère 5 liners soir
4. capsules-daily.yml → Génère 4 capsules soir
5. interview-daily.yml → Génère interview (non-bloquant)
6. botiran-radio-daily.yml → Met à jour playlist finale
   └─> radio_sequence.json COMPLÈTE :
       • Flash info matin/midi/soir + Horoscope matin/soir
       • 80 musiques + 15 liners + 12 capsules
       • Interview après flash info midi
       • Durée totale : ~24 heures
```

---

## 🛠️ Configurer les comptes tiers

### Telegram — Créer un bot et un canal

**Créer le bot :**
1. Ouvrir Telegram → chercher **@BotFather**
2. Envoyer `/newbot`
3. Donner un nom, puis un nom d'utilisateur (doit finir par `bot`)
4. BotFather envoie le token → c'est votre `TELEGRAM_BOT_TOKEN`

**Créer le canal :**
1. Créer un canal public sur Telegram
2. Ajouter le bot comme **administrateur** avec droits de publication

**Trouver le TELEGRAM_CHAT_ID :**
```bash
curl "https://api.telegram.org/bot<VOTRE_TOKEN>/getChat?chat_id=@votre_canal"
```
La valeur `"id"` dans la réponse est votre `TELEGRAM_CHAT_ID` (commence par `-100`).

### GitHub — Personal Access Token

1. GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. **Generate new token** → cocher `repo` (accès complet)
3. Copier le token → c'est votre `PAT_SUBMODULE`

### Mistral AI

1. Aller sur [console.mistral.ai](https://console.mistral.ai/)
2. Créer une clé API dans **Settings** → **API Keys**
3. Copier la clé → `MISTRAL_API_KEY`

> **Modèle utilisé :** `mistral-large-latest` (pour l'interview)
> **Alternative :** `mistral-small-latest` ou `mistral-medium-latest` si limite de quota

---

## ✏️ Personnaliser le contenu

### Ajouter un site d'information

Éditer `data/sources.py` :
```python
RSS_FEEDS = {
    "Guadeloupe 1ère": "https://.../rss",
    "Nouveau Site": "https://.../rss",  # Ajouter ici
}
```

### Corriger une prononciation

Éditer `data/tts_normalize.py` :
```python
PRONONCIATIONS_LOCALES = {
    "Lyannaj": "Lyan naje",
    "Nouveau Mot": "prononciation",  # Ajouter ici
}
```

### Modifier les prompts LLM

Les fichiers dans `private/prompts/` définissent le style et le contenu :
- `maryse_ame.md` — Identité de Botiran
- `maryse.md` — Structure du flash info
- `horoscope.md` — Structure de l'horoscope
- `kreyol_resistance_symbol_ref.md` — Symboles pour les interviews

### Changer le pool musical

La playlist utilise les titres du cache `playlists/music_pool_cache.json`. Pour le modifier :
1. Modifier `playlist_24h.py`
2. Ou régénérer manuellement le pool

---

## 🗂️ Structure complète du projet

```
FlashInfoKarukera/
│
├── flash-info-gwada.py              # ★ Script flash info (3 éditions/jour)
├── horoscope-gwada.py               # ★ Script horoscope (2 éditions/jour)
├── generate_interview.py             # ★ Génère les interviews quotidiennes
├── generate_radio_sequence.py       # ★ Génère la playlist radio 24h
├── show_playlist.py                 # ★ Affiche la playlist
├── playlist_24h.py                  # ★ Synchronise avec YouTube Music
├── youtube_uploader.py               # ★ Génère liners et capsules
├── requirements.txt                 # Dépendances Python
├── .env                             # Clés API (PRIVÉ — dans .gitignore)
│
├── Stingers/                        # Jingles audio entre segments
├── Media/                           # Images (thumbnails, bannières)
│
├── private/                         # Submodule — prompts et données privées
│   └── prompts/                     # Instructions pour l'IA
│       ├── maryse_ame.md
│       ├── maryse.md
│       ├── styliste.md
│       ├── ancrage.md
│       ├── tones.md
│       ├── prenom.md
│       ├── horoscope.md
│       ├── kreyol_resistance_symbol_ref.md
│       ├── faune_guadeloupe_ref.md
│       └── flore_guadeloupe_ref.md
│
├── data/                            # Données et mémoire
│   ├── sources.py
│   ├── tts_normalize.py
│   ├── fetes_patronales.py
│   ├── marroniers.py
│   ├── geography.py
│   ├── weather_codes.py
│   ├── rss.xml
│   └── used_articles_AAAA-MM-JJ.json
│
├── docs/                            # Site GitHub Pages + Radio
│   ├── index.html
│   ├── favicon.svg
│   ├── artwork.jpg
│   ├── podcast.xml
│   ├── radio_sequence.json          # ✨ PLAYLIST RADIO 24H
│   ├── liners/                      # ✨ Liners audio
│   │   └── liner-{bloc}-{date}-{artists}.mp3
│   ├── capsules/                    # ✨ Capsules culturelles
│   │   └── capsule-{date}-{position}.mp3
│   └── audio/                       # ✨ Audio (flash info, horoscope, interview)
│       ├── Emissions/
│       │   └── interview-resistance-creole-{date}.mp3
│       ├── flash-info/
│       │   └── flash-info-{date}-{edition}.mp3
│       └── horoscope/
│           └── horoscope-{date}-{edition}.mp3
│
├── playlists/                       # Caches et IDs
│   ├── youtube_cache.json
│   ├── music_pool_cache.json
│   ├── playlist_24h_id.txt
│   └── youtube_playlist_id.txt
│
└── .github/
    └── workflows/
        ├── generate-all.yml         # ✨ ORCHESTRATEUR (cron 4h/11h/17h)
        ├── horoscope-daily.yml
        ├── flash-info.yml
        ├── liners-daily.yml          # ✨ Génère les liners
        ├── capsules-daily.yml        # ✨ Génère les capsules
        ├── interview-daily.yml       # ✨ Génère l'interview
        └── botiran-radio-daily.yml    # ✨ Génère la playlist radio
```

---

## 🔄 Pipeline technique détaillé

### Flash Info & Horoscope

```
RSS Feeds + Météo + Prénoms
    │
    ▼
┌───────────────────────┐
│  Botiran rédige       │  ← prompts/maryse.md
│  (Mistral AI)         │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  Révision stylistique │  ← prompts/styliste.md
│  (Mistral AI)         │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  Ancrage local        │  ← prompts/ancrage.md
│  (Mistral AI)         │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  TTS Voxtral          │  ← Normalisation (tts_normalize.py)
│  (Synthèse vocale)    │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  FFmpeg               │  ← Assemble avec stingers
│  (Assemblage audio)   │
└───────────┬───────────┘
            │
            ▼
    Telegram + GitHub Releases + RSS
```

### Interview Radio

```
private/prompts/kreyol_resistance_symbol_ref.md
private/prompts/faune_guadeloupe_ref.md
private/prompts/flore_guadeloupe_ref.md
    │
    ▼
┌───────────────────────┐
│  Sélection aléatoire   │  ← 10-15 lignes par fichier
│  de 10-15 symboles     │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  UNIQUE_RUN_ID        │  ← Anti-répétition
│  + Météo du jour       │
│  + Horoscope du jour   │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  Dialogue LLM          │  ← SYSTEM_PROMPT anti-bias
│  (Mistral AI)         │
│  8+ tours alternés    │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  TTS Voxtral          │  ← Paul (journalist) + Oliver (expert)
│  (2 voix différentes) │
└───────────┬───────────┘
            │
            ▼
    Interview MP3 + JSON
     + Intégration dans radio_sequence.json
```

### Liners & Capsules

```
Music Pool (YouTube)
    │
    ▼
┌───────────────────────┐
│  Sélection des artistes│  ← 5 artistes par liner
│  (aléatoire)          │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  Prompt LLM            │  ← "Annonce les artistes suivants..."
│  (Mistral AI)         │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  TTS Voxtral          │
│  (Voix Botiran)       │
└───────────┬───────────┘
            │
            ▼
    Liner/Capsule MP3
```

### Playlist Radio 24h

```
Music Pool (80 titres)
Liners (15)
Capsules (12)
Flash Info (3)
Horoscope (2)
Interview (1)
    │
    ▼
┌───────────────────────┐
│  build_sequence()      │  ← generate_radio_sequence.py
│  - Bloc matin (27)     │
│  - Bloc midi (27)      │  ← Interview insérée ici
│  - Bloc soir (26)      │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  radio_sequence.json  │  ← 86 éléments
│  (Playlist complète)   │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  YouTube Music         │  ← playlist_24h.py
│  (Synchronisation)     │
└───────────────────────┘
```

---

## ❓ Questions fréquentes

### 🔴 Le workflow échoue avec un conflit Git

**Cause :** Plusieurs workflows essaient de `git push` simultanément.
**Solution :** Utiliser l'orchestration séquentielle via `generate-all.yml` qui garantit qu'un seul workflow push à la fois.

### 🔴 L'interview bloque la playlist

**Cause :** Le job interview échouait et bloquait le job playlist.
**Solution :** 
- `continue-on-error: true` sur le job interview
- `needs: capsules` (pas `interview`) sur le job playlist
- `gh run watch ... || true` pour éviter la propagation d'erreur

### 🔴 L'interview n'apparaît pas dans la playlist

**Vérifications :**
1. Le fichier `docs/audio/Emissions/interview-resistance-creole-YYYY-MM-DD.mp3` existe-t-il ?
2. Le workflow `interview-daily.yml` a-t-il réussi ?
3. Le workflow `botiran-radio-daily.yml` a-t-il été exécuté **après** l'interview ?

**Solution :** L'interview est insérée par `generate_radio_sequence.py` **uniquement si le fichier MP3 existe** au moment de la génération.

### 🔴 Les liners/capsules ont des artistes factices

**Cause :** Le flag `--generate-liners-only` utilise des placeholders.
**Solution :** Utiliser le workflow complet `generate-all.yml` qui récupère les vrais artistes du music pool.

### 🔴 La playlist n'a pas 86 éléments

**Vérifier :**
```bash
python show_playlist.py --stats
```

**Causes possibles :**
- Le music pool est vide (`playlists/music_pool_cache.json`)
- Les transitions RSS sont manquantes (`docs/podcast.xml`)
- Les workflows n'ont pas tous terminé

### 🔴 Comment tester localement sans tout générer ?

```bash
# Tester l'intégration interview dans la playlist
python generate_radio_sequence.py --dry-run

# Tester uniquement la génération d'interview
python generate_interview.py --dry-run --verbose

# Voir la playlist actuelle
python show_playlist.py
```

### 🔴 Les workflows GitHub ne se déclenchent pas

**Vérifier :**
1. Les **secrets** sont-ils configurés ? (`MISTRAL_API_KEY`, `PAT_SUBMODULE`, etc.)
2. Les **workflows** sont-ils activés ? (Settings → Actions → General → Workflow permissions)
3. Le **submodule** `private/` est-il initialisé ? (`git submodule update --init`)

### 🔴 L'API Mistral retourne une erreur 429

**Cause :** Rate limit dépassé.
**Solution :** 
- Utiliser l'orchestration séquentielle (évite les appels concurrentiels)
- Attendre quelques minutes avant de relancer
- Vérifier votre quota Mistral AI

### 🔴 Comment forcer la régénération complète ?

```bash
# Supprimer les caches
rm -f playlists/youtube_cache.json playlists/music_pool_cache.json

# Relancer le workflow
gh workflow run generate-all.yml
```

### 🔴 Où sont stockés les fichiers audio ?

| Type | Emplacement | URL publique |
|------|-------------|--------------|
| Flash Info | `docs/audio/flash-info/` | `https://famibelle.github.io/FlashInfoKarukera/audio/flash-info/...` |
| Horoscope | `docs/audio/horoscope/` | `https://famibelle.github.io/FlashInfoKarukera/audio/horoscope/...` |
| Interview | `docs/audio/Emissions/` | `https://famibelle.github.io/FlashInfoKarukera/audio/Emissions/...` |
| Liners | `docs/liners/` | `https://famibelle.github.io/FlashInfoKarukera/liners/...` |
| Capsules | `docs/capsules/` | `https://famibelle.github.io/FlashInfoKarukera/capsules/...` |

### 🔴 Comment ajouter de la musique à la playlist ?

La playlist utilise le pool musical du cache `playlists/music_pool_cache.json`. Pour le mettre à jour :
1. Modifier `playlist_24h.py` (source du pool)
2. Ou régénérer manuellement : `python playlist_24h.py --update-pool`

---

## 📞 Support

Pour toute question ou problème :
- **Issues GitHub :** https://github.com/famibelle/FlashInfoKarukera/issues
- **Discussions :** https://github.com/famibelle/FlashInfoKarukera/discussions

---

**Dernière mise à jour :** 3 mai 2026  
**Version :** 2.0 — Radio 24h avec orchestration complète  
**Auteur :** Famibelle / Mistral Vibe  
**Licence :** MIT
