# 🎵 Spotify Dynamic Radio System

## Vue d'ensemble

Ce système génère et met à jour automatiquement une playlist Spotify **"Radio des Îles"** en fonction de l'heure de la journée, entièrement orchestré via **GitHub Actions**.

```
     06:00 UTC
        │
        ▼
    🌅 MORNING MODE
    ├─ Zouk doux
    ├─ Musique classique caribéenne
    └─ Ambiance calme
        │
        ▼ (12:00 UTC)
        │
        ▼
    ☀️ MIDDAY MODE
    ├─ Kompa
    ├─ Zouk festif
    └─ Énergie radio
        │
        ▼ (18:00 UTC)
        │
        ▼
    🌙 EVENING MODE
    ├─ Gwoka
    ├─ Léwoz
    └─ Vibes relaxantes
        │
        └─► (repeat at 06:00)
```

---

## 📁 Fichiers du système

| Fichier | Description |
|---------|-------------|
| **`playlist_engine.py`** | Moteur principal - orchestration et logique Spotify |
| **`auth_spotify.py`** | Script d'authentification OAuth - obtenir les credentials |
| **`.github/workflows/spotify-radio.yml`** | Workflow GitHub Actions - exécution programmée |
| **`SETUP_SPOTIFY_RADIO.md`** | Guide complet de configuration |
| **`tests/test_playlist_engine.py`** | Tests unitaires du système |

---

## 🚀 Démarrage rapide

### 1️⃣ Préparer les credentials Spotify

```bash
# Remplir auth_spotify.py avec vos credentials
vim auth_spotify.py
# - CLIENT_ID: voir https://developer.spotify.com/dashboard
# - CLIENT_SECRET: voir https://developer.spotify.com/dashboard

# Exécuter pour obtenir le REFRESH_TOKEN
python auth_spotify.py
```

### 2️⃣ Configurer les secrets GitHub

Dans votre repository : **Settings → Secrets and variables → Actions**

Ajouter 4 secrets :
- `SPOTIPY_CLIENT_ID` → Votre Client ID
- `SPOTIPY_CLIENT_SECRET` → Votre Client Secret
- `SPOTIPY_REFRESH_TOKEN` → Token obtenu avec `auth_spotify.py`
- `SPOTIFY_PLAYLIST_ID` → ID de votre playlist Spotify

### 3️⃣ Vérifier l'installation

```bash
# Vérifier le workflow
→ Aller sur GitHub → Actions → "🎶 Spotify Radio Playlist Update"

# Déclencher manuellement
→ "Run workflow" → "Run workflow"

# Vérifier la playlist
→ Ouvrir Spotify → Voir "Radio des Îles" mise à jour
```

---

## ⚙️ Architecture technique

### `playlist_engine.py`

**Classe `RadioMode`**
```python
RadioMode.MORNING   # 06:00-11:59
RadioMode.MIDDAY    # 12:00-17:59
RadioMode.EVENING   # 18:00-05:59
```

**Fonctions principales**
```python
init_spotify_client()        # Auth OAuth
get_radio_mode(hour)         # Déterminer le mode
search_tracks(sp, query)     # Rechercher sur Spotify
build_playlist(sp, mode)     # Construire la playlist
update_playlist(sp, id, uris)# Mettre à jour Spotify
run_playlist_engine()        # Orchestration complète
```

**Logique de sélection**
1. Détecter l'heure → choisir le mode radio
2. Construire requêtes adaptées au mode
3. Récupérer 20-50 tracks via Spotify API
4. Filtrer les doublons et répétitions d'artistes
5. Sélectionner 20 tracks équilibrées
6. Mettre à jour la playlist Spotify

### `.github/workflows/spotify-radio.yml`

**Exécution programmée (cron)**
```yaml
schedule:
  - cron: '0 6 * * *'   # 06:00 UTC - Morning
  - cron: '0 12 * * *'  # 12:00 UTC - Midday
  - cron: '0 18 * * *'  # 18:00 UTC - Evening
```

**Étapes**
1. Checkout le code
2. Installer Python et dépendances
3. Exécuter `playlist_engine.py`
4. Rapporter succès/erreur

---

## 🎶 Configuration musicale

Chaque mode a des **genres** et des **requêtes de recherche** spécifiques :

### 🌅 MODE_MORNING (06:00-11:59)
```
Requêtes :
  • "zouk doux"
  • "musique classique caribéenne"
  • "morning calm"
  • "ambient guadeloupe"
  • "classical caribbean"

Genres : zouk, classical, calm, ambient
Énergie max : 0.6 (musique plus calme)
```

### ☀️ MODE_MIDDAY (12:00-17:59)
```
Requêtes :
  • "kompa"
  • "zouk festif"
  • "caribbean dance"
  • "radio energy"
  • "festival music"

Genres : kompa, zouk, festive, dance
Énergie max : 0.85 (plus dynamique)
```

### 🌙 MODE_EVENING (18:00-05:59)
```
Requêtes :
  • "gwoka"
  • "léwoz"
  • "roots caribbean"
  • "chill evening"
  • "deep relaxation"

Genres : gwoka, roots, chill, deep, reggae
Énergie max : 0.65 (relaxant)
```

---

## 🔧 Personalisation

### Modifier les horaires d'exécution

Éditer `.github/workflows/spotify-radio.yml` :
```yaml
schedule:
  - cron: '0 6 * * *'   # Heure 1
  - cron: '0 12 * * *'  # Heure 2
  - cron: '0 18 * * *'  # Heure 3
```

Format cron : `minute heure jour mois jour_semaine`

### Changer la taille de la playlist

Éditer `playlist_engine.py` :
```python
track_uris = build_playlist(sp, mode, target_size=20)
#                                              ↑
#                               Nombre de tracks (20 par défaut)
```

### Ajouter des genres/requêtes

Éditer `RADIO_CONFIG` dans `playlist_engine.py` :
```python
RADIO_CONFIG = {
    RadioMode.MORNING: {
        "queries": [
            "zouk doux",
            "classical caribbean",
            "YOUR_QUERY_HERE"  # ← Ajouter
        ],
        ...
    }
}
```

---

## 🧪 Tests

Exécuter les tests unitaires :

```bash
pip install pytest
python -m pytest tests/test_playlist_engine.py -v
```

Tests couverts :
- ✅ Détection du mode radio (MORNING/MIDDAY/EVENING)
- ✅ Configuration radio (genres, requêtes, énergie)
- ✅ Conditions limites (transitions entre modes)
- ✅ Unicité des modes
- ✅ Validité de la configuration

---

## 📊 Flux de données

```
GitHub Actions (cron)
        │
        ▼
playlist_engine.py (run_playlist_engine)
        │
        ├─→ get_radio_mode(hour)
        │
        ├─→ init_spotify_client()
        │
        ├─→ build_playlist(mode)
        │   ├─→ search_tracks(query) × 5
        │   ├─→ get_recent_used_tracks()
        │   └─→ filter & select
        │
        └─→ update_playlist(track_uris)
            └─→ Spotify API

        ▼
Playlist "Radio des Îles" mise à jour 🎵
```

---

## 🐛 Dépannage

| Problème | Solution |
|----------|----------|
| Workflow échoue | Vérifier logs → Actions → Workflow |
| Auth échoue | Vérifier secrets GitHub + refresh token |
| Playlist ne change pas | Attendre l'heure programmée ou Run manuelle |
| Pas de tracks | Vérifier connexion internet + quota Spotify |

Voir `SETUP_SPOTIFY_RADIO.md` pour le dépannage complet.

---

## 📝 Dépendances

Ajouter à `requirements.txt` :
```
spotipy>=2.23.0
```

Installer localement :
```bash
pip install -r requirements.txt
```

---

## 🎯 Prochaines étapes

1. ✅ Lire `SETUP_SPOTIFY_RADIO.md` complètement
2. ✅ Exécuter `python auth_spotify.py`
3. ✅ Ajouter les 4 secrets à GitHub
4. ✅ Déclencher manuellement le workflow
5. ✅ Écouter votre playlist ! 🎵

---

## 📞 Support

Pour plus de détails : voir `SETUP_SPOTIFY_RADIO.md`

