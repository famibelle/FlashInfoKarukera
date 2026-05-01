#!/usr/bin/env python3
"""
YouTube Music Auth Setup
Génère browser.json depuis curl_headers.txt

Utilisation :
  1. Va sur music.youtube.com (connecté), F12 → Network
  2. Filtre : youtubei/v1  →  clique sur une requête browse ou search
  3. Clic droit → Copy → Copy as cURL (bash ou cmd)
  4. Colle dans curl_headers.txt
  5. python3 ytmusic_setup.py
"""

import sys
import re
import json
import shlex
from pathlib import Path
from ytmusicapi import YTMusic

CURL_FILE    = Path("curl_headers.txt")
BROWSER_JSON = Path("browser.json")

# Headers que ytmusicapi utilise pour s'authentifier
WANTED_HEADERS = {
    "cookie", "x-goog-authuser", "authorization",
    "user-agent", "x-origin", "x-goog-visitor-id",
    "x-youtube-client-name", "x-youtube-client-version",
    "x-youtube-identity-token", "x-youtube-page-cl",
}


def _parse_curl_regex(text: str) -> dict:
    """Fallback regex quand shlex échoue (ex: quote dans une valeur de cookie)."""
    headers = {}
    # Double-quoted headers
    for m in re.finditer(r'-H\s+"([^"]+)"', text):
        key, _, val = m.group(1).partition(':')
        headers[key.strip().lower()] = val.strip()
    # Single-quoted headers — la quote fermante est suivie d'un flag ou de la fin
    for m in re.finditer(r"-H\s+'(.+?)'(?=\s+-|\s*$)", text, re.DOTALL):
        key, _, val = m.group(1).partition(':')
        headers[key.strip().lower()] = val.strip()
    # -b 'cookies' ou -b "cookies"
    for pat in [r"-b\s+'(.+?)'(?=\s+-|\s*$)", r'-b\s+"([^"]+)"']:
        m = re.search(pat, text, re.DOTALL)
        if m:
            headers['cookie'] = m.group(1)
            break
    return headers


def parse_curl(raw: str) -> dict:
    """Parse un curl (bash ou Windows cmd) et retourne les headers utiles."""
    # Joindre les continuations Windows (^) et bash (\)
    joined = re.sub(r'\^\s*\n\s*', ' ', raw)
    joined = re.sub(r'\\\s*\n\s*', ' ', joined)

    try:
        tokens = shlex.split(joined)
    except ValueError as e:
        print(f"shlex échoué ({e}) — basculement sur le parser regex...")
        return _parse_curl_regex(joined)

    headers = {}
    i = 0
    while i < len(tokens):
        tok = tokens[i]

        if tok in ('-H', '--header') and i + 1 < len(tokens):
            header = tokens[i + 1]
            if ':' in header:
                key, _, val = header.partition(':')
                headers[key.strip().lower()] = val.strip()
            i += 2

        elif tok in ('-b', '--cookie') and i + 1 < len(tokens):
            headers['cookie'] = tokens[i + 1]
            i += 2

        else:
            i += 1

    return headers


def build_browser_json(headers: dict) -> dict:
    """Construit le dict browser.json dans le format attendu par ytmusicapi."""
    result = {}
    for key, val in headers.items():
        if key in WANTED_HEADERS:
            # ytmusicapi veut les clés en Title-Case (Cookie, X-Goog-AuthUser…)
            title_key = '-'.join(w.capitalize() for w in key.split('-'))
            result[title_key] = val
    return result


if not CURL_FILE.exists():
    print(f"Fichier introuvable : {CURL_FILE}")
    print()
    print("Crée curl_headers.txt avec le cURL copié depuis music.youtube.com")
    print("(Network → requête youtubei/v1/browse → Copy as cURL)")
    sys.exit(1)

raw = CURL_FILE.read_text(encoding='utf-8')
print(f"Lecture de {CURL_FILE} ({len(raw)} caractères)...")

headers = parse_curl(raw)
print(f"Headers parsés : {list(headers.keys())}")

# Vérifier les champs obligatoires
missing = []
if 'cookie' not in headers:
    missing.append('cookie')
if 'x-goog-authuser' not in headers:
    missing.append('x-goog-authuser')

if missing:
    print(f"❌ Headers manquants : {missing}")
    print("   → Assure-toi d'avoir copié une requête youtubei/v1/browse ou search")
    sys.exit(1)

browser_data = build_browser_json(headers)
BROWSER_JSON.write_text(json.dumps(browser_data, indent=2), encoding='utf-8')
print(f"✅ {BROWSER_JSON} généré ({len(browser_data)} entrées)")

# Vérifier que ytmusicapi accepte le fichier
try:
    yt = YTMusic(str(BROWSER_JSON))
    print("✅ Authentification YouTube Music OK")
    print()
    print("Lance maintenant :")
    print("  python3 playlist_engine.py")
except Exception as e:
    print(f"⚠️  browser.json généré mais ytmusicapi signale : {e}")
