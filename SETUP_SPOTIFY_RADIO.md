# 🎵 Configuration du Système Spotify Radio

## 📋 Table des matières

1. [Étapes de configuration](#étapes-de-configuration)
2. [Obtenir les credentials Spotify](#obtenir-les-credentials-spotify)
3. [Configurer les secrets GitHub](#configurer-les-secrets-github)
4. [Vérifier l'installation](#vérifier-linstallation)
5. [Dépannage](#dépannage)

---

## ⚙️ Étapes de configuration

### **ÉTAPE 1 : Créer une application Spotify**

1. Aller sur [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Se connecter avec un compte Spotify (créer un compte gratuit si nécessaire)
3. Accepter les conditions d'utilisation
4. Créer une nouvelle application :
   - Nom : `FlashInfoKarukera Radio` (ou autre)
   - Accepter les conditions
   - Valider la création

### **ÉTAPE 2 : Récupérer les credentials**

Après création, vous verrez :
- ✅ **Client ID**
- ✅ **Client Secret** (cliquer sur "Show Client Secret")

**⚠️ Important :** Copier ces deux valeurs dans un endroit sûr.

### **ÉTAPE 3 : Obtenir le Refresh Token**

Le refresh token permet au workflow d'accéder à Spotify sans intervention manuelle.

#### Option A : Utiliser le script d'authentification fourni

1. Sauvegarder le code ci-dessous en fichier `auth_spotify.py` (dans le répertoire du projet)

```python
#!/usr/bin/env python3
"""
Script d'authentification Spotify - Obtenir le refresh token
"""
import os
import webbrowser
from spotipy.oauth2 import SpotifyOAuth

# Remplacer par vos credentials
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
REDIRECT_URI = "http://localhost:8888/callback"

# Créer une instance OAuth
oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="playlist-modify-public playlist-modify-private"
)

# Obtenir l'URL d'authentification
auth_url = oauth.get_authorize_url()
print(f"\n🔗 Ouvrir cette URL dans votre navigateur:\n{auth_url}")

# Vous serez redirigé vers localhost - copier la URL complète
redirect_url = input("\n📋 Coller la URL complète de redirection:\n")

# Échanger le code contre un token
code = oauth.parse_response_code(redirect_url)
token_info = oauth.get_access_token(code)

refresh_token = token_info["refresh_token"]
access_token = token_info["access_token"]

print(f"\n✅ REFRESH_TOKEN : {refresh_token}")
print(f"✅ ACCESS_TOKEN (optionnel) : {access_token}")
print("\n⚠️  Sauvegarder le REFRESH_TOKEN - il ne s'affichera plus!")
```

2. Remplacer `YOUR_CLIENT_ID` et `YOUR_CLIENT_SECRET` par vos credentials
3. Exécuter : `python auth_spotify.py`
4. Ouvrir l'URL dans le navigateur et autoriser l'application
5. Copier la URL de redirection complète
6. Coller la URL - le script affichera le **REFRESH_TOKEN**

### **ÉTAPE 4 : Obtenir l'ID de la Playlist**

#### Option A : Créer une playlist manuellement

1. Sur Spotify (web ou app), créer une playlist : `Radio des Îles`
2. Ouvrir la playlist
3. Cliquer sur le menu (⋯) → Copier le lien de la playlist
4. L'URL ressemblera à : `https://open.spotify.com/playlist/XXXXXXXXXXXXXXX`
5. Copier l'ID (la partie `XXXXXXXXXXXXXXX`)

#### Option B : Utiliser le script pour lister vos playlists

```python
#!/usr/bin/env python3
"""
Lister vos playlists pour obtenir l'ID
"""
import spotipy
from spotipy.oauth2 import SpotifyOAuth

oauth = SpotifyOAuth(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    redirect_uri="http://localhost:8888/callback"
)

sp = spotipy.Spotify(auth_manager=oauth)
results = sp.current_user_playlists()

print("\n🎵 Vos playlists :")
for playlist in results["items"]:
    print(f"  • {playlist['name']} → ID: {playlist['id']}")
```

---

## 🔐 Configurer les secrets GitHub

### **Accédérer aux secrets du repository**

1. Aller sur votre repository GitHub
2. Settings → Secrets and variables → Actions
3. Cliquer "New repository secret"

### **Ajouter les 4 secrets requius**

| Secret | Valeur | Source |
|--------|--------|--------|
| `SPOTIPY_CLIENT_ID` | Votre Client ID | Spotify Developer Dashboard |
| `SPOTIPY_CLIENT_SECRET` | Votre Client Secret | Spotify Developer Dashboard |
| `SPOTIPY_REFRESH_TOKEN` | Votre Refresh Token | Script `auth_spotify.py` |
| `SPOTIFY_PLAYLIST_ID` | ID de votre playlist | Lien de la playlist Spotify |

**Exemple d'ajout d'un secret :**

```
Secret name: SPOTIPY_CLIENT_ID
Secret value: [coller votre Client ID]
[Cliquer "Add secret"]
```

Répéter pour les 4 secrets.

---

## ✅ Vérifier l'installation

### **1. Vérifier le workflow dans GitHub**

1. Aller sur repository → Actions
2. Voir "🎶 Spotify Radio Playlist Update"
3. Les 3 exécutions programmées doivent être listées (cron jobs)

### **2. Déclencher une exécution manuelle**

1. Aller sur la page du workflow
2. Cliquer "Run workflow" → "Run workflow"
3. Attendre 2-3 minutes
4. Voir le résultat dans les logs

### **3. Vérifier la playlist Spotify**

Ouvrir votre playlist `Radio des Îles` :
- La playlist doit être vidée et remplie de nouvelles tracks
- La composition dépend de l'heure (mode morning/midday/evening)

---

## 🔍 Horaires d'exécution

Le workflow s'exécute automatiquement à :

```
🌅 06:00 UTC → Mode MORNING (zouk doux, classique caribéenne)
☀️ 12:00 UTC → Mode MIDDAY (kompa, zouk festif)
🌙 18:00 UTC → Mode EVENING (gwoka, léwoz, chill)
```

**⚠️ Attention :** Les horaires sont en UTC. Adapter si votre serveur/zone horaire est différente.

---

## 🐛 Dépannage

### **Erreur : "Missing required Spotify credentials"**

✅ **Solution :** Vérifier que les 4 secrets sont ajoutés dans GitHub Settings

### **Erreur : "Invalid refresh token"**

✅ **Solution :** 
- Regénérer le refresh token avec `auth_spotify.py`
- Mettre à jour le secret GitHub

### **Erreur : "Playlist not found"**

✅ **Solution :**
- Vérifier l'ID de playlist dans le secret
- Vérifier que la playlist existe dans Spotify

### **Playlist ne change pas**

✅ **Solutions :**
1. Attendre l'heure programmée (06:00, 12:00, 18:00 UTC)
2. Ou déclencher manuellement (Run workflow)
3. Consulter les logs du workflow pour les erreurs

### **Vérifier les logs du workflow**

1. Actions → Workflow
2. Cliquer sur la dernière exécution
3. "Run Spotify Playlist Engine" → Voir les logs détaillés

---

## 📝 Notes personnalisables

### Changer les horaires d'exécution

Éditer [.github/workflows/spotify-radio.yml](.github/workflows/spotify-radio.yml) :

```yaml
schedule:
  - cron: '0 6 * * *'   # Heure 1
  - cron: '0 12 * * *'  # Heure 2
  - cron: '0 18 * * *'  # Heure 3
```

Format cron : `minute heure jour mois jour_semaine`
- `0 6 * * *` = 06:00 chaque jour
- `0 12 * * *` = 12:00 chaque jour

### Changer la taille de la playlist

Éditer `playlist_engine.py`, fonction `build_playlist()` :

```python
track_uris = build_playlist(sp, mode, target_size=20, playlist_id=playlist_id)
#                                              ↑
#                                       Nombre de tracks
```

### Ajouter des genres musicaux

Éditer `playlist_engine.py`, section `RADIO_CONFIG` :

```python
RADIO_CONFIG = {
    RadioMode.MORNING: {
        "queries": [
            "zouk doux",
            "classical caribean",
            "new query here"  # ← Ajouter ici
        ],
        ...
    }
}
```

---

## 🎯 Prochaines étapes

1. ✅ Ajouter les secrets GitHub (voir plus haut)
2. ✅ Vérifier l'exécution manuelle
3. ✅ Attendre les premières exécutions programmées
4. ✅ Écouter votre playlist radio "Radio des Îles" ! 🎵

---

**Questions ou problèmes ?**
Consulter les logs du workflow GitHub Actions pour plus de détails.

