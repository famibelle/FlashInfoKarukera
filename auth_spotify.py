#!/usr/bin/env python3
"""
Spotify OAuth Authentication Helper
Obtient les credentials nécessaires pour autoriser le accès à Spotify

Utilisation :
  1. Remplacer CLIENT_ID et CLIENT_SECRET par vos credentials Spotify
  2. Exécuter : python auth_spotify.py
  3. Ouvrir l'URL affichée dans votre navigateur
  4. Autoriser l'application
  5. Copier la URL de redirection
  6. Coller la URL dans le terminal
  7. Copier le REFRESH_TOKEN généré
"""

import os
import sys
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

# ============================================================================
# CHARGER LES CREDENTIALS DEPUIS LE FICHIER .env
# ============================================================================

load_dotenv()

CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

# ============================================================================

SCOPE = "playlist-modify-public playlist-modify-private"


def get_refresh_token():
    """
    Interactively obtain a refresh token from Spotify OAuth
    """
    print("\n" + "=" * 70)
    print("🎵 SPOTIFY OAUTH AUTHENTICATION")
    print("=" * 70)

    # Validate credentials
    if not CLIENT_ID or not CLIENT_SECRET:
        print("\n❌ ERROR: CLIENT_ID or CLIENT_SECRET not found in .env file!")
        print("\n📝 Steps:")
        print("  1. Create a .env file in the project root")
        print("  2. Add these lines:")
        print("     SPOTIPY_CLIENT_ID=your_client_id")
        print("     SPOTIPY_CLIENT_SECRET=your_client_secret")
        print("  3. Save the .env file")
        print("  4. Run the script again")
        sys.exit(1)

    # Create OAuth manager
    oauth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    )

    # Get authorization URL
    auth_url = oauth.get_authorize_url()

    print("\n🔗 STEP 1: Open this URL in your browser:")
    print(f"\n   {auth_url}\n")
    print("📋 STEP 2: You will be redirected to a localhost URL")
    print("⚠️  Copy the ENTIRE URL from your browser's address bar\n")

    # Get redirect URL from user
    redirect_url = input("🔐 Paste the complete redirect URL here:\n> ").strip()

    if not redirect_url:
        print("\n❌ ERROR: No URL provided")
        sys.exit(1)

    try:
        # Exchange authorization code for token
        code = oauth.parse_response_code(redirect_url)

        if not code:
            print("\n❌ ERROR: Could not parse authorization code from URL")
            sys.exit(1)

        # Get token
        token_info = oauth.get_access_token(code)

        refresh_token = token_info.get("refresh_token")
        access_token = token_info.get("access_token")
        expires_in = token_info.get("expires_in", 3600)

        if not refresh_token:
            print("\n❌ ERROR: No refresh token received")
            sys.exit(1)

        # Display results
        print("\n" + "=" * 70)
        print("✅ AUTHENTICATION SUCCESSFUL!")
        print("=" * 70)

        print("\n🔑 CREDENTIALS FOR GITHUB SECRETS:\n")

        print("SPOTIPY_CLIENT_ID:")
        print(f"  {CLIENT_ID}\n")

        print("SPOTIPY_CLIENT_SECRET:")
        print(f"  {CLIENT_SECRET}\n")

        print("SPOTIPY_REFRESH_TOKEN:")
        print(f"  {refresh_token}\n")

        print("⏱️  Token expires in:", f"{expires_in // 3600} hours")

        print("\n📌 Next steps:")
        print("  1. Go to your GitHub repository")
        print("  2. Settings → Secrets and variables → Actions")
        print("  3. Add 3 new secrets above")
        print("  4. Add SPOTIFY_PLAYLIST_ID (see SETUP_SPOTIFY_RADIO.md)")

        return refresh_token

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n⚠️  Troubleshooting:")
        print("  • Make sure you authorized the app")
        print("  • Check that the URL is complete and correct")
        print("  • Try again")
        sys.exit(1)


if __name__ == "__main__":
    get_refresh_token()
