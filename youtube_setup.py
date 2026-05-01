#!/usr/bin/env python3
"""
YouTube Data API v3 — OAuth Setup
Génère youtube_token.json via le flux OAuth browser.

Pré-requis :
  1. Google Cloud Console → APIs & Services → Enable "YouTube Data API v3"
  2. Create OAuth 2.0 Client ID (type: Desktop app)
  3. Download client_secret.json → poser dans ce dossier
  4. python3 youtube_setup.py

Le token est sauvegardé dans youtube_token.json.
Pour GitHub Actions, copier le contenu dans le secret YOUTUBE_TOKEN_JSON.
"""

import json
import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

CLIENT_SECRET = Path("client_secret.json")
TOKEN_PATH    = Path("youtube_token.json")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


def run_oauth():
    if not CLIENT_SECRET.exists():
        print(f"Fichier introuvable : {CLIENT_SECRET}")
        print()
        print("Étapes :")
        print("  1. https://console.cloud.google.com/apis/library/youtube.googleapis.com")
        print("     → Enable 'YouTube Data API v3'")
        print("  2. https://console.cloud.google.com/apis/credentials")
        print("     → Create Credentials → OAuth client ID → Desktop app")
        print("  3. Télécharge le JSON → renomme en client_secret.json")
        print("  4. Relance : python3 youtube_setup.py")
        sys.exit(1)

    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        if creds.valid:
            print(f"Token déjà valide : {TOKEN_PATH}")
            _show_next_steps()
            return
        if creds.expired and creds.refresh_token:
            print("Token expiré — rafraîchissement...")
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json())
            print(f"Token rafraîchi : {TOKEN_PATH}")
            _show_next_steps()
            return

    print("Ouverture du navigateur pour l'authentification YouTube...")
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_PATH.write_text(creds.to_json())
    print(f"Token sauvegardé : {TOKEN_PATH}")
    _show_next_steps()


def _show_next_steps():
    print()
    print("Pour GitHub Actions, ajoute ce secret :")
    print("  Nom   : YOUTUBE_TOKEN_JSON")
    print(f"  Valeur: (copie le contenu de {TOKEN_PATH})")
    print()
    token_data = json.loads(TOKEN_PATH.read_text())
    print(f"  token_uri   : {token_data.get('token_uri', '')}")
    print(f"  client_id   : {token_data.get('client_id', '')[:30]}...")
    print(f"  scopes      : {token_data.get('scopes', [])}")


if __name__ == "__main__":
    run_oauth()
