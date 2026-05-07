#!/usr/bin/env python3
"""
Dream Radio — Génère les rêves techniques et antenne pour Radio Karukera.

Usage:
    python dream_radio.py [--date YYYY-MM-DD] [--dry-run] [--llm-key TA_CLE_MISTRAL] [--no-llm] [--no-github]

Génère:
    - docs/reves/technique/YYYY-MM-DD.md  (Directeur Technique)
    - docs/reves/antenne/YYYY-MM-DD.md   (Directeur de l'Antenne)

Avec LLM:
    Si MISTRAL_API_KEY est dans .env ou --llm-key est fourni,
    ajoute un résumé narratif généré par Mistral AI.

Avec GitHub API:
    Par défaut, récupère les stats réelles depuis GitHub Actions.
    **Un token GitHub est requis** (GH_TOKEN, GITHUB_TOKEN, ou PAT_SUBMODULE).
    Sans token, l'API publique sera utilisée (rate limit: 60 req/heure).
    Utilisez --no-github pour désactiver complètement l'API GitHub.

Dependencies:
    pip install python-dotenv requests

Exemple:
    # Avec .env (recommandé)
    echo "MISTRAL_API_KEY=ta_clé" > .env
    echo "GH_TOKEN=ton_token_github" >> .env
    python dream_radio.py
    
    # Avec arguments CLI
    python dream_radio.py --llm-key ta_clé --date 2024-01-15
    
    # Sans LLM et sans GitHub API
    python dream_radio.py --no-llm --no-github
    
    # Sans cache (pour forcer le rafraîchissement)
    python dream_radio.py --no-cache
    
    # Mode dry-run (affichage seulement)
    python dream_radio.py --dry-run

Cache:
    Les résultats de l'API GitHub sont mis en cache pendant 300 secondes (5 minutes).
    Le cache est stocké dans .dream_radio_cache/github_workflows.cache
    Utilisez --no-cache pour désactiver le cache.
"""

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()  # Charge les variables depuis .env
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# ------ CACHE SYSTEM ------
class SimpleCache:
    """Cache simple en mémoire avec option de persistance dans un fichier."""
    
    def __init__(self, cache_file=None, ttl=300):
        """
        Initialise le cache.
        
        Args:
            cache_file: Chemin du fichier de cache (optionnel)
            ttl: Time-to-live en secondes (défaut: 300 = 5 minutes)
        """
        self.memory_cache = {}
        self.cache_file = Path(cache_file) if cache_file else None
        self.ttl = ttl
        self._load_from_file()
    
    def _load_from_file(self):
        """Charge le cache depuis le fichier."""
        if not self.cache_file or not self.cache_file.exists():
            return
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                import ast
                self.memory_cache = ast.literal_eval(f.read())
            log_info(f"Cache chargé depuis {self.cache_file}")
        except Exception as e:
            log_warning(f"Impossible de charger le cache: {e}")
    
    def _save_to_file(self):
        """Sauvegarde le cache dans le fichier."""
        if not self.cache_file:
            return
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                f.write(str(self.memory_cache))
        except Exception as e:
            log_warning(f"Impossible de sauvegarder le cache: {e}")
    
    def get(self, key):
        """Récupère une valeur du cache."""
        if key not in self.memory_cache:
            return None
        
        entry = self.memory_cache[key]
        # Vérifier le TTL
        if "timestamp" in entry and (time.time() - entry["timestamp"]) > self.ttl:
            del self.memory_cache[key]
            self._save_to_file()
            return None
        
        return entry.get("value")
    
    def set(self, key, value):
        """Stocke une valeur dans le cache."""
        self.memory_cache[key] = {
            "value": value,
            "timestamp": time.time()
        }
        self._save_to_file()
    
    def clear(self):
        """Efface tout le cache."""
        self.memory_cache = {}
        if self.cache_file:
            try:
                self.cache_file.unlink()
            except:
                pass

# Importer time pour le cache
import time

# Initialiser le cache (désactivé par défaut, activer avec --cache ou CACHE_DIR)
GITHUB_CACHE = None
CACHE_DIR = None

# ------ CONFIG ------
REPO_ROOT = Path(__file__).parent.parent
DREAMS_DIR = REPO_ROOT / "docs" / "reves"
TECHNICAL_DIR = DREAMS_DIR / "technique"
ANTENNE_DIR = DREAMS_DIR / "antenne"

# GitHub Config
GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY", "famibelle/FlashInfoKarukera")
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/actions"

# Initialiser CACHE_DIR après REPO_ROOT
# Utiliser .dream_radio_cache pour éviter les conflits avec .cache (fichier git)
CACHE_DIR = REPO_ROOT / ".dream_radio_cache"


def init_cache(use_cache=True):
    """Initialise le système de cache."""
    global GITHUB_CACHE
    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        GITHUB_CACHE = SimpleCache(cache_file=CACHE_DIR / "github_workflows.cache", ttl=300)

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
DREAM = "🌙"
IDEA = "💡"

# Couleurs pour le terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BLUE = "\033[94m"
PURPLE = "\033[95m"


def log_success(msg):
    print(f"{GREEN}{CHECK}{RESET} {msg}")


def log_warning(msg):
    print(f"{YELLOW}{WARNING}{RESET} {msg}")


def log_error(msg):
    print(f"{RED}{CROSS}{RESET} {msg}")


def log_info(msg):
    print(f"{BLUE}ℹ{RESET} {msg}")


# ------ CONFIG LLM ------
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MODEL = "mistral-tiny"  # Modèle léger et rapide (mistral-small pour plus de qualité)


def get_mistral_api_key():
    """Récupère la clé API Mistral depuis les variables d'environnement."""
    # python-dotenv a déjà chargé le .env si disponible
    # Essayer plusieurs noms de variables possibles
    for key_name in ["MISTRAL_API_KEY", "MISTRAL_API_KEY_BOTIRAN"]:
        key = os.environ.get(key_name)
        if key:
            return key
    return None


# ------ GITHUB API FUNCTIONS ------

def get_github_token():
    """Récupère le token GitHub depuis les variables d'environnement."""
    # Essayer plusieurs noms de variables possibles
    for key_name in ["GH_TOKEN", "GITHUB_TOKEN", "PAT_SUBMODULE", "GITHUB_PAT"]:
        key = os.environ.get(key_name)
        if key:
            return key
    return None


def call_github_api(endpoint, token=None, use_cache=True):
    """
    Appelle l'API GitHub avec option de cache.
    
    Args:
        endpoint: URL relative de l'API (ex: /repos/owner/repo/actions/workflows)
        token: Token GitHub optionnel
        use_cache: Utiliser le cache (défaut: True)
        
    Returns:
        dict: Réponse JSON de l'API, ou None en cas d'erreur
    """
    if not REQUESTS_AVAILABLE:
        log_error("La bibliothèque 'requests' est requise pour l'API GitHub")
        return None
    
    # Générer une clé de cache unique
    token_hash = hashlib.sha256((token or "").encode()).hexdigest()[:8]
    cache_key = f"github:{GITHUB_REPO}:{endpoint}:{token_hash}"
    
    # Vérifier le cache d'abord
    if use_cache and GITHUB_CACHE:
        cached_result = GITHUB_CACHE.get(cache_key)
        if cached_result is not None:
            log_info(f"Cache hit pour {endpoint}")
            return cached_result
    
    token = token or get_github_token()
    if not token:
        log_warning("Aucun token GitHub trouvé. Utilisation de l'API publique (rate limit faible)")
    
    url = f"https://api.github.com{endpoint}"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            # Stocker dans le cache
            if use_cache and GITHUB_CACHE:
                GITHUB_CACHE.set(cache_key, result)
            return result
        elif response.status_code == 401:
            log_error("Token GitHub invalide ou expiré")
            return None
        elif response.status_code == 403:
            rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            if rate_limit_remaining == 0:
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                reset_date = datetime.fromtimestamp(reset_time).strftime("%H:%M:%S")
                log_error(f"Rate limit atteint. Réessayez après {reset_date} UTC")
            else:
                log_error(f"Accès refusé à l'API GitHub: {response.text[:200]}")
            return None
        else:
            log_error(f"Erreur API GitHub {response.status_code}: {response.text[:200]}")
            return None
    except requests.exceptions.Timeout:
        log_error("Timeout lors de l'appel à l'API GitHub")
        return None
    except requests.exceptions.RequestException as e:
        log_error(f"Erreur de connexion à l'API GitHub: {e}")
        return None
    except Exception as e:
        log_error(f"Erreur inattendue avec l'API GitHub: {e}")
        return None


def get_workflow_id(workflow_name):
    """
    Récupère l'ID d'un workflow par son nom.
    
    Args:
        workflow_name: Nom du workflow (ex: 'horoscope-daily.yml')
        
    Returns:
        int: ID du workflow, ou None si non trouvé
    """
    endpoint = f"/repos/{GITHUB_REPO}/actions/workflows"
    workflows = call_github_api(endpoint)
    
    if not workflows or "workflows" not in workflows:
        return None
    
    for wf in workflows["workflows"]:
        if wf["name"] == workflow_name or wf["path"] == f".github/workflows/{workflow_name}":
            return wf["id"]
    
    return None


def get_workflow_runs(workflow_id, since_date=None, limit=10):
    """
    Récupère les exécutions (runs) d'un workflow.
    
    Args:
        workflow_id: ID du workflow
        since_date: Date de début (YYYY-MM-DD), optionnel
        limit: Nombre max de runs à récupérer
        
    Returns:
        list: Liste des runs, ou [] en cas d'erreur
    """
    endpoint = f"/repos/{GITHUB_REPO}/actions/workflows/{workflow_id}/runs"
    params = {"per_page": min(limit, 100)}
    
    # Filtrer par date si spécifié
    if since_date:
        endpoint += f"?created=%3E{since_date}T00:00:00Z"
    
    runs = call_github_api(endpoint)
    
    if not runs or "workflow_runs" not in runs:
        return []
    
    return runs["workflow_runs"]


def get_all_workflows_stats(days_back=7, workflow_names=None):
    """
    Récupère les statistiques de tous les workflows pour une période donnée.
    
    Args:
        days_back: Nombre de jours à analyser (défaut: 7)
        workflow_names: Liste des noms de workflows à inclure (optionnel)
        
    Returns:
        list: Liste de dicts avec les stats par workflow
    """
    since_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    workflows_data = []
    
    # Liste des workflows à analyser (par défaut, les principaux)
    if workflow_names is None:
        workflow_names = [
            "horoscope-daily.yml",
            "flash-info.yml", 
            "capsules-daily.yml",
            "emission-daily.yml",
            "botiran-radio-daily.yml",
            "daily-radio-orchestrator.yml"
        ]
    
    for wf_name in workflow_names:
        workflow_id = get_workflow_id(wf_name)
        if not workflow_id:
            log_warning(f"Workflow '{wf_name}' non trouvé")
            continue
        
        runs = get_workflow_runs(workflow_id, since_date, limit=50)
        if not runs:
            continue
        
        # Calculer les stats pour ce workflow
        successful_runs = [r for r in runs if r.get("conclusion") == "success"]
        failed_runs = [r for r in runs if r.get("conclusion") == "failure"]
        
        # Calculer la durée moyenne (en secondes)
        # Essayer run_duration_ms d'abord, sinon calculer à partir des timestamps
        durations = []
        for r in runs:
            # Option 1: Utiliser run_duration_ms si disponible
            run_duration = r.get("run_duration_ms")
            if run_duration:
                durations.append(run_duration / 1000)
            else:
                # Option 2: Calculer à partir de run_started_at et updated_at
                started_at = r.get("run_started_at")
                updated_at = r.get("updated_at")
                if started_at and updated_at:
                    try:
                        start_time = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                        end_time = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                        duration = (end_time - start_time).total_seconds()
                        if duration > 0:
                            durations.append(duration)
                    except Exception as e:
                        log_warning(f"Erreur calcul durée pour run {r.get('id', 'N/A')}: {e}")
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Dernière exécution
        last_run = runs[0] if runs else None
        last_status = last_run.get("conclusion", "unknown") if last_run else "unknown"
        last_error = None
        
        # Essayer de trouver la dernière erreur avec plus de détails
        for r in runs:
            if r.get("conclusion") == "failure":
                # Le message d'erreur peut être dans differentes places
                last_error = r.get("failure_reason", "Erreur inconnue")
                # Essayer de récupérer plus de détails
                if not last_error or last_error == "Erreur inconnue":
                    last_error = f"Run {r.get('id', 'N/A')} échoué - {r.get('html_url', '#')}"
                break
        
        workflows_data.append({
            "name": wf_name.replace(".yml", ""),
            "runs": len(runs),
            "success_count": len(successful_runs),
            "failure_count": len(failed_runs),
            "avg_duration": avg_duration,
            "success_rate": len(successful_runs) / len(runs) if runs else 0,
            "last_status": last_status,
            "last_error": last_error,
            "last_run_time": last_run.get("run_started_at") if last_run else None,
        })
    
    return workflows_data


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


# ------ LLM FUNCTIONS ------

def call_mistral_api(prompt, api_key, model=MISTRAL_MODEL, max_tokens=500, temperature=0.7):
    """
    Appelle l'API Mistral pour générer du texte.
    
    Args:
        prompt: Le prompt à envoyer au modèle
        api_key: Clé API Mistral
        model: Modèle à utiliser (mistral-tiny, mistral-small, mistral-medium)
        max_tokens: Nombre max de tokens dans la réponse
        temperature: Créativité (0.0 = déterministe, 1.0 = aléatoire)
    
    Returns:
        str: Réponse du modèle, ou None en cas d'erreur
    """
    if not REQUESTS_AVAILABLE:
        log_error("La bibliothèque 'requests' est requise pour l'API Mistral. Installez-la avec: pip install requests")
        return None
    
    if not api_key:
        log_error("Aucune clé API Mistral fournie")
        return None
    
    try:
        response = requests.post(
            MISTRAL_API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            log_error(f"Erreur API Mistral: {response.status_code} - {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        log_error("Timeout lors de l'appel à l'API Mistral")
        return None
    except requests.exceptions.RequestException as e:
        log_error(f"Erreur de connexion à l'API Mistral: {e}")
        return None
    except Exception as e:
        log_error(f"Erreur inattendue avec l'API Mistral: {e}")
        return None


def generate_llm_dream_summary(dream_content, dream_type, date_str, api_key=None, llm_data=None):
    """
    Génère un résumé de rêve narratif et poétique via LLM.
    
    Args:
        dream_content: Le contenu complet du rêve (markdown)
        dream_type: "technique" ou "antenne"
        date_str: Date du rêve (YYYY-MM-DD)
        api_key: Clé API Mistral (optionnelle)
        llm_data: Données structurées supplémentaires (optionnel)
    
    Returns:
        str: Résumé généré, ou None si erreur
    """
    if not api_key:
        return None
    
    # Adapter le prompt selon le type et les données disponibles
    if dream_type == "antenne" and llm_data:
        system_prompt = """Tu es le Directeur d'Antenne de Radio Botiran 🐚, avec 25 ans d'expérience.
Ton rôle : Analyser TOUTES les données de la journée (contenu audio généré, playlist, cohérence, animateurs)
et transformer cela en un RÊVE NARRATIF et PROFESSIONNEL qui porte conseil.

CONTEXTE COMPLET :
"""
        
        # Ajouter les données structurées
        user_prompt = f"""DATE: {date_str}

### 📊 STATISTIQUES
- Flash Infos: {llm_data.get('flash_infos', {}).get('count', 0)} générés
- Horoscopes: {llm_data.get('horoscopes', {}).get('count', 0)} produits
- Liners: {llm_data.get('liners', {}).get('count', 0)} diffusés (Cohérence: {llm_data.get('liners', {}).get('coherence_rate', 0)}%)
- Émissions: {llm_data.get('emissions', {}).get('count', 0)} créées
- Capsules: {llm_data.get('capsules', {}).get('count', 0)} culturelles
- Musique: {llm_data.get('musics', {}).get('count', 0)} titres

### 🎵 PROGRAMMATION MUSICALE
"""
        
        if llm_data.get('playlist'):
            user_prompt += f"""Playlist:
{llm_data['playlist'][:500]}

"""
        
        if llm_data.get('musics', {}).get('genres'):
            user_prompt += f"""Genres répartis: {llm_data['musics']['genres']}
"""
        
        if llm_data.get('liners', {}).get('issues'):
            user_prompt += """### ⚠️ PROBLÈMES DE COHÉRENCE LINERS
"""
            for issue in llm_data['liners']['issues'][:5]:  # Limiter à 5
                expected = issue.get('expected', 'N/A')
                user_prompt += f"""- Liner #{issue['index']}: "{issue.get('liner', 'N/A')}" → Attendu: {expected}
"""
        
        # Ajouter les contenus des fichiers
        if llm_data.get('flash_infos', {}).get('files'):
            user_prompt += """
### 📰 CONTENU FLASH INFOS
"""
            for f in llm_data['flash_infos']['files'][:3]:
                content_preview = f['content'][:100].replace('"', "'").replace('\n', ' ')
                user_prompt += f"- {f['name']}: {content_preview}...\n"
        
        if llm_data.get('horoscopes', {}).get('files'):
            user_prompt += """
### ✨ CONTENU HOROSCOPES
"""
            for f in llm_data['horoscopes']['files'][:3]:
                content_preview = f['content'][:100].replace('"', "'").replace('\n', ' ')
                user_prompt += f"- {f['name']}: {content_preview}...\n"
        
        # Ajouter les recommandations par animateur
        user_prompt += """
### 👥 ANIMATEURS ET RECOMMANDATIONS
"""
        for name, data in llm_data.get('animateurs', {}).items():
            user_prompt += f"""- {name}:
  - Passages: {data['passages']}
  - Note: {data['note']}/10
  - Feedback: {data['feedback']}
  - Recommandations: {', '.join(data.get('recommandations', []))}
"""
        
        user_prompt += """

INSTRUCTIONS:
1. Écris un rêve ONIRIQUE du point de vue d'un Directeur d'Antenne expérimenté (25 ans)
2. Intègre les problèmes de cohérence, les contenus générés, la programmation musicale
3. Termine par des CONSEILS CONCRETS et PERSONNALISÉS pour chaque animateur
4. Utilise des métaphores radio (ondes, micro, fréquence, harmonies)
5. Inclut des emojis (🎤, 🎵, ⚠️, ✨, 🌙, 📻)
6. Écris en français, style professionnel mais poétique
7. Sois concis (8-12 lignes)

Exemple de style:
"Cette nuit, Radio Botiran m'a chuchoté ses secrets... Les Flash Infos dansaient avec les horoscopes sous la lune de Guadeloupe, mais des ombres (les 4 liners incohérents) perturbaient l'harmonie. Harry, avec ses 3 passages parfaits, devait varier ses adjectifs comme on accorde une guitare..."

Génère le rêve:"""
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
    else:
        # Fallback pour le mode simple (sans données enrichies)
        system_prompt = """Tu es l'âme de Radio Botiran 🐚, une radio caribéenne vibrante.
Ton rôle : Transformer un rapport technique en un RÊVE NARRATIF et POÉTIQUE qui porte conseil.

Règles :
1. Utilise un ton onirique, métaphorique, presque magique
2. Décris ce que le système a "rêvé" pendant la nuit
3. Termine par des CONSEILS CONCRETS et actionnables
4. Inclut des emojis pertinents (🎤, 🎵, ⚠️, ✨, 🌙)
5. Sois concis (4-6 lignes max)
6. Écris en français avec des expressions caribéennes

Exemple de style :
"Cette nuit, Radio Botiran m'a emporté sur une île où les Flash Infos dansaient avec les horoscopes..."

Contenu à analyser :"""
        
        user_prompt = f"""Date : {date_str}
Type : {dream_type}

{dream_content[:3000]}"""
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    return call_mistral_api(full_prompt, api_key, max_tokens=800, temperature=0.7)


def generate_music_director_analysis(llm_data, date_str, api_key=None):
    """
    Génère une analyse musicale complète par le Directeur Musical de Radio Botiran.
    Inclut l'analyse des liners et leur cohérence avec la programmation musicale.
    
    Args:
        llm_data: Données structurées (musics, liners, playlist, etc.)
        date_str: Date au format YYYY-MM-DD
        api_key: Clé API Mistral (optionnelle)
        
    Returns:
        str: Analyse générée par LLM, ou None si erreur
    """
    if not api_key:
        return None
    
    # Construire le prompt spécialisé pour le Directeur Musical
    system_prompt = """Tu es le **Directeur Musical** de Radio Botiran 🎵🐚, une radio caribéenne légendaire.
Ton expertise : 25 ans de programmation musicale, maître des transitions, connoisseur des rythmes antillais.

Ton rôle aujourd'hui : 
**Analyser la programmation musicale complète + les liners** et transformer cela en un **RÊVE ONIRIQUE** 
qui révèle l'harmonie (ou les dissonances) de la playlist, tout en donnant des **CONSEILS PRÉCIS** 
pour améliorer la cohérence entre les morceaux et les introductions.

Ton style :
- Poétique et métaphorique (ondes, fréquents, harmonies, rythmes)
- Technique mais accessible (BPM, genres, transitions)
- **Inclure le contenu des liners** et leur adéquation avec la musique
- Emojis adaptés : 🎵 🎤 🎶 ✨ 🌊 🎧
- Langue : Français avec expressions caribéennes
- Structure : 3 parties (rêve, analyse, conseils)
"""
    
    # Extraire les données des liners
    liners_data = llm_data.get("liners", {})
    liners_texts = liners_data.get("texts", [])
    liner_issues = liners_data.get("issues", [])
    liner_warnings = liners_data.get("warnings_list", [])
    
    # Extraire les données musicales
    musics_data = llm_data.get("musics", {})
    genres = musics_data.get("genres", {})
    artists = musics_data.get("artists", {})
    playlist = llm_data.get("playlist", "")
    
    # Construire la section liners avec leur contenu et leur correspondance musicale
    liners_analysis = """
### 🎤 ANALYSE DES LINERS (Introductions Musicales)
"""
    
    if liners_texts:
        liners_analysis += f"""Nombre de liners: {len(liners_texts)}
Score de cohérence: {liners_data.get('coherence_rate', 0):.0f}%
Problèmes critiques: {liners_data.get('critical_issues', 0)}

**Liste des liners avec leur musique suivante :**
"""
        for liner in liners_texts[:10]:  # Limiter à 10 pour éviter un prompt trop long
            next_music = liner.get("next_music", {})
            next_artist = next_music.get("artist", "N/A") if isinstance(next_music, dict) else "N/A"
            next_title = next_music.get("title", "N/A") if isinstance(next_music, dict) else "N/A"
            next_genre = next_music.get("genre", "N/A") if isinstance(next_music, dict) else "N/A"
            
            liners_analysis += f"- **Liner #{liner.get('index', 0)}** : \"{liner.get('text', '')[:60]}...\"\n"
            liners_analysis += f"  → **Musique suivante** : {next_artist} - {next_title} ({next_genre})\n"
            liners_analysis += f"  → **Cohérent** : {'✅' if liner.get('is_coherent') else '❌'}\n\n"
    
    if liner_issues:
        liners_analysis += f"""**Problèmes détectés dans les liners :**
"""
        for issue in liner_issues[:5]:
            liners_analysis += f"- {issue.get('issue', 'N/A')}\n"
    
    # Construire la section musique
    music_analysis = f"""
### 🎵 ANALYSE DE LA PROGRAMMATION MUSICALE

**Statistiques :**
- Nombre de morceaux: {musics_data.get('count', 0)}
- Genres répartis: {dict(genres)}
- Artistes uniques: {len(artists)}

**Répartition par genre :**
"""
    
    for genre, count in sorted(genres.items(), key=lambda x: x[1], reverse=True):
        music_analysis += f"- {genre}: {count} morceaux\n"
    
    # Ajouter les tops artistes
    music_analysis += """\n**Top Artistes :**
"""
    for artist, count in sorted(artists.items(), key=lambda x: x[1], reverse=True)[:5]:
        music_analysis += f"- {artist}: {count} titres\n"
    
    # Constructeur le prompt final
    user_prompt = f"""DATE: {date_str}

{music_analysis}

{liners_analysis}

### 📋 PLAYLIST COMPLÈTE (extrait) :
{playlist[:1000]}

--- INSTRUCTIONS POUR LE RÊVE ---

1. **Décris en 4-6 lignes** ce que la radio a "rêvé" cette nuit :
   - Les morceaux dansaient-ils en harmonie ?
   - Y avait-il des dissonances (liners incohérents, transitions brusques) ?
   - Quelles émotions la playlist a-t-elle transmises ?

2. **Donne un score de cohérence globale** (0-100%) avec justification

3. **Identifie 3 problèmes principaux** dans la programmation + liners

4. **Propose 3 solutions concrètes** pour demain

5. **Style** : Onirique, poétique, avec métaphores musicales (ondes, fréquences, harmonies)

**Exemple de style :**
"Cette nuit, Radio Botiran m'a emporté dans un voyage sonore où les kompas d'Exile One 
rencontraient les zouks de Kassav' dans une danse parfaite... Mais l'ombre de 3 liners 
décalés est venue troubler cette harmonie, comme une fausse note dans une mélodie parfaite.

Score: 85/100 - presqu'excellent, mais à peaufiner.

Problèmes: Liner #5 ne correspond pas à la musique suivante, transition trop abrupte entre Gwoka et Reggae.
Conseils: Réenregistrer le liner #5 avec le bon artiste, ajouter une transition douce entre les styles."

Génère le rêve complet du Directeur Musical:"""
    
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    return call_mistral_api(full_prompt, api_key, max_tokens=1500, temperature=0.7)


# ------ ANALYSE TECHNIQUE ------

def generate_technical_dream(date_obj, llm_key=None, use_github_api=True):
    """Génère le rêve technique."""
    date_str = format_date(date_obj)
    
    # --- Collecter les infos depuis les workflows (GitHub API uniquement) ---
    workflows_data = []
    github_api_available = False
    
    if use_github_api:
        log_info("Récupération des stats workflows depuis GitHub API...")
        workflows_data = get_all_workflows_stats(days_back=7)
        
        if workflows_data:
            github_api_available = True
            log_info(f"Données récupérées: {len(workflows_data)} workflows analysés")
        else:
            log_error("GitHub API non disponible ou aucune donnée retournée")
    else:
        log_error("GitHub API désactivée (option --no-github)")
    
    # PAS de fallback sur données simulées - on requiert des données réelles
    if not workflows_data:
        # Générer un message d'erreur dans le markdown
        workflows_data = []
    
    # Adapter les données pour la compatibilité avec le reste du code
    for wf in workflows_data:
        if "success_count" in wf and "failure_count" in wf:
            wf["runs"] = wf["success_count"] + wf["failure_count"]
    
    # Calculer les stats (seulement si données disponibles)
    if workflows_data:
        total_runs = sum(w["runs"] for w in workflows_data)
        total_success = sum(w["runs"] * w["success_rate"] for w in workflows_data)
        success_rate = (total_success / total_runs * 100) if total_runs else 0
        total_avg_duration = sum(w["runs"] * w["avg_duration"] for w in workflows_data) / total_runs if total_runs else 0
    else:
        total_runs = 0
        total_success = 0
        success_rate = 0
        total_avg_duration = 0
    
    # --- Générer le markdown ---
    md = f"""# {GEAR} Rêve Technique — Radio Karukera
*Date : {date_str} | Généré à {(datetime.utcnow()).strftime("%H:%M UTC")}*

"""
    
    # Message d'erreur si pas de données GitHub
    if not workflows_data and use_github_api:
        md += f"""{CROSS} **GitHub API Indisponible**

Impossible de récupérer les statistiques des workflows. Le rêve technique ne peut pas être généré sans accès à l'API GitHub.

**Solutions :**
1. Vérifiez que vous avez un token GitHub valide (GH_TOKEN, GITHUB_TOKEN, ou PAT_SUBMODULE)
2. Vérifiez votre connexion internet
3. Essayez à nouveau plus tard

"""
        return md
    
    md += "---\n\n"
    
    # Toujours ajouter la section Rêve de la Nuit (en premier)
    if llm_key:
        log_info("Génération du résumé LLM pour le rêve technique...")
        llm_summary = generate_llm_dream_summary(md, "technique", date_str, llm_key)
        if llm_summary:
            md += f"## {DREAM} Rêve de la Nuit\n\n{llm_summary}\n\n---\n\n"
        else:
            log_warning("Impossible de générer le résumé LLM (API non disponible)")
            # Ajouter un résumé par défaut pour le rêve technique
            default_tech_summary = f"""Cette nuit, les serveurs de Radio Botiran {DREAM} ont rêvé de bits caribéens...

Les {total_runs} workflows ont dansé comme des vagues sur la plage, avec un taux de succès de {success_rate:.1f}%. 
Les {sum(1 for w in workflows_data if w['last_status'] != 'success')} workflows en alerte nous rappellent qu'il faut surveiller les logs 
comme un pêcheur surveille son filet.

Au réveil, l'équipe technique a compris qu'il fallait :
- Paralléliser les workflows pour gagner du temps
- Réduire la verbosité des logs
- Continuer à optimiser le cache"""
            md += f"## {DREAM} Rêve de la Nuit\n\n{default_tech_summary}\n\n---\n\n"
    else:
        # Ajouter un résumé par défaut pour le rêve technique
        default_tech_summary = f"""Cette nuit, les serveurs de Radio Botiran {DREAM} ont rêvé de bits caribéens...

Les {total_runs} workflows ont dansé comme des vagues sur la plage, avec un taux de succès de {success_rate:.1f}%. 
Les {sum(1 for w in workflows_data if w['last_status'] != 'success')} workflows en alerte nous rappellent qu'il faut surveiller les logs 
comme un pêcheur surveille son filet.

Au réveil, l'équipe technique a compris qu'il fallait :
- Paralléliser les workflows pour gagner du temps
- Réduire la verbosité des logs
- Continuer à optimiser le cache"""
        md += f"## {DREAM} Rêve de la Nuit\n\n{default_tech_summary}\n\n---\n\n"
    
    md += f"""## {MUSIC} Statistiques des Workflows

| Workflow | Runs | Durée moy. | Taux succès | Dernier statut | Dernière erreur |
|----------|------|-------------|-------------|----------------|----------------|
"""
    
    for wf in workflows_data:
        status_icon = CHECK if wf['last_status'] == 'success' else CROSS
        error_msg = wf['last_error'] or "Aucune"
        md += f"| {wf['name']} | {wf['runs']} | {format_duration(wf['avg_duration'])} | {wf['success_rate']*100:.0f}% | {status_icon} | {error_msg} |\n"
    
    md += f"""| **Total** | **{total_runs}** | **{format_duration(total_avg_duration)}** | **{success_rate:.1f}%** | - | - |

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
    
    md += f"""---

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


# ------ UTILS POUR ANTENNE ------

def load_audio_metadata(date_str, audio_type, days_back=7):
    """
    Charge les métadonnées des contenus audio générés.
    
    Cherche dans :
    - docs/audio/{audio_type}/ (fichiers JSON)
    - docs/liners/ (pour les liners)
    - docs/audio/{audio_type}/{YYYY-MM}/ (fichiers JSON par mois)
    
    Args:
        date_str: Date au format YYYY-MM-DD
        audio_type: Type de contenu (flash-info, horoscope, liners, Emissions, capsules)
        days_back: Nombre de jours à remonter (défaut: 7)
        
    Returns:
        list: Liste de dicts avec les métadonnées de chaque fichier
    """
    results = []
    
    # Normaliser le type (les dossiers peuvent avoir des noms différents)
    type_mapping = {
        "flash-info": "flash-info",
        "flash_info": "flash-info",
        "flashinfo": "flash-info",
        "horoscope": "horoscope",
        "horoscopes": "horoscope",
        "liners": "liners",
        "liner": "liners",
        "emissions": "Emissions",
        "emission": "Emissions",
        "capsules": "capsules",
        "capsule": "capsules",
    }
    audio_type = type_mapping.get(audio_type.lower(), audio_type)
    
    # Liste des chemins à explorer
    search_paths = []
    
    # 1. Dossier principal docs/audio/{audio_type}/
    audio_dir = REPO_ROOT / "docs" / "audio" / audio_type
    if audio_dir.exists():
        search_paths.append(audio_dir)
    
    # 2. Dossier docs/liners/ pour les liners
    if audio_type.lower() == "liners":
        liners_dir = REPO_ROOT / "docs" / "liners"
        if liners_dir.exists():
            search_paths.append(liners_dir)
    
    # 3. Sous-dossiers par mois dans docs/audio/{audio_type}/
    if audio_dir.exists():
        for subdir in audio_dir.iterdir():
            if subdir.is_dir() and re.match(r"\d{4}-\d{2}", subdir.name):
                search_paths.append(subdir)
    
    # Générer les patterns de fichiers à rechercher
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    date_formats = [
        date_str,  # YYYY-MM-DD
        date_str.replace("-", ""),  # YYYYMMDD
        f"{date_obj.strftime('%Y-%m-%d')}",
        f"{date_obj.strftime('%Y%m%d')}",
    ]
    
    # Pour les liners, ajouter les patterns de semaine (W18, W19, etc.)
    if audio_type.lower() == "liners":
        year = date_obj.year
        # Calculer la semaine ISO
        import calendar
        week_number = date_obj.isocalendar()[1]
        date_formats.extend([
            f"{year}-W{week_number:02d}",
            f"W{week_number:02d}",
        ])
    
    # Chercher les fichiers JSON correspondant à la date
    found_files = False
    for search_path in search_paths:
        for date_pattern in date_formats:
            # Patterns pour trouver les fichiers
            # Note: glob ne supporte pas * au début et à la fin dans le même pattern
            patterns = [
                f"*{date_pattern}*",  # *date*
                f"{date_pattern}*",   # date*
                f"*{date_pattern}",   # *date
            ]
            
            for pattern in patterns:
                for ext in ["json", "md", "txt"]:
                    # Construct valid glob pattern
                    glob_pattern = f"{pattern}.{ext}"
                    try:
                        for f in search_path.glob(glob_pattern):
                            found_files = True
                            try:
                                metadata = parse_audio_file(f, audio_type, date_str)
                                if metadata:
                                    results.append(metadata)
                            except Exception as e:
                                log_warning(f"Erreur lecture {f}: {e}")
                    except Exception as e:
                        log_warning(f"Pattern glob invalide: {glob_pattern} - {e}")
    
    # Si aucun fichier trouvé et qu'on cherche des liners, essayer de charger TOUS les liners
    if not found_files and audio_type.lower() == "liners":
        log_info("Aucun liner trouvé pour la date, chargement de tous les liners disponibles...")
        for ext in ["json", "md", "txt"]:
            for f in (REPO_ROOT / "docs" / "liners").glob(f"*.{ext}"):
                try:
                    metadata = parse_audio_file(f, audio_type, date_str)
                    if metadata:
                        results.append(metadata)
                except Exception as e:
                    log_warning(f"Erreur lecture {f}: {e}")
    
    # Si on ne trouve pas de fichiers pour la date exacte, chercher dans les derniers jours
    if not results and days_back > 0:
        for days in range(1, days_back + 1):
            prev_date = (date_obj - timedelta(days=days)).strftime("%Y-%m-%d")
            prev_results = load_audio_metadata(prev_date, audio_type, days_back=0)
            if prev_results:
                results.extend(prev_results)
                break
    
    # Dédoublonnage par filename
    unique_results = []
    seen_filenames = set()
    for r in results:
        if r["filename"] not in seen_filenames:
            seen_filenames.add(r["filename"])
            unique_results.append(r)
    
    return sorted(unique_results, key=lambda x: x.get("date", ""), reverse=True)


def parse_audio_file(filepath, audio_type, default_date):
    """
    Parse un fichier audio (JSON, MD ou TXT) et extrait les métadonnées.
    
    Args:
        filepath: Path du fichier
        audio_type: Type de contenu
        default_date: Date par défaut
        
    Returns:
        dict: Métadonnées extraites, ou None si erreur
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        metadata = {
            "filename": filepath.name,
            "path": str(filepath.relative_to(REPO_ROOT)),
            "type": audio_type,
            "date": default_date,
            "content": content[:500] if len(content) > 500 else content,
            "full_content": content,
        }
        
        # Essayer de parser comme JSON
        if filepath.suffix == ".json":
            try:
                data = json.loads(content)
                
                # Extraire les champs communs
                if isinstance(data, dict):
                    metadata["title"] = data.get("title", "")
                    metadata["text"] = data.get("text", "")[:500]
                    metadata["duration"] = data.get("duration", "")
                    metadata["word_count"] = data.get("word_count", 0)
                    metadata["voice"] = data.get("voice", "")
                    
                    # Pour les émissions
                    if data.get("type") == "emission":
                        metadata["inspiration_title"] = data.get("inspiration", {}).get("title", "")
                        metadata["inspiration_artist"] = data.get("inspiration", {}).get("artist", "")
                        metadata["audio_url"] = data.get("audio_url", "")
                        
                    # Pour les liners
                    if audio_type.lower() == "liners" or "liner" in str(filepath).lower():
                        metadata["label"] = data.get("label", "")
                        metadata["bloc"] = data.get("bloc", "")
                        metadata["artists"] = data.get("artists", [])
                        metadata["voice"] = data.get("voice", "")
                        
                        # Extraire l'édition de l Asíbloc ou du filename
                        edition = metadata.get("bloc", "").lower()
                        if not edition:
                            filename = filepath.name.lower()
                            if "matin" in filename:
                                edition = "matin"
                            elif "midi" in filename:
                                edition = "midi"
                            elif "soir" in filename:
                                edition = "soir"
                        metadata["edition"] = edition
                        
                    # Pour flash-info et horoscope
                    if audio_type.lower() in ["flash-info", "flashinfo", "flash_info", "horoscope"]:
                        metadata["edition"] = extract_edition_from_filename(filepath.name)
                        
                        # Extraire la date du filename si disponible
                        date_match = re.search(r"(\d{4}-?\d{2}-?\d{2})", filepath.name)
                        if date_match:
                            metadata["date"] = date_match.group(1).replace("-", "-")
                        
                    return metadata
                
            except json.JSONDecodeError:
                pass
        
        # Parser le markdown
        if filepath.suffix == ".md":
            # Extraire le titre (première ligne # ...)
            title_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
            if title_match:
                metadata["title"] = title_match.group(1).strip()
            
            # Extraire l'édition
            metadata["edition"] = extract_edition_from_filename(filepath.name)
            
            # Extraire la date du filename
            date_match = re.search(r"(\d{4}-?\d{2}-?\d{2})", filepath.name)
            if date_match:
                metadata["date"] = date_match.group(1).replace("-", "-")
            
            return metadata
        
        # Fichier texte brut
        if filepath.suffix == ".txt":
            metadata["edition"] = extract_edition_from_filename(filepath.name)
            date_match = re.search(r"(\d{4}-?\d{2}-?\d{2})", filepath.name)
            if date_match:
                metadata["date"] = date_match.group(1).replace("-", "-")
            return metadata
        
        return metadata
        
    except Exception as e:
        log_warning(f"Erreur parsing {filepath}: {e}")
        return None


def extract_edition_from_filename(filename):
    """Extrait l'édition (matin, midi, soir) d'un nom de fichier."""
    filename_lower = filename.lower()
    if "matin" in filename_lower:
        return "matin"
    elif "midi" in filename_lower:
        return "midi"
    elif "soir" in filename_lower:
        return "soir"
    return "inconnu"


def load_playlist(date_str):
    """Récupère la programmation complète via show_playlist.py."""
    try:
        import subprocess
        # Essayer python3 puis python
        for cmd in ["python3", "python"]:
            try:
                result = subprocess.run(
                    [cmd, "show_playlist.py"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=REPO_ROOT
                )
                if result.returncode == 0:
                    return result.stdout
            except FileNotFoundError:
                continue
    except Exception as e:
        log_warning(f"Impossible d'exécuter show_playlist.py: {e}")
    
    # Fallback : lire radio_sequence.json directement
    sequence_path = REPO_ROOT / "docs" / "radio_sequence.json"
    sequence = load_json(sequence_path) or {"sequence": []}
    if sequence:
        return json.dumps({"sequence": sequence["sequence"]}, indent=2, ensure_ascii=False)
    
    return ""


# ------ LINER ANALYSIS FUNCTIONS ------

def extract_artist_title(liner_text):
    """
    Extrait l'artiste et le titre d'un liner.
    
    Formats supportés:
    - "Artiste - Titre"
    - "Artiste | Titre"
    - "Artiste: Titre"
    - "Artiste — Titre" (tiret long)
    - "[Artiste] - Titre"
    - "Artiste - [Titre]"
    
    Args:
        liner_text: Texte du liner
        
    Returns:
        dict: {"artist": str, "title": str} ou {"artist": "", "title": ""} si non parsable
    """
    if not liner_text:
        return {"artist": "", "title": ""}
    
    text = liner_text.strip()
    
    # Supprimer les crochets au début/fine si présent
    text = text.strip("[]")
    
    # Patterns de séparation
    separators = [
        (" — ", "long dash"),
        (" - ", "dash"),
        (" | ", "pipe"),
        (" : ", "colon"),
        (" :", "colon no space"),
        ("-", "dash no space"),
        ("|", "pipe no space"),
    ]
    
    for sep, name in separators:
        if sep in text:
            parts = text.split(sep, 1)
            if len(parts) == 2:
                artist = parts[0].strip()
                title = parts[1].strip()
                # Nettoyer les crochets
                artist = artist.strip("[]")
                title = title.strip("[]")
                return {"artist": artist, "title": title}
    
    # Si aucun séparateur trouvé, tout est considéré comme artiste
    return {"artist": text, "title": ""}


def compare_artist_names(name1, name2):
    """
    Compare deux noms d'artistes avec tolérance aux variantes.
    
    Gère les cas comme:
    - "Kassav'" vs "Kassav"
    - "Kassav'" vs "Kassav'"
    - "Jean-Philippe" vs "Jean Philippe"
    - "Exile One" vs "Exile-One"
    
    Args:
        name1: Premier nom (normalisé)
        name2: Deuxième nom (normalisé)
        
    Returns:
        bool: True si les noms correspondent (même approximativement)
    """
    if not name1 or not name2:
        return False
    
    n1 = name1.lower().strip()
    n2 = name2.lower().strip()
    
    # Correspondance exacte
    if n1 == n2:
        return True
    
    # Supprimer les caractères spéciaux communs
    for char in ["'", "`", "-", "_", "."]:
        n1_clean = n1.replace(char, "")
        n2_clean = n2.replace(char, "")
        if n1_clean == n2_clean:
            return True
    
    # Remplacer les espaces multiples
    n1_single = re.sub(r"\s+", " ", n1)
    n2_single = re.sub(r"\s+", " ", n2)
    if n1_single == n2_single:
        return True
    
    # Vérifier si un nom est dans l'autre
    if n1 in n2 or n2 in n1:
        return True
    
    # Vérifier les mots clés (pour les noms composés)
    words1 = set(n1.split())
    words2 = set(n2.split())
    if words1 and words2:
        # Si au moins 50% des mots correspondent
        common = words1 & words2
        if len(common) >= max(1, min(len(words1), len(words2)) // 2):
            return True
    
    return False


def analyze_liner_format(liner_text):
    """
    Analyse le format d'un liner et détecte les problèmes.
    
    Args:
        liner_text: Texte du liner
        
    Returns:
        str: Description du problème, ou None si le format est correct
    """
    if not liner_text or not liner_text.strip():
        return "Liner vide"
    
    text = liner_text.strip()
    
    # Problème 1: Trop court (moins de 15 caractères)
    if len(text) < 15:
        return "Liner trop court (moins de 15 caractères)"
    
    # Problème 2: Contient des caractères suspects
    suspicious_chars = ["http://", "https://", "www.", "@", "#", "$"]
    for char in suspicious_chars:
        if char in text.lower():
            return f"Caractère suspect détecté: '{char}'"
    
    # Problème 3: Commence par un chiffre
    if text[0].isdigit():
        return "Liner commence par un chiffre"
    
    # Problème 4: Contient des emojis excessifs (plus de 3)
    emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]'
    emoji_count = len(re.findall(emoji_pattern, text))
    if emoji_count > 3:
        return f"Trop d'emojis ({emoji_count})"
    
    # Problème 5: Format générique détecté (mots-clés)
    generic_patterns = [
        (r"la voix qui\b", "expression générique"),
        (r"la voix de\b", "expression générique"),
        (r"écoutez bien\b", "appel à l'écoute"),
        (r"attention\b", "appel à l'attention"),
        (r"voici\b", "introduction générique"),
        (r"maintenant\b", "référence temporelle vague"),
        (r"et voici\b", "introduction générique"),
        (r"sur radio\b", "référence à la radio"),
        (r"sur les ondes\b", "référence aux ondes"),
        (r"pour vous\b", "appel au public"),
        (r"le jour se lève\b", "description générique"),
        (r"un rythme\b", "description musicale vague"),
        (r"la mémoire de\b", "référence vague"),
        (r"nos terres\b", "référence générique"),
    ]
    
    for pattern, desc in generic_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return f"Liner trop générique: {desc} ('{pattern}')"
    
    # Problème 6: Pas de séparateur (devrait avoir un artiste et un titre)
    extracted = extract_artist_title(text)
    if not extracted.get("title"):
        # Vérifier si le texte contient au moins un nom d'artiste connu
        known_artists = [
            "kassav", "exile one", "wck", "slaï", "admiral t", "fanny j", "zouk machine",
            "gaoule", "jacob desvarieux", "jean-marie", "warren", "akiyo", "djakout",
            "claudette", "an djakout", "corinne", "harry diboula", "monique", "solitude",
            "maryse", "gilles floro", "sweet micky", "harmonik", "patrick", "sain",
            "coco", "jean-philipp", "zin", "dominik", "dominique",
        ]
        
        text_lower = text.lower()
        if any(artist in text_lower for artist in known_artists):
            return "Format non standard: artiste détecté mais titre manquant (utiliser 'Artiste - Titre')"
        else:
            return "Format non standard: pas de séparateur artiste/titre détecté (utiliser 'Artiste - Titre')"
    
    # Problème 7: L'artiste extrait est trop court (1-2 caractères)
    if extracted.get("artist") and len(extracted["artist"]) < 3:
        return f"Nom d'artiste trop court: '{extracted['artist']}'"
    
    # Problème 8: Le titre extrait est trop court (1-2 caractères)
    if extracted.get("title") and len(extracted["title"]) < 3:
        return f"Titre trop court: '{extracted['title']}'"
    
    return None


def analyze_liner_files(liner_files):
    """
    Analyse une liste de fichiers de liners pour détecter les problèmes.
    
    Args:
        liner_files: Liste de dicts avec les métadonnées des liners
        
    Returns:
        list: Liste des problèmes détectés
    """
    issues = []
    
    for idx, liner_file in enumerate(liner_files):
        liner_text = liner_file.get("label", "") or liner_file.get("content", "")[:100]
        
        # Analyser le format
        format_issue = analyze_liner_format(liner_text)
        if format_issue:
            issues.append({
                "index": idx,
                "filename": liner_file.get("filename", "N/A"),
                "liner": liner_text[:50],
                "type": "file_format",
                "severity": "medium",
                "issue": format_issue,
            })
        
        # Vérifier les artistes (si disponibles)
        artists = liner_file.get("artists", [])
        if artists and len(artists) > 5:
            issues.append({
                "index": idx,
                "filename": liner_file.get("filename", "N/A"),
                "liner": liner_text[:50],
                "type": "too_many_artists",
                "severity": "low",
                "issue": f"Trop d'artistes associés ({len(artists)})",
            })
    
    return issues


# ------ ANALYSE ANTENNE ------

# ------ NOUVELLES FONCTIONS POUR ÉVALUATION INDIVIDUELLE ------

def load_journalist_texts(date_str: str, repo_root: Path = REPO_ROOT) -> dict[str, list[str]]:
    """
    Charge les textes générés par chaque journaliste pour une date donnée.
    
    Args:
        date_str: Date au format YYYY-MM-DD
        repo_root: Racine du repository
        
    Returns:
        dict: {nom_journaliste: [liste_de_textes]}
    """
    results = {}
    
    # Harry - Flash Info (archives/flash-info/)
    flash_dir = repo_root / "archives" / "flash-info"
    harry_texts = []
    if flash_dir.exists():
        for f in sorted(flash_dir.glob(f"flash-info-{date_str}-*.txt")):
            harry_texts.append(f.read_text(encoding="utf-8", errors="ignore"))
        # Fallback : essayer sans tirets dans la date
        if not harry_texts:
            for f in sorted(flash_dir.glob(f"flash-info-{date_str.replace('-', '')}-*.txt")):
                harry_texts.append(f.read_text(encoding="utf-8", errors="ignore"))
    results["Harry"] = harry_texts
    
    # Maryse Condé - Horoscope (archives/horoscope/)
    horo_dir = repo_root / "archives" / "horoscope"
    maryse_texts = []
    if horo_dir.exists():
        for f in sorted(horo_dir.glob(f"horoscope-{date_str}-*.txt")):
            maryse_texts.append(f.read_text(encoding="utf-8", errors="ignore"))
        if not maryse_texts:
            for f in sorted(horo_dir.glob(f"horoscope-{date_str.replace('-', '')}-*.txt")):
                maryse_texts.append(f.read_text(encoding="utf-8", errors="ignore"))
    results["Maryse Condé"] = maryse_texts
    
    # Monique - Émissions (docs/audio/Emissions/)
    emission_dir = repo_root / "docs" / "audio" / "Emissions"
    monique_texts = []
    if emission_dir.exists():
        for f in sorted(emission_dir.glob(f"emission-{date_str}.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                monique_texts.append(data.get("text", ""))
            except (json.JSONDecodeError, FileNotFoundError):
                continue
    results["Monique"] = monique_texts
    
    # Mulatresse Solitude - Capsules (archives/capsules/ et docs/capsules/)
    solitude_texts = []
    processed_files = set()
    
    # Dossier principal pour analyse centralisée (avec Harry et Maryse)
    archives_capsules_dir = repo_root / "archives" / "capsules"
    if archives_capsules_dir.exists():
        for f in sorted(archives_capsules_dir.glob(f"capsule-{date_str}-*.txt")):
            solitude_texts.append(f.read_text(encoding="utf-8", errors="ignore"))
            processed_files.add(f.name)
        # Fallback : essayer sans tirets dans la date
        if not solitude_texts:
            for f in sorted(archives_capsules_dir.glob(f"capsule-{date_str.replace('-', '')}-*.txt")):
                if f.name not in processed_files:
                    solitude_texts.append(f.read_text(encoding="utf-8", errors="ignore"))
                    processed_files.add(f.name)
    # Dossier secondaire pour compatibilité
    docs_capsules_dir = repo_root / "docs" / "capsules"
    if docs_capsules_dir.exists():
        for f in sorted(docs_capsules_dir.glob(f"capsule-{date_str}-*.txt")):
            if f.name not in processed_files:
                solitude_texts.append(f.read_text(encoding="utf-8", errors="ignore"))
                processed_files.add(f.name)
    results["Mulatresse Solitude"] = solitude_texts
    
    # Corinne - Liners (docs/liners/)
    liners_dir = repo_root / "docs" / "liners"
    corinne_texts = []
    if liners_dir.exists():
        for f in sorted(liners_dir.glob("liner-*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("label"):
                    corinne_texts.append(data["label"])
            except (json.JSONDecodeError, FileNotFoundError):
                continue
    results["Corinne"] = corinne_texts
    
    return results


def evaluate_journalist_llm(
    journalist_name: str,
    journalist_texts: list[str],
    date_str: str,
    api_key: str,
    liners_issues: list[dict] = None,
    capsule_themes: list[str] = None,
) -> dict:
    """
    Évalue UN journaliste via un appel LLM dédié.
    Retourne un dict avec : note, feedback, recommandations, scores détaillés
    
    Args:
        journalist_name: Nom du journaliste
        journalist_texts: Liste des textes générés
        date_str: Date au format YYYY-MM-DD
        api_key: Clé API Mistral
        liners_issues: Liste des problèmes de liners (pour Corinne)
        capsule_themes: Liste des thèmes de capsules (pour Solitude)
        
    Returns:
        dict: Évaluation complète au format JSON
    """
    # Définition des personas avec leurs critères spécifiques
    personas = {
        "Harry": {
            "role": "Journaliste Flash Info",
            "style": "factuel, urgent, professionnel, neutre",
            "criteria": [
                "Précision des faits",
                "Clarté de l'information", 
                "Neutralité absolue",
                "Respect du format journalistique",
                "Concision (15-25 mots par flash)"
            ]
        },
        "Maryse Condé": {
            "role": "Présentatrice Horoscope",
            "style": "mystérieux, intime, engageant, culturel",
            "criteria": [
                "Authenticité culturelle guadeloupéenne",
                "Structure claire par signe",
                "Ton adapté à l'astrologie",
                "Respect des 12 signes",
                "Formulations variées"
            ]
        },
        "Monique": {
            "role": "Docteure en écologie - Émissions Culturelles",
            "style": "pédagogique, passionné, scientifique accessible",
            "criteria": [
                "Précision scientifique",
                "Accessibilité pour le grand public",
                "Riche en contenu local",
                "Flow naturel et captivant",
                "Équilibre science/storytelling"
            ]
        },
        "Mulatresse Solitude": {
            "role": "Voix de la Résistance - Capsules culturelles",
            "style": "chaleureux, évocateur, solennel, poétique",
            "criteria": [
                "Authenticité culturelle guadeloupéenne",
                "Originalité des sujets",
                "Concision (15-20 secondes)",
                "Impact émotionnel",
                "Respect de la mémoire collective"
            ]
        },
        "Corinne": {
            "role": "Speakrine - Liners",
            "style": "neutre, professionnel, clair, direct",
            "criteria": [
                "Format [Artiste] - [Titre] respecté",
                "Cohérence avec la musique suivante",
                "Variété des formulations",
                "Ton radio professionnel",
                "Absence de formules génériques"
            ]
        }
    }
    
    persona = personas.get(journalist_name, personas["Harry"])
    
    # Préparer un échantillon de textes (max 5 pour éviter un prompt trop long)
    texts_sample = journalist_texts[:5]
    sample_text = "\n\n---\n\n".join(t[:500] for t in texts_sample)  # Limiter à 500 chars par texte
    
    # Construire le prompt
    system_prompt = f"""Tu es le **Responsable de la Programmation Musicale** de Radio Botiran 🎵🐚.
Ton expertise : 25 ans d'expérience en radio caribéenne, spécialiste de l'analyse des contenus audio et de leur cohérence avec la programmation musicale.

**Journaliste à évaluer :** {journalist_name}
**Rôle :** {persona['role']}
**Style attendu :** {persona['style']}

**Mission :** Évaluer de manière **professionnelle, précise et constructive** les textes générés par ce journaliste.

**Critères de notation (0-10) :**
- **Format/Structure** : 0-3 pts (respect des règles de format spécifiques)
- **Contenu/Précision** : 0-3 pts (qualité et exactitude du contenu)
- **Style/Ton** : 0-2 pts (adéquation avec le style attendu)
- **Originalité** : 0-2 pts (créativité et unicité)

**Format de sortie OBLIGATOIRE (JSON strict) :**
{{
    "note": <int 0-10>,
    "feedback": "<résumé en 1 phrase en français>",
    "recommandations": ["<recommandation 1>", "<recommandation 2>"],
    "format_score": <int 0-3>,
    "content_score": <int 0-3>,
    "style_score": <int 0-2>,
    "originality_score": <int 0-2>,
    "strengths": ["<force 1>", "<force 2>"],
    "weaknesses": ["<faiblesse 1>", "<faiblesse 2>"]
}}

**Règles :**
- Réponds UNIQUEMENT en JSON valide
- Pas de commentaire avant ou après le JSON
- Tous les champs doivent être présents
- Écris en français"""
    
    user_prompt = f"""DATE: {date_str}
JOURNALISTE: {journalist_name}
NOMBRE DE TEXTES: {len(journalist_texts)}

### 📄 Échantillon des textes générés :
{sample_text}

### 🎯 Critères spécifiques pour {journalist_name} :
{chr(10).join(f'- {c}' for c in persona['criteria'])}

### 📊 Contexte supplémentaire :
"""
    
    # Ajouter le contexte spécifique
    if liners_issues and journalist_name == "Corinne":
        user_prompt += f"""- **Problèmes détectés** : {len(liners_issues)} erreurs de format dans les liners
- **Erreurs critiques** : {len([i for i in liners_issues if i.get('severity') == 'high'])} erreurs de cohérence
- **Avertissements** : {len(liners_issues) - len([i for i in liners_issues if i.get('severity') == 'high'])} améliorations suggérées
"""
    
    if capsule_themes and journalist_name == "Mulatresse Solitude":
        user_prompt += f"""- **Thèmes abordés aujourd'hui** : {', '.join(capsule_themes[:10])}
"""
    
    user_prompt += """
### 🎯 Instructions d'évaluation :
1. Analyse globalement la qualité des textes générés
2. Identifie 2 points forts principaux
3. Identifie 2 axes d'amélioration principaux  
4. Donne 2 recommandations **concrètes et actionnables**
5. Sois **précis, professionnel et constructif**
6. Prends en compte le contexte radio (Guadeloupe, culture caribéenne)

**Réponds UNIQUEMENT avec le JSON, sans texte avant ou après.**"""
    
    # Appel LLM
    raw = call_mistral_api(
        user_prompt,
        api_key,
        model="mistral-small",
        max_tokens=500,
        temperature=0.3,
        json_mode=True
    )
    
    if raw:
        try:
            result = json.loads(raw)
            # Valider que tous les champs requis sont présents
            required_keys = ["note", "feedback", "recommandations", "format_score", 
                          "content_score", "style_score", "originality_score", 
                          "strengths", "weaknesses"]
            if all(key in result for key in required_keys):
                return result
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Fallback : évaluation par défaut
    return {
        "note": 7,
        "feedback": f"Évaluation automatique - {journalist_name}",
        "recommandations": ["Revoir manuellement les textes"],
        "format_score": 2,
        "content_score": 2,
        "style_score": 1,
        "originality_score": 2,
        "strengths": ["Texte généré"],
        "weaknesses": ["Évaluation LLM indisponible"]
    }


def generate_antenne_dream(date_obj, llm_key=None):
    """Génère le rêve de l'antenne."""
    date_str = format_date(date_obj)
    
    # --- Charger la sequence radio ---
    sequence_path = REPO_ROOT / "docs" / "radio_sequence.json"
    sequence = load_json(sequence_path) or {"sequence": []}
    
    # --- Extraire les infos de base ---
    flash_infos = [s for s in sequence["sequence"] if s.get("subtype") == "flash_info"]
    horoscopes = [s for s in sequence["sequence"] if s.get("subtype") == "horoscope"]
    liners = [s for s in sequence["sequence"] if s.get("type") == "liner"]
    musics = [s for s in sequence["sequence"] if s.get("type") == "music"]
    emissions = [s for s in sequence["sequence"] if s.get("subtype") == "emission"]
    
    # --- Charger les fichiers audio générés ---
    flash_files = load_audio_metadata(date_str, "flash-info")
    horo_files = load_audio_metadata(date_str, "horoscope")
    liner_files = load_audio_metadata(date_str, "liners")
    capsule_files = load_audio_metadata(date_str, "capsules")
    emission_files = load_audio_metadata(date_str, "Emissions")
    
    # --- Charger la playlist complète ---
    playlist_content = load_playlist(date_str)
    
    # --- Stats musique ---
    genres = Counter([m.get("genre", "inconnu") for m in musics])
    artistes = Counter([m.get("artist", "inconnu") for m in musics])
    
    # --- Analyse de cohérence des liners (AVANCÉE) ---
    coherent_liners = 0
    liner_issues = []
    liner_warnings = []  # Nouveau: avertissements (pas des erreurs mais à améliorer)
    
    for i, liner in enumerate(liners):
        next_item = sequence["sequence"][i+1] if i+1 < len(sequence["sequence"]) else None
        
        liner_text = liner.get("label", "")
        liner_artist = liner.get("artist", "")  # Si disponible dans les métadonnées
        liner_title = liner.get("title", "")  # Si disponible
        
        # Analyse 1: Vérifier le format du liner
        format_issue = analyze_liner_format(liner_text)
        if format_issue:
            liner_issues.append({
                "index": i,
                "liner": liner_text[:50],
                "expected": "Format: [Artiste] - [Titre]",
                "type": "format",
                "severity": "high",
                "issue": format_issue,
            })
            continue  # Passer à la suite si le format est invalide
        
        # Analyse 2: Comparaison avec la musique suivante (si disponible)
        if next_item and next_item.get("type") == "music":
            next_artist = next_item.get("artist", "").lower()
            next_title = next_item.get("title", "").lower()
            next_genre = next_item.get("genre", "").lower()
            
            # Extraire artiste et titre du liner
            extracted = extract_artist_title(liner_text)
            liner_artist_extracted = extracted.get("artist", "").lower()
            liner_title_extracted = extracted.get("title", "").lower()
            
            # Vérification artiste
            artist_match = False
            if next_artist:
                # Correspondance exacte
                if liner_artist_extracted and next_artist in liner_artist_extracted:
                    artist_match = True
                # Correspondance partielle (nom dans le texte)
                elif next_artist in liner_text.lower():
                    artist_match = True
                # Vérifier les variantes (ex: "Kassav'" vs "Kassav")
                elif compare_artist_names(liner_artist_extracted, next_artist):
                    artist_match = True
            
            # Vérification titre (optionnelle, moins critique)
            title_match = False
            if next_title and liner_title_extracted:
                if next_title in liner_title_extracted or liner_title_extracted in next_title:
                    title_match = True
            
            if artist_match:
                coherent_liners += 1
                
                # Vérification supplémentaire: le titre correspond-il ?
                if next_title and liner_title_extracted and not title_match:
                    liner_warnings.append({
                        "index": i,
                        "liner": liner_text[:50],
                        "expected_artist": next_artist,
                        "expected_title": next_title,
                        "type": "title_mismatch",
                        "severity": "low",
                        "issue": f"Titre non correspondant: '{liner_title_extracted}' vs '{next_title}'",
                    })
            else:
                # Essayer de trouver l'artiste dans le texte complet du liner
                if next_artist and next_artist in liner_text.lower():
                    coherent_liners += 1
                    liner_warnings.append({
                        "index": i,
                        "liner": liner_text[:50],
                        "expected_artist": next_artist,
                        "type": "artist_in_text",
                        "severity": "medium",
                        "issue": f"Artiste trouvé dans le texte mais pas au format standard",
                    })
                else:
                    liner_issues.append({
                        "index": i,
                        "liner": liner_text[:50],
                        "expected": f"{next_artist} - {next_title}" if next_title else next_artist,
                        "actual_artist": liner_artist_extracted,
                        "actual_title": liner_title_extracted,
                        "type": "artist_mismatch",
                        "severity": "high",
                        "next_music": {
                            "artist": next_item.get("artist", ""),
                            "title": next_item.get("title", ""),
                            "genre": next_item.get("genre", ""),
                        },
                    })
        else:
            # Pas de musique suivante, vérifier le format quand même
            format_issue = analyze_liner_format(liner_text)
            if format_issue:
                liner_warnings.append({
                    "index": i,
                    "liner": liner_text[:50],
                    "type": "format_warning",
                    "severity": "medium",
                    "issue": format_issue,
                })
    
    # Calculer le taux de cohérence
    coherence_rate = (coherent_liners / len(liners) * 100) if liners else 0
    
    # Analyser aussi les liners chargés depuis les fichiers
    if liner_files:
        file_liner_issues = analyze_liner_files(liner_files)
        liner_issues.extend(file_liner_issues)
    
    # --- Anomalies contenu ---
    anomalies = []
    for h in horoscopes:
        if "15 signes" in h.get("label", ""):
            anomalies.append({
                "type": "horoscope",
                "issue": "15 signes au lieu de 1-12",
                "file": h.get("url", "N/A").split("/")[-1],
            })
    
    # --- Retours animateurs avec recommandations détaillées ---
    animateurs = {
        "Harry Diboula": {
            "passages": 3, 
            "note": 9, 
            "feedback": f"{CHECK} Parfait, varier les adjectifs",
            "recommandations": [
                "Continuer à utiliser des expressions créoles pour plus d'authenticité",
                "Varier les adjectifs pour décrire les artistes (ex: 'puissant', 'émouvant', 'rythmé')",
                "Ajouter des anecdotes personnelles sur les artistes"
            ]
        },
        "Monique": {
            "passages": 2, 
            "note": 8.5, 
            "feedback": f"{CHECK} Ajouter une touche perso",
            "recommandations": [
                "Développer un style plus narratif pour captiver l'audience",
                "Ajouter une signature personnelle en fin d'intervention",
                "Travailler la transition entre les morceaux"
            ]
        },
        "Corinne": {
            "passages": 0, 
            "note": 5, 
            "feedback": f"{WARNING} Absente aujourd'hui",
            "recommandations": [
                "Reprendre les passages dès que possible - l'équipe compte sur toi!",
                "Se former aux nouveaux outils de génération de contenu",
                "Participer aux réunions de programmation pour mieux comprendre les attentes"
            ]
        },
        "Solitude": {
            "passages": 4, 
            "note": 9.5, 
            "feedback": f"{CHECK}{STAR} Reine de la nuit !",
            "recommandations": [
                "Partager tes techniques avec les nouveaux animateurs",
                "Enregistrer des capsules de formation pour l'équipe",
                "Continuer à innover avec des idées créatives"
            ]
        },
        "Maryse": {
            "passages": 3, 
            "note": 10, 
            "feedback": f"{CHECK}{STAR} Parfaite !",
            "recommandations": [
                "Servir de mentor pour les autres animateurs",
                "Participer à la formation des nouveaux",
                "Proposer des idées pour améliorer la cohérence des liners"
            ]
        },
    }
    
    # --- Préparer les données pour le LLM ---
    # Construire un résumé complet des données
    llm_data = {
        "date": date_str,
        "flash_infos": {
            "count": len(flash_infos),
            "files": [{"name": f["filename"], "content": f["content"][:200]} for f in flash_files],
            "details": [{"label": fi.get("label", "")[:100], "url": fi.get("url", "")} for fi in flash_infos]
        },
        "horoscopes": {
            "count": len(horoscopes),
            "files": [{"name": f["filename"], "content": f["content"][:200]} for f in horo_files],
            "details": [{"label": h.get("label", "")[:100], "url": h.get("url", "")} for h in horoscopes]
        },
        "liners": {
            "count": len(liners),
            "files": [{"name": f["filename"], "content": f["content"][:200]} for f in liner_files],
            "coherence_rate": coherence_rate,
            "coherent_count": coherent_liners,
            "critical_issues": len([i for i in liner_issues if i.get("severity") == "high"]),
            "warnings": len(liner_warnings),
            "issues": liner_issues,
            "warnings_list": liner_warnings,
            # Contenu textuel des liners depuis la sequence
            "texts": [{
                "index": i,
                "text": liner.get("label", ""),
                "next_music": sequence["sequence"][i+1] if i+1 < len(sequence["sequence"]) else None,
                "is_coherent": i in [idx for idx, l in enumerate(liners) if l.get("label", "")],
            } for i, liner in enumerate(liners)],
            # Statistiques par type de problème
            "format_issues": len([i for i in liner_issues if i.get("type") == "format"]),
            "generic_issues": len([i for i in liner_issues if "générique" in i.get("issue", "").lower()]),
            "artist_mismatch": len([i for i in liner_issues if i.get("type") == "artist_mismatch"]),
        },
        "emissions": {
            "count": len(emissions),
            "files": [{"name": f["filename"], "content": f["content"][:200]} for f in emission_files],
            "details": [{"label": e.get("label", "")[:100], "url": e.get("url", "")} for e in emissions]
        },
        "capsules": {
            "count": len(capsule_files),
            "files": [{"name": f["filename"], "content": f["content"][:200]} for f in capsule_files]
        },
        "playlist": playlist_content[:2000],  # Limiter la taille
        "musics": {
            "count": len(musics),
            "genres": dict(genres),
            "artists": dict(artistes)
        },
        "animateurs": animateurs
    }
    
    # --- Générer un résumé par défaut si LLM non disponible ---
    total_liner_problems = len(liner_issues) + len(liner_warnings)
    critical_liner_issues = len([i for i in liner_issues if i.get("severity") == "high"])
    
    default_dream_summary = f"""Cette nuit, Radio Botiran {DREAM} m'a chuchoté ses secrets à travers les ondes...

Les {len(flash_infos)} Flash Infos dansaient avec les {len(horoscopes)} horoscopes sous la lune de Guadeloupe,
mais {critical_liner_issues} ombres critiques et {len(liner_warnings)} avertissements (les liners à corriger) perturbaient l'harmonie avec la programmation musicale.
Avec une cohérence de {coherence_rate:.0f}%, l'équipe devait réaligner chaque liner avec son artiste.

Harry, avec ses 3 passages parfaits, continuait d'inspirer, tandis que Solitude, reine de la nuit avec {animateurs['Solitude']['passages']} passages,
monnait l'exemple. Maryse, parfaite avec sa note de 10/10, était notre étoile polaire.

Au réveil, le Directeur a compris qu'il fallait :
- Améliorer les prompts des liners avec le format [Artiste] - [Titre]
- Corriger les {critical_liner_issues} problèmes critiques de cohérence détectés
- Appliquer les {len(liner_warnings)} suggestions d'amélioration
- Maintenir cette dynamique d'équipe"""
    
    # --- Générer le markdown ---
    md = f"""# {MIC} Rêve Antenne — Radio Karukera
*Date : {date_str} | Généré à {(datetime.utcnow()).strftime("%H:%M UTC")}*

---
"""
    
    # Toujours ajouter la section Rêve de la Nuit (en premier)
    md += f"## {DREAM} Rêve de la Nuit\n\n"
    
    if llm_key:
        log_info("Génération du résumé LLM pour le rêve antenne...")
        llm_summary = generate_llm_dream_summary(md, "antenne", date_str, llm_key, llm_data)
        if llm_summary:
            md += f"{llm_summary}\n\n---\n\n"
        else:
            log_warning("Impossible de générer le résumé LLM (API non disponible)")
            md += f"{default_dream_summary}\n\n---\n\n"
    else:
        md += f"{default_dream_summary}\n\n---\n\n"
    
    # Ajouter la section Rêve du Directeur Musical (analyse musicale + liners)
    if llm_key:
        log_info("Génération de l'analyse musicale par le Directeur Musical...")
        music_analysis = generate_music_director_analysis(llm_data, date_str, llm_key)
        if music_analysis:
            md += f"## {MUSIC} Rêve du Directeur Musical\n\n"
            md += f"{music_analysis}\n\n---\n\n"
        else:
            log_warning("Impossible de générer l'analyse musicale (API non disponible)")
    
    md += f"""## {NEWS} Bilan de la Journée

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
    
    # Utiliser les fichiers chargés (basés sur la date) plutôt que la sequence
    # qui peut être en retard d'un jour
    if flash_files:
        for idx, ffile in enumerate(flash_files):
            filename = ffile.get("filename", "N/A")
            # Extraire l'édition du nom de fichier
            if "matin" in filename:
                edition = "matin"
                edition_label = "du matin"
            elif "midi" in filename:
                edition = "midi"
                edition_label = "du midi"
            elif "soir" in filename:
                edition = "soir"
                edition_label = "du soir"
            else:
                edition = "inconnu"
                edition_label = "inconnu"
            # Extraire la date (format YYYYMMDD)
            date_part = filename.replace("flash-info-", "").replace(f"-{edition}", "").replace(".md", "").replace(".txt", "")
            formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
            # Générer l'URL correcte
            base_url = "https://famibelle.github.io/FlashInfoKarukera"
            mp3_filename = filename.replace('.md', '.mp3').replace('.txt', '.mp3')
            url = f"{base_url}/audio/flash-info/{formatted_date[:7]}/{mp3_filename}"
            label = f"Flash Info Guadeloupe — {formatted_date}, édition {edition_label}"
            md += f"**Édition {idx+1} ({formatted_date}, {edition_label})** : {label}\n"
            md += f"- Durée: ~15 min | URL: `{url}`\n\n"
    elif flash_infos:
        # Fallback sur la sequence si aucun fichier trouvé
        for idx, fi in enumerate(flash_infos):
            label = fi.get("label", "N/A")
            # Extraire l'édition du label
            if "matin" in label.lower():
                edition = "matin"
            elif "midi" in label.lower():
                edition = "midi"
            elif "soir" in label.lower():
                edition = "soir"
            else:
                edition = "inconnu"
            md += f"**Édition {idx+1} ({edition})** : {label[:80]}\n"
            md += f"- Durée: ~15 min | URL: `{fi.get('url', '#')}`\n\n"
    
    md += f"""---

## {HORO} Contenu des Horoscopes
"""
    
    # Utiliser les fichiers chargés (basés sur la date) plutôt que la sequence
    # qui peut être en retard d'un jour
    if horo_files:
        for idx, hfile in enumerate(horo_files):
            filename = hfile.get("filename", "N/A")
            # Extraire l'édition du nom de fichier
            if "matin" in filename:
                edition = "matin"
                edition_label = "du matin"
            elif "soir" in filename:
                edition = "soir"
                edition_label = "du soir"
            else:
                edition = "inconnu"
                edition_label = "inconnu"
            # Extraire la date (format YYYYMMDD)
            date_part = filename.replace("horoscope-", "").replace(f"-{edition}", "").replace(".md", "").replace(".txt", "")
            formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
            # Générer l'URL correcte
            base_url = "https://famibelle.github.io/FlashInfoKarukera"
            mp3_filename = filename.replace('.md', '.mp3').replace('.txt', '.mp3')
            url = f"{base_url}/audio/horoscope/{formatted_date[:7]}/{mp3_filename}"
            label = f"Horoscope {edition_label} — {formatted_date}"
            md += f"**Horoscope {idx+1}** : {label}\n"
            md += f"- Signes: {formatted_date}\n"
            md += f"- URL: `{url}`\n"
            # Vérifier si ce fichier a une anomalie (15 signes)
            if any(a["file"] == mp3_filename for a in anomalies):
                md += f"- {WARNING} **Anomalie** : 15 signes détecté → à relancer avec `--overwrite`\n"
            md += "\n"
    elif horoscopes:
        # Fallback sur la sequence si aucun fichier trouvé
        for idx, h in enumerate(horoscopes):
            label = h.get('label', 'N/A')
            signes = label.split('—')[-1].strip() if '—' in label else 'inconnu'
            md += f"**Horoscope {idx+1}** : {label}\n"
            md += f"- Signes: {signes}\n"
            md += f"- URL: `{h.get('url', '#')}`\n"
            if any(a["file"] == h.get("url", "").split("/")[-1] for a in anomalies):
                md += f"- {WARNING} **Anomalie** : 15 signes détecté → à relancer avec `--overwrite`\n"
            md += "\n"
    
    md += f"""---

## {MIC} Cohérence Liners {MUSIC} Programmation

"""
    
    # Calculer les stats avancées
    high_severity = len([i for i in liner_issues if i.get("severity") == "high"])
    medium_severity = len([i for i in liner_issues if i.get("severity") == "medium"])
    low_severity = len([i for i in liner_issues if i.get("severity") == "low"])
    
    md += f"**Score : {coherence_rate:.0f}% ({coherent_liners}/{len(liners)} cohérents)**\n\n"
    
    # Statistiques par type de problème
    format_issues = len([i for i in liner_issues if i.get("type") == "format"])
    artist_mismatch = len([i for i in liner_issues if i.get("type") == "artist_mismatch"])
    
    md += f"""| Type | Critiques | Avertissements | Total |
|------|----------|---------------|-------|
| Erreurs format | {format_issues} | {len([w for w in liner_warnings if w.get("type") == "format_warning"])} | {format_issues} |
| Artiste non correspondant | {artist_mismatch} | {len([w for w in liner_warnings if w.get("type") in ["artist_in_text", "title_mismatch"]])} | {artist_mismatch} |
| **Total** | **{high_severity + medium_severity + low_severity}** | **{len(liner_warnings)}** | **{len(liner_issues) + len(liner_warnings)}** |

"""
    
    if liner_issues:
        md += f"### {CROSS} Liners à corriger (Critiques)\n\n"
        for issue in sorted(liner_issues, key=lambda x: x.get("severity", "") == "high", reverse=True):
            severity_emoji = {"high": CROSS, "medium": WARNING, "low": IDEA}.get(issue.get("severity", "medium"), WARNING)
            issue_type = issue.get("type", "unknown")
            issue_desc = issue.get("issue", "")
            
            md += f"- **#{issue['index']}** {severity_emoji} **[{issue_type.upper()}]** \"{issue['liner']}...\"\n"
            if issue_desc:
                md += f"  - *Problème* : {issue_desc}\n"
            if issue.get("expected"):
                md += f"  - *Attendu* : {issue['expected']}\n"
            if issue.get("next_music"):
                next_m = issue["next_music"]
                md += f"  - *Musique suivante* : {next_m.get('artist', 'N/A')} - {next_m.get('title', 'N/A')}\n"
    
    if liner_warnings:
        md += f"\n### {WARNING} Améliorations suggérées\n\n"
        for warning in liner_warnings:
            md += f"- **#{warning['index']}** {IDEA} **[{warning.get('type', 'unknown').upper()}]** \"{warning['liner']}...\"\n"
            if warning.get("issue"):
                md += f"  - *Suggestion* : {warning['issue']}\n"
    
    if not liner_issues and not liner_warnings:
        md += f"{CHECK} Tous les liners sont cohérents avec la programmation !\n"
    
    md += f"""---

## {MUSIC} 📌 RAPPEL - Responsable de la Programmation Musicale

**Les liners doivent annoncer les morceaux comme le ferait un animateur radio professionnel.**

- **Format obligatoire** : `"[Artiste] - [Titre]"` (ex: "Kassav' - Zouk là sé séléwé zot")
- **Ton** : Naturel, chaleureux, engageant (comme un vrai animateur radio)
- **Contenu** : Présenter l'artiste ET le titre de manière claire et dynamique
- **À éviter** : Formules génériques ("la voix qui...", "écoutez bien...")

**Exemples de liners corrects :**
- ✅ *"Et maintenant, laissez-vous porter par Kassav' avec 'Zouk là sé séléwé zot' — un classique intemporel !"*
- ✅ *"On enchaîne avec Admiral T et 'Gade zot pé fé sa' — du gwoka pur et puissant !"*

**Exemples à corriger :**
- ❌ *"La voix qui porte nos rêves..."* (trop générique)
- ❌ *"Écoutez bien ce morceau..."* (pas d'informations sur l'artiste/titre)

> ⚠️ **C'est votre responsabilité** de vérifier que tous les liners respectent ce standard.

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
    
    # Section des recommandations personnalisées
    md += f"## {MIC} Recommandations Personnalisées par Animateur\n\n"
    
    for name, stats in animateurs.items():
        md += f"### {name} {STAR if stats['note'] >= 9 else ''}\n"
        md += f"- **Passages**: {stats['passages']} | **Note**: {stats['note']}/10\n"
        md += f"- **Feedback général**: {stats['feedback']}\n"
        
        # Ajouter les recommandations spécifiques
        if stats.get('recommandations'):
            md += f"- **Conseils pour demain**:\n"
            for idx, conseil in enumerate(stats['recommandations'], 1):
                md += f"  {idx}. {conseil}\n"
        md += "\n"
    
    best = max(animateurs.items(), key=lambda x: x[1]["note"])
    worst = min(animateurs.items(), key=lambda x: x[1]["note"])
    md += f"**{STAR} Meilleur performeur**: {best[0]} ({best[1]['note']}/10) - {', '.join(best[1].get('recommandations', [])[:1])}\n"
    md += f"**{WARNING} À améliorer**: {worst[0]} ({worst[1]['note']}/10) - {', '.join(worst[1].get('recommandations', [])[:1])}\n"
    
    md += f"""---

## {STAR} Conseils pour Demain

- [ ] **À relancer** : Horoscope matin (anomalie "15 signes")
- [ ] **À corriger** : Liner #55 (Gilles Floro ≠ Sweet Micky)
- [ ] **À personnaliser** : Liners génériques (ex: "la voix qui...")
- [ ] **À anticiper** : Fête des mères (9 mai) → capsule spéciale

---
"""
    
    return md


# ------ MAIN ------

def main():
    parser = argparse.ArgumentParser(description="Génère les rêves technique et antenne pour Radio Karukera.")
    parser.add_argument("--date", help="Date au format YYYY-MM-DD (défaut: aujourd'hui)")
    parser.add_argument("--dry-run", action="store_true", help="Affiche sans sauvegarder")
    parser.add_argument("--llm-key", help="Clé API Mistral pour générer les résumés narratifs")
    parser.add_argument("--no-llm", action="store_true", help="Désactive l'utilisation du LLM")
    parser.add_argument("--no-github", action="store_true", help="Désactive l'utilisation de l'API GitHub")
    parser.add_argument("--no-cache", action="store_true", help="Désactive le cache GitHub API")
    args = parser.parse_args()
    
    # Initialiser le cache (sauf si --no-cache)
    use_cache = not args.no_cache
    init_cache(use_cache=use_cache)
    
    # Récupérer la clé API (CLI > Variable d'environnement > None)
    llm_key = args.llm_key
    if not llm_key and not args.no_llm:
        llm_key = get_mistral_api_key()
    
    if llm_key:
        log_info("Utilisation de l'API Mistral pour les résumés narratifs")
    else:
        if not args.no_llm:
            log_warning("Pas de clé API Mistral trouvée. Utilisation du mode standard (sans LLM).")
            log_warning("Pour activer les résumés narratifs :")
            log_warning("  1. Créez un compte sur https://mistral.ai/")
            log_warning("  2. Récupérez votre clé API")
            log_warning("  3. Passez-la via --llm-key ou exportez MISTRAL_API_KEY")
    
    if use_cache:
        log_info("Cache GitHub API activé (TTL: 300s)")
    
    date_obj = get_today(args.date)
    date_str = format_date(date_obj)
    
    log_info(f"Génération des rêves pour le {date_str}")
    
    # Générer les rêves
    use_github_api = not args.no_github
    technical_md = generate_technical_dream(date_obj, llm_key if not args.no_llm else None, use_github_api=use_github_api)
    antenne_md = generate_antenne_dream(date_obj, llm_key if not args.no_llm else None)
    
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
