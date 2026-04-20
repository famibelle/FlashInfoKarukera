# Flash Info Karukera

> Bulletin audio quotidien de l'actualité guadeloupéenne, généré automatiquement et diffusé sur Telegram, Buzzsprout (Spotify) et X.

---

## Vue d'ensemble

**Flash Info Karukera** est un pipeline entièrement automatisé qui collecte les flux RSS locaux chaque matin, rédige un script radio en créole oral guadeloupéen, le synthétise en audio via Voxtral TTS, et le diffuse sur plusieurs canaux.

Le pipeline enchaîne six étapes principales :

```mermaid
flowchart TD
    A([⏰ Cron GitHub Actions\n7h00 Guadeloupe]) --> B

    subgraph COLLECTE["① Collecte"]
        B[RSS Feeds\n6 sources locales] --> D[Filtrage par date\net priorité locale]
        C[Open-Meteo\nMétéo sans clé API] --> D
    end

    subgraph REDACTION["② Rédaction — 3 passes LLM"]
        D --> E[🖊️ Maryse\nRédactrice principale\nMistral Large]
        E --> F[✏️ Réviseur stylistique\nMistral Large]
        F --> G[📍 Ancrage local\nMistral Large]
    end

    subgraph POSTPROCESS["③ Post-traitement"]
        G --> H[_enforce_prononciations\nSigles, noms créoles,\ncodes DOM]
        H --> I[_ensure_sources_in_outro\nSécurité citations]
        I --> J[classify_tones\nTonalité par segment]
    end

    subgraph AUDIO["④ Génération audio"]
        J --> K[_normalize_for_tts\nNormalisation texte]
        K --> L[Voxtral TTS\nVoix Marie par tonalité]
        L --> M[FFmpeg\nAssemblage + stingers]
    end

    subgraph DIFFUSION["⑤ Diffusion"]
        M --> N[📱 Telegram]
        M --> O[🎙️ Buzzsprout → Spotify]
        M --> P[🐦 X / Twitter]
    end
```

---

## Architecture détaillée

### ① Collecte RSS et météo

Six flux RSS sont interrogés en parallèle et filtrés à la date cible :

| Source | URL |
|--------|-----|
| France-Antilles — Vie locale | `franceantilles.fr` |
| France-Antilles — Sports | `franceantilles.fr` |
| RCI Guadeloupe | `rci.fm` |
| Zyé a Mangrov'la | `zye-a-mangrovla.fr` |
| Région Guadeloupe | `regionguadeloupe.fr` |
| La 1ère — Économie | `la1ere.franceinfo.fr` |

Les articles sont **triés par priorité géographique** avant sélection des 7 meilleurs :

```mermaid
flowchart LR
    A[Tous les articles\ndu jour] --> B{Lieu détecté ?}
    B -->|Commune guadeloupéenne| C[Priorité 0 🟢]
    B -->|N/A inconnu| D[Priorité 1 🟡]
    B -->|Pays étranger| E[Priorité 2 🔴]
    C --> F[Tri final\nchronologique\npar groupe]
    D --> F
    E --> F
    F --> G[Top 7 retenus]
```

La météo est récupérée via [Open-Meteo](https://open-meteo.com/) (sans clé API) pour Pointe-à-Pitre.

---

### ② Rédaction — 3 passes LLM (Mistral Large)

Chaque passe a un rôle distinct et reçoit le script du précédent :

```mermaid
sequenceDiagram
    participant Items as Articles RSS + Météo
    participant Maryse as 🖊️ Maryse<br/>(Rédactrice)
    participant Style as ✏️ Réviseur<br/>Stylistique
    participant Anchor as 📍 Ancrage<br/>Local

    Items->>Maryse: JSON articles + météo
    Maryse-->>Style: Script brut segmenté
    Note over Maryse: temp=0.75<br/>intro + météo + sujets + outro

    Style-->>Anchor: Script révisé
    Note over Style: temp=0.3<br/>Supprime lyrisme, cartes postales<br/>Vérifie style oral

    Anchor-->>Anchor: Identifie lieux explicites
    Anchor-->>Items: Script ancré
    Note over Anchor: temp=0.3<br/>Remplace génériques par noms propres<br/>Glossaire sigles locaux
```

**Structure du script produit :**

```
INTRO      → "Bonjour, nous sommes le [DATE]... C'est parti."
MÉTÉO      → 2-3 phrases, conditions + températures + vent
SUJET 1    → 60-90 mots, transition géographique ou thématique
SUJET 2    → ...
...
SUJET N    → ...
OUTRO      → "Voilà pour ce Flash Info... Sources : X et Y."
```

Les segments sont séparés par `<<<SEG>>>`.

---

### ③ Post-traitement déterministe

Après les LLMs, trois passes de correction garantissent la qualité :

```mermaid
flowchart TD
    A[Script ancré] --> B[_enforce_prononciations\ninsensible à la casse\nnormalisation apostrophes]
    B --> C[_ensure_sources_in_outro\ninjecte Sources si absent]
    C --> D[classify_tones\nJSON array de tonalités]

    B -.->|Remplacements| E["JSVH → Jeunesse Sportive de Vieux Zabitan
UNAR → Union Athlétique de Rivière-des-Pères
SDIS → Service Départemental d'Incendie et de Secours
971 → quatre-vingt-dix-sept-un
Vieux-Habitants → Vieux Zabitan
Delgrès → Delgrèsse"]

    D -.->|Tonalités| F["neutral · happy · excited
sad · angry · curious"]
```

---

### ④ Normalisation TTS et génération audio

Avant chaque appel Voxtral, `_normalize_for_tts()` applique une chaîne de transformations dans un ordre strict :

```mermaid
flowchart TD
    T([Texte segment]) --> S0
    S0["0. Prononciations locales\n_PRONONCIATIONS_LOCALES"] --> S1
    S1["1. Apostrophes / emojis → ASCII"] --> S2
    S2["2. n° → numéro"] --> S3
    S3["3. Ordinaux : 1er → premier"] --> S4
    S4["4. Monnaies : 15€ → quinze euros"] --> S5
    S5["5. Scores : 3-1 → trois à un"] --> S6
    S6["6. Codes DOM : 971 → quatre-vingt-dix-sept-un"] --> S7
    S7["7. Heures : 07h30 → sept heures trente"] --> S8
    S8["8. Unités : 28°C → vingt-huit degrés"] --> S9
    S9["9. Nombres → num2words FR"] --> S10
    S10["9a. Sigles pointés : S.D.I.S → S. D. I. S."] --> S11
    S11["9b/c. Sigles caps → épelés\nsauf _SIGLES_MOT (RCI...)"] --> S12
    S12["10. Abréviations : M. → Monsieur"] --> S13
    S13["10b. Me + Majuscule → Maître"] --> DONE
    DONE([Texte TTS-ready])
```

**Voix par tonalité (voix Marie, Voxtral) :**

| Tonalité | Voice ID | Cas d'usage |
|----------|----------|-------------|
| `neutral` | `fr_marie_neutral` | Info factuelle, météo, administratif |
| `happy` | `fr_marie_happy` | Intro, outro, bonne nouvelle |
| `excited` | `fr_marie_excited` | Sport, exploit, événement culturel |
| `sad` | `fr_marie_sad` | Drame, accident, décès |
| `angry` | `fr_marie_angry` | Grève, conflit, polémique |
| `curious` | `fr_marie_curious` | Insolite, découverte, enquête |

---

### ⑤ Diffusion

```mermaid
flowchart LR
    MP3[flash-YYYYMMDD-HHMM.mp3] --> TG[📱 Telegram\nchat privé ou canal]
    MP3 --> BZ[🎙️ Buzzsprout\n→ Spotify, Apple Podcasts...]
    MP3 --> XX[🐦 X / Twitter]
```

---

## Installation

### Prérequis

- Python 3.12+
- FFmpeg (`apt install ffmpeg` ou `brew install ffmpeg`)
- Compte Mistral AI (Maryse + Voxtral TTS)
- Bot Telegram + chat ID
- Compte Buzzsprout
- App X/Twitter (tweepy)

### Dépendances Python

```bash
pip install -r requirements.txt
```

### Configuration `.env`

Créer un fichier `.env` à la racine du projet :

```env
MISTRAL_API_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
BUZZSPROUT_API_TOKEN=...
BUZZSPROUT_PODCAST_ID=...
X_API_KEY=...
X_API_SECRET=...
X_ACCESS_TOKEN=...
X_ACCESS_TOKEN_SECRET=...
```

### Stingers

Déposer les fichiers audio de jingle dans le dossier `Stingers/` (`.mp3` ou `.wav`).
Si le dossier est vide, un stinger synthétique est généré automatiquement.

---

## Utilisation

```bash
# Flash du jour (publication complète)
python flash-info-gwada.py

# Flash d'une date passée
python flash-info-gwada.py --date 2026-04-17

# Test : génère + Telegram, sans Buzzsprout ni X
python flash-info-gwada.py --dry-run

# Génère l'audio seulement, sans aucun envoi
python flash-info-gwada.py --no-send

# Logs détaillés (textes, JSONs, tonalités)
python flash-info-gwada.py --dry-run --verbose

# Choisir un stinger précis
python flash-info-gwada.py --stinger mon_jingle.mp3

# Chemin de sortie personnalisé
python flash-info-gwada.py --no-send --output /tmp/test.mp3
```

---

## Automatisation GitHub Actions

Le workflow `.github/workflows/flash-info.yml` déclenche le pipeline :

- **Automatiquement** tous les jours à 7h00 heure Guadeloupe (11h00 UTC)
- **Manuellement** depuis l'onglet Actions avec les options :
  - `date` — rejouer un flash passé
  - `dry_run` — test sans publication Buzzsprout/X
  - `verbose` — logs détaillés dans les Actions

Les secrets API sont configurés dans **Settings → Secrets and variables → Actions** :
`MISTRAL_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `BUZZSPROUT_API_TOKEN`, `BUZZSPROUT_PODCAST_ID`, `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`.

---

## Personnalisation

### Ajouter un flux RSS

```python
RSS_FEEDS = [
    ...
    "https://mon-media-local.fr/rss",
]
```

Ajouter la correspondance nom dans `_SOURCE_NAMES` si besoin.

### Ajouter une prononciation locale

```python
_PRONONCIATIONS_LOCALES = {
    ...
    "Mon Sigle": "développement oral complet",
    "Nom-Composé": "Prononziation Kréyòl",
}
```

### Ajouter un sigle prononcé comme un mot

```python
_SIGLES_MOT = {"RCI", "MON_SIGLE", ...}
```

---

## Structure du projet

```
FlashInfoKarukera/
├── flash-info-gwada.py       # Script principal
├── requirements.txt          # num2words, tweepy
├── .env                      # Clés API (non versionné)
├── Stingers/                 # Fichiers audio jingle
│   └── *.mp3 / *.wav
└── .github/
    └── workflows/
        └── flash-info.yml    # GitHub Actions
```
