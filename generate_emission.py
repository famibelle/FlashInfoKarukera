#!/usr/bin/env python3
"""
generate_emission.py

Génère une émission radio culturelle de 3 minutes en français (monologue).
  - Sélectionne 1 élément de chacun des 5 fichiers _ref.md
  - Utilise un morceau de la playlist comme inspiration
  - Texte généré par LLM Mistral (monologue structuré en 5 paragraphes)
  - TTS Voxtral (fr_marie_*) avec tons variés par paragraphe
  - Sortie : docs/audio/Emissions/emission-YYYY-MM-DD.mp3 + .json

Usage:
    python generate_emission.py
    python generate_emission.py --verbose
    python generate_emission.py --dry-run          # texte seul, pas de TTS
"""

import argparse
import json
import os
import random
import subprocess
import sys
import tempfile
from datetime import date, datetime
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent))
from tts_utils import tts_call, normalize_for_tts

# ── Config ──────────────────────────────────────────────────────────────────

PROMPTS_DIR = Path(__file__).parent / "private" / "prompts"
SOURCE_FILES = [
    PROMPTS_DIR / "kreyol_resistance_symbol_ref.md",
    PROMPTS_DIR / "faune_guadeloupe_ref.md",
    PROMPTS_DIR / "flore_guadeloupe_ref.md",
    PROMPTS_DIR / "lieux_spirituels_ref.md",
    PROMPTS_DIR / "histoire_guadeloupe_ref.md",
]
OUTPUT_DIR = Path("docs/audio/Emissions")

# Voix Marie avec tons variés (disponibles dans Voxtral)
TTS_VOICE_BASE = "fr_marie_"

MISTRAL_MODEL = "mistral-large-latest"

# ── Sélection aléatoire ────────────────────────────────────────────────────

def _select_random_lines_from_file(filepath: Path, num_lines: int = 1) -> list[str]:
    """Sélectionne aléatoirement N lignes de tableau Markdown d'un fichier _ref.md."""
    header_keywords = ['famille', 'nom créole', 'nom français', 'nom scientifique',
                       'sacré', 'dimension culturelle', 'usage', 'catégorie', 'nom du lieu',
                       'commune', 'localisation']
    
    data_lines = []
    content = filepath.read_text(encoding="utf-8")
    
    for line in content.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue
        pipe_count = stripped.count('|')
        if pipe_count >= 2 and '---' not in stripped:
            clean_line = stripped[1:-1].strip()
            cells = [c.strip() for c in clean_line.split('|')]
            non_empty_cells = [c for c in cells if c]
            if len(non_empty_cells) >= 2:
                line_lower = clean_line.lower()
                if not any(keyword in line_lower for keyword in header_keywords):
                    clean_line = clean_line.replace('|', '\t')
                    data_lines.append(clean_line)
    
    random.shuffle(data_lines)
    return data_lines[:min(num_lines, len(data_lines))]


def _load_playlist_sample():
    """Retourne un morceau de musique aléatoire de la playlist pour inspiration."""
    try:
        with open(Path("docs") / "radio_sequence.json", encoding="utf-8") as f:
            seq = json.load(f)["sequence"]
        music_tracks = [t for t in seq if t.get("type") == "music"]
        if music_tracks:
            track = random.choice(music_tracks)
            return {
                "title": track.get("title", "Morceau inconnu"),
                "artist": track.get("artist", "Artiste inconnu"),
                "genre": track.get("genre", "N/A")
            }
    except Exception as e:
        print(f"⚠️  Playlist non disponible : {e}", file=sys.stderr)
    return {"title": "la musique caribéenne", "artist": "nos artistes", "genre": "variés"}


def _select_elements():
    """Sélectionne 1 élément par fichier + charge l'inspiration musicale."""
    elements = {}
    file_titles = {
        "kreyol_resistance_symbol_ref.md": "Symboles de la résistance créole",
        "faune_guadeloupe_ref.md": "Faune de Guadeloupe",
        "flore_guadeloupe_ref.md": "Flore de Guadeloupe",
        "lieux_spirituels_ref.md": "Lieux spirituels de Guadeloupe",
        "histoire_guadeloupe_ref.md": "Histoire de Guadeloupe",
    }
    
    for filepath in SOURCE_FILES:
        if filepath.exists():
            lines = _select_random_lines_from_file(filepath, 1)
            if lines:
                key = filepath.name
                elements[key] = {
                    "title": file_titles.get(key, key),
                    "content": lines[0]
                }
    
    # Ajouter l'inspiration musicale
    elements["inspiration"] = _load_playlist_sample()
    
    return elements


# ── LLM ──────────────────────────────────────────────────────────────────────

def _mistral_chat(system: str, user: str) -> str:
    """Appel à l'API Mistral pour générer le texte."""
    import urllib.request, urllib.error, time
    
    key = os.environ["MISTRAL_API_KEY"]
    payload = json.dumps({
        "model": MISTRAL_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": 0.8,
        "max_tokens": 2048,
        "response_format": {"type": "text"}
    }).encode()
    
    req = urllib.request.Request(
        "https://api.mistral.ai/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if e.code in (429, 500, 502, 503) and attempt < 3:
                wait = 15 * 2 ** attempt
                print(f"   ⏳ LLM {e.code} — attente {wait}s…")
                time.sleep(wait)
            else:
                raise RuntimeError(f"LLM HTTP {e.code}: {body}") from None
    raise RuntimeError("LLM : trop de tentatives")


# ── Génération du monologue ───────────────────────────────────────────────

def _load_prompt(filename: str) -> str:
    """Charge un fichier de prompt depuis PROMPTS_DIR."""
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt introuvable : {path}")
    return path.read_text(encoding="utf-8").strip()

# Charger le prompt Monique pour les émissions
SYSTEM_PROMPT = _load_prompt("monique_ame.md") + "\n\n" + _load_prompt("monique.md") + "\n\n" + _load_prompt("emission_instruction.md")


def generate_monologue(elements: dict, verbose: bool = False) -> str:
    """Génère le texte du monologue via LLM."""
    track = elements.get("inspiration", {})
    track_desc = f"'{track['title']}' par {track['artist']} ({track['genre']})"
    
    # Formater les éléments pour le LLM
    formatted_elements = ""
    category_order = [
        ("kreyol_resistance_symbol_ref.md", "Symboles de résistance créole"),
        ("faune_guadeloupe_ref.md", "Faune"),
        ("flore_guadeloupe_ref.md", "Flore"),
        ("lieux_spirituels_ref.md", "Lieux spirituels"),
        ("histoire_guadeloupe_ref.md", "Histoire"),
    ]
    
    for file_key, category in category_order:
        if file_key in elements:
            formatted_elements += f"- {category} : {elements[file_key]['content']}\n"
    
    # Charger le template de user prompt
    try:
        user_template = _load_prompt("emission_user_template.md")
    except Exception:
        user_template = """Contexte : Ton émission est inspirée par {track_desc}.
Éléments à intégrer :
{elements}
Structure ton monologue en 5 paragraphes."""
    
    user_prompt = user_template.format(
        track_desc=track_desc,
        elements=formatted_elements
    )
    
    if verbose:
        print("\n── SYSTEM PROMPT ─────────────────────────────────────────────")
        print(SYSTEM_PROMPT)
        print("\n── USER PROMPT ─────────────────────────────────────────────────")
        print(user_prompt)
        print()
    
    print("🤖 Génération du monologue (LLM)…")
    text = _mistral_chat(SYSTEM_PROMPT, user_prompt).strip()
    
    # Vérifier qu'on a bien 5 paragraphes
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) < 5:
        # Si pas assez, on essaye de séparer manuellement
        print(f"⚠️  Seuls {len(paragraphs)} paragraphes générés, tentative de correction…")
        # Séparer par phrases longues
        sentences = [s.strip() for s in text.split('. ') if s.strip()]
        if len(sentences) >= 5:
            # Regrouper en 5 paragraphes
            chunk_size = len(sentences) // 5
            paragraphs = []
            for i in range(5):
                chunk = sentences[i*chunk_size:(i+1)*chunk_size]
                paragraphs.append('. '.join(chunk) + '.')
            text = '\n\n'.join(paragraphs)
    
    return text


# ── Détermination du ton par LLM ────────────────────────────────────────

TONE_CLASSIFIER_MODEL = "mistral-small-latest"  # Modèle léger pour la classification
AVAILABLE_TONES = ["neutral", "happy", "excited", "curious", "sad"]

def _determine_tone(paragraph: str) -> str:
    """Utilise le LLM pour déterminer le ton optimal d'un paragraphe."""
    try:
        system_prompt = _load_prompt("tone_classifier_system.md")
    except Exception:
        system_prompt = """Tu es un expert en analyse de texte. Choisis UN ton parmi : neutral, happy, excited, curious, sad. Réponds UNIQUEMENT avec le nom du ton."""
    
    try:
        user_template = _load_prompt("tone_classifier_user_template.md")
    except Exception:
        user_template = "Paragraphe à analyser :\n\n{paragraph}\n\nTon adapté :"
    
    user_prompt = user_template.format(paragraph=paragraph)
    
    try:
        response = _mistral_chat_classifier(system_prompt, user_prompt)
        # Nettoyer la réponse et vérifier qu'elle est valide
        tone = response.strip().lower()
        if tone in AVAILABLE_TONES:
            return tone
        # Fallback : neutral
        return "neutral"
    except Exception as e:
        print(f"   ⚠️  Classification du ton échouée : {e}, fallback sur neutral")
        return "neutral"


def _mistral_chat_classifier(system: str, user: str) -> str:
    """Appel à l'API Mistral pour la classification de ton (modèle léger)."""
    import urllib.request, urllib.error, time
    
    key = os.environ["MISTRAL_API_KEY"]
    payload = json.dumps({
        "model": TONE_CLASSIFIER_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": 0.2,  # Plus déterministe pour la classification
        "max_tokens": 16,
        "response_format": {"type": "text"}
    }).encode()
    
    req = urllib.request.Request(
        "https://api.mistral.ai/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if e.code in (429, 500, 502, 503) and attempt < 3:
                wait = 10 * 2 ** attempt
                print(f"   ⏳ Tone classifier {e.code} — attente {wait}s…")
                time.sleep(wait)
            else:
                raise RuntimeError(f"Tone classifier HTTP {e.code}: {body}") from None
    raise RuntimeError("Tone classifier: trop de tentatives")


# ── TTS avec tons variés ───────────────────────────────────────────────────

def _concat_mp3(files: list[Path], output_path: Path) -> None:
    """Concatène plusieurs fichiers MP3 en un seul."""
    all_files: list[Path] = []
    for i, f in enumerate(files):
        all_files.append(f)
        if i < len(files) - 1:
            # Ajouter un petit silence entre les paragraphes
            silence_path = f.parent / f"_sil_{i:02d}.mp3"
            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d=0.3",
                "-c:a", "libmp3lame", "-q:a", "4", str(silence_path),
            ], check=True)
            all_files.append(silence_path)
    
    inputs = [arg for f in all_files for arg in ("-i", str(f))]
    n = len(all_files)
    filter_str = "".join(f"[{i}:a]" for i in range(n)) + f"concat=n={n}:v=0:a=1[out]"
    
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[out]",
        "-c:a", "libmp3lame", "-q:a", "2",
        str(output_path),
    ], check=True)
    
    # Nettoyer les fichiers temporaires
    for f in all_files:
        if f.name.startswith("_sil_"):
            f.unlink(missing_ok=True)


def generate_audio(text: str, output_path: Path) -> None:
    """Génère l'audio avec tons déterminés par LLM pour chaque paragraphe."""
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    
    # Déterminer le ton optimal pour chaque paragraphe via LLM
    print("🎭 Détermination des tons par LLM…")
    tones = []
    for i, para in enumerate(paragraphs):
        tone = _determine_tone(para)
        tones.append(tone)
        print(f"   [{i+1}] ton: {tone}")
    
    temp_files = []
    with tempfile.TemporaryDirectory(prefix="emission_") as tmpdir:
        tmp = Path(tmpdir)
        
        print(f"🔊 TTS ({len(paragraphs)} paragraphes)…")
        for i, (para, tone) in enumerate(zip(paragraphs, tones)):
            temp_path = tmp / f"para_{i:02d}.mp3"
            voice_id = f"{TTS_VOICE_BASE}{tone}"
            print(f"   [{i+1}/{len(paragraphs)}] ton: {tone} → {voice_id}…", flush=True)
            tts_call(normalize_for_tts(para), temp_path, voice_id=voice_id)
            temp_files.append(temp_path)
        
        print("   🔗 Concatenation FFmpeg…")
        _concat_mp3(temp_files, output_path)


# ── Pipeline principal ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Émission culturelle quotidienne — 3 min monologue")
    parser.add_argument("--verbose", action="store_true", help="Affiche prompts et sorties LLM")
    parser.add_argument("--dry-run", action="store_true", help="Texte seul, sans TTS")
    args = parser.parse_args()
    
    # Avertir si des fichiers sources manquent (mais continuer)
    missing = [f for f in SOURCE_FILES if not f.exists()]
    if missing:
        for f in missing:
            print(f"⚠️  Fichier introuvable : {f}", file=sys.stderr)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    out_mp3 = OUTPUT_DIR / f"emission-{today}.mp3"
    out_json = OUTPUT_DIR / f"emission-{today}.json"
    
    # 1. Sélection des éléments + inspiration
    print("🎲 Sélection des éléments…")
    elements = _select_elements()
    print(f"   ✅ {len(elements) - 1} éléments + inspiration musicale")
    
    # 2. Génération du monologue
    text = generate_monologue(elements, verbose=args.verbose)
    
    word_count = len(text.split())
    print(f"✅ Monologue généré : {word_count} mots")
    
    # 3. Sauvegarde JSON
    output_data = {
        "date": today,
        "type": "emission",
        "title": "Émission culturelle — Découverte de la Guadeloupe",
        "duration": "~3 minutes",
        "word_count": word_count,
        "voice": f"{TTS_VOICE_BASE}* (tons variés)",
        "inspiration": elements.get("inspiration", {}),
        "elements": {k: v for k, v in elements.items() if k != "inspiration"},
        "text": text,
        "audio_url": f"https://famibelle.github.io/FlashInfoKarukera/audio/Emissions/emission-{today}.mp3"
    }
    out_json.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"💾 JSON → {out_json}")
    
    # Afficher le texte en mode verbose
    if args.verbose:
        print("\n── Monologue complet ────────────────────────────────────────")
        paragraphs = text.split('\n\n')
        for i, para in enumerate(paragraphs, 1):
            print(f"   [{i}] {para.strip()}")
        print("────────────────────────────────────────────────────────────────")
        print(f"💾 Fichier MP3 : {out_mp3}")
    
    if args.dry_run:
        print("\n── Monologue complet ────────────────────────────────────────")
        paragraphs = text.split('\n\n')
        # Déterminer les tons via LLM même en dry-run pour montrer le résultat
        print("🎭 Détermination des tons par LLM…")
        tones = []
        for i, para in enumerate(paragraphs):
            tone = _determine_tone(para)
            tones.append(tone)
            print(f"   [{i+1}] ton: {tone}")
        for i, (para, tone) in enumerate(zip(paragraphs, tones), 1):
            print(f"\n[{i} — ton: {tone}]")
            print(para)
        print(f"\n⏭️  TTS ignoré (--dry-run)")
        return
    
    # 4. Génération audio
    generate_audio(text, out_mp3)
    size_kb = out_mp3.stat().st_size // 1024
    print(f"✅ MP3 → {out_mp3} ({size_kb} Ko)")

    # 5. Mise à jour du podcast.xml
    _update_podcast_xml(out_mp3)
    
    # 6. Lecture automatique du fichier
    print("\n🔊 Lecture du fichier audio...")
    try:
        # Essaye mpg123 d'abord
        subprocess.run(["mpg123", str(out_mp3)], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            # Fallback sur afplay (macOS)
            subprocess.run(["afplay", str(out_mp3)], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Fallback sur ffplay
                subprocess.run(["ffplay", "-autoexit", "-nodisp", str(out_mp3)], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("   ⚠️  Aucun lecteur audio disponible (mpg123/afplay/ffplay). Installez-en un pour la lecture automatique.")


# ── Mise à jour podcast.xml ───────────────────────────────────────────────

def _indent_xml(elem, level=0):
    """Indente correctement l'XML."""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            _indent_xml(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def _update_podcast_xml(mp3_path: Path) -> None:
    """Ajoute l'émission au fichier podcast.xml."""
    PODCAST_PATH = Path("docs/podcast.xml")
    if not PODCAST_PATH.exists():
        print("⚠️  podcast.xml introuvable")
        return

    today = date.today()
    mp3_url = f"https://famibelle.github.io/FlashInfoKarukera/audio/Emissions/{mp3_path.name}"
    mp3_size = mp3_path.stat().st_size
    pub_date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    # Parse XML
    try:
        tree = ET.parse(PODCAST_PATH)
        root = tree.getroot()
        channel = root.find('channel')
        if channel is None:
            print("⚠️  Balise <channel> introuvable dans podcast.xml")
            return

        # Namespace itunes
        NS_ITUNES = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
        
        # Créer le nouvel item
        item = ET.Element('item')
        ET.SubElement(item, 'title').text = f"Émission culturelle — {today.isoformat()}"
        desc = ET.SubElement(item, 'description')
        desc.text = "Émission culturelle quotidienne sur les symboles, l'histoire et la nature de la Guadeloupe."
        ET.SubElement(item, 'pubDate').text = pub_date
        enc = ET.SubElement(item, 'enclosure')
        enc.set('url', mp3_url)
        enc.set('length', str(mp3_size))
        enc.set('type', 'audio/mpeg')
        ET.SubElement(item, 'guid', {'isPermaLink': 'false'}).text = f'emission-{today.isoformat()}'
        # itunes:duration
        ET.SubElement(item, f'{{{NS_ITUNES}}}duration').text = '180'
        
        # Ajouter l'item au channel (à la fin, convention RSS)
        channel.append(item)

        # S'assurer que le namespace itunes est déclaré sur la racine avec le préfixe 'itunes'
        if 'xmlns:itunes' not in root.attrib:
            # Conserver la déclaration existante du fichier original
            # ElementTree peut avoir ajouté xmlns:ns0, on va la remplacer
            for attr in list(root.attrib.keys()):
                if attr.startswith('xmlns:') and root.attrib[attr] == NS_ITUNES:
                    del root.attrib[attr]
            root.set('xmlns:itunes', NS_ITUNES)
        
        # Sauvegarder avec bonne indentation
        _indent_xml(root)
        
        # Écrire dans un buffer pour corriger les préfixes
        import io
        xml_buffer = io.StringIO()
        tree.write(xml_buffer, encoding='unicode', xml_declaration=True)
        xml_content = xml_buffer.getvalue()
        
        # Remplacer les préfixes nsX: par itunes:
        xml_content = xml_content.replace('ns0:', 'itunes:')
        xml_content = xml_content.replace('ns1:', 'itunes:')
        xml_content = xml_content.replace('ns2:', 'itunes:')
        
        PODCAST_PATH.write_text(xml_content, encoding='utf-8')
        print(f"✅ podcast.xml mis à jour avec l'émission")
    except Exception as e:
        print(f"⚠️  Erreur mise à jour podcast.xml: {e}")


if __name__ == "__main__":
    main()
