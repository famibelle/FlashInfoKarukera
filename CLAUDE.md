# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Présentation

**Flash Info Karukera** est une plateforme de radio guadeloupéenne automatisée. Des pipelines Python autonomes génèrent du contenu audio en français/créole (flash info, horoscope, émissions culturelles, liners, capsules) via LLM (texte) + TTS, le publient dans `docs/` (servi par GitHub Pages), et le diffusent sur Telegram, Buzzsprout/Apple Podcasts, YouTube Music, Spotify et X. Tout tourne quotidiennement via des workflows GitHub Actions en cron — il n'y a pas de serveur permanent.

## Installation & commandes

Projet Python, sans `package.json`. Utilise un `.venv` local et `requirements.txt`.

```bash
pip install -r requirements.txt          # dépendances
git submodule update --init --recursive  # OBLIGATOIRE — voir « sous-module privé » ci-dessous

# Lancer un pipeline à la main (la plupart acceptent --verbose et --dry-run) :
python flash-info-gwada.py --verbose      # --dry-run = texte seul, sans TTS ni publication
python horoscope-gwada.py
python generate_emission.py --dry-run
python generate_radio_sequence.py         # reconstruit docs/radio_sequence.json

# Tests (unittest stdlib, pas de pytest) :
python -m unittest tests.test_normalize -v
python -m unittest tests.test_playlist_engine -v
```

Les secrets sont lus depuis `.env` (gitignored) via un petit loader inline dans chaque script — clés notables : `MISTRAL_API_KEY`, `TELEGRAM_BOT_TOKEN`, `BUZZSPROUT_API_TOKEN`, `YOUTUBE_*`, `SPOTIPY_*`, `X_*`, `GH_TOKEN`.

## Le sous-module `private/` est obligatoire

`private/` est un sous-module git (`FlashInfoKarukera-private`) et les scripts **ne tournent pas sans lui**. Il contient le cerveau éditorial :
- `private/prompts/*.md` — les prompts de persona/style (Harry, Maryse, Monique, Corinne, Solitude ; chacun a un `_ame.md` = identité + un prompt de tâche).
- `private/index_culturel/*_ref.md` — tableaux Markdown de faits culturels (flore, faune, zodiaque, symboles de résistance, lieux spirituels…) ; les scripts y piochent des **lignes aléatoires** comme matière première.
- `private/data/sources.py` — `RSS_FEEDS` / `RSS_SOURCES` pour le flash info.

En CI le sous-module nécessite le token `PAT_SUBMODULE`, et un `git config insteadOf` doit être positionné avant le checkout pour cloner le dépôt privé.

## Architecture

Chaque type de contenu est un script de pipeline indépendant et autonome à la racine du dépôt, suivant le même schéma : **sélection de la source → texte LLM (Mistral) → TTS (Voxtral) → publication dans `docs/` + diffusion**.

| Script | Sortie |
|--------|--------|
| `flash-info-gwada.py` | Flash info (RSS + météo + prénoms du jour), 3×/jour |
| `horoscope-gwada.py` | Horoscope créole 12 signes (+ vidéo TikTok), 2×/jour |
| `generate_emission.py` | Émission culturelle (monologue de 3 min) |
| `generate_interview.py`, `generate_liner.py` | Interviews, liners d'artistes |
| `generate_radio_sequence.py` | Assemble tout dans `docs/radio_sequence.json` |
| `playlist_24h.py` + `caribbean_db.py` | Playlist YouTube Music 24h depuis la base de pistes caribéennes |

Modules partagés : `tts_utils.py` (TTS/STT Voxtral via l'API Mistral — modèle `voxtral-mini-tts-2603`, voix `fr_marie_*` indexées par ton), `data/tts_normalize.py` (normalisation du texte pour le TTS, le code le plus couvert par les tests unitaires), `title_generator.py`, `playlist_engine.py`.

**Modèles LLM :** `mistral-large-latest` pour la génération de contenu ; `mistral-small-latest` / `open-mistral-nemo` pour les tâches légères (classification de ton, hashtags).

### Organisation des sorties (`docs/` → GitHub Pages)

`docs/radio_sequence.json` est la **seule source de vérité du player radio** (`docs/radio.html`). L'audio est sous `docs/audio/`, `docs/liners/`, `docs/capsules/`. Flux RSS : `podcast.xml`, `flash-info.xml`, `horoscope.xml`, `emissions.xml`.

### Orchestration (GitHub Actions)

`.github/workflows/daily-radio-orchestrator.yml` tourne à 3 horaires cron et déclenche les workflows par contenu **séquentiellement** via `gh workflow run … && gh run watch` (horoscope → flash-info → liners → capsules → émission → playlist). L'édition (`matin`/`midi`/`soir`) est déduite de l'heure UTC.

## Pièges critiques (extraits de `DEVNOTES.md`)

- **`[skip ci]` casse le déploiement Pages.** Les commits générés portent `[skip ci]`, ce qui annule *tous* les déclencheurs, y compris `pages.yml`. Chaque workflow qui commite dans `docs/` doit appeler explicitement `gh workflow run pages.yml --ref main` après son push (un `workflow_dispatch` ne peut pas être annulé par `[skip ci]`).
- **Le player lit uniquement `radio_sequence.json`.** `radio.html` ne scanne jamais le système de fichiers. Si un fichier n'est pas dans ce JSON au chargement de la page, il n'existe pas pour le player.
- **Les noms de fichiers sont déterministes** (`flash-info-YYYYMMDD-{matin|midi|soir}.mp3`, `horoscope-YYYYMMDD-{matin|soir}.mp3`, `emission-YYYY-MM-DD.mp3`). Donc `generate_radio_sequence.py` pré-remplit chaque slot du jour avec `"pending": true` ; le player saute en 404 gracieusement tant que le fichier n'existe pas.
- **Les scripts tournent à/après 02:00 UTC.** Un job à 00:00 UTC (ex. dreams) doit calculer `yesterday` explicitement, sinon il ne trouve aucun contenu généré pour « aujourd'hui ».
