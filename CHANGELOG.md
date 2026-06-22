# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format s'inspire de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/)
et le projet suit le [versionnage sémantique](https://semver.org/lang/fr/).

Catégories utilisées : `Ajouté`, `Modifié`, `Corrigé`, `Supprimé`, `Sécurité`.

## [Non publié]

### Corrigé
- TTS Voxtral : régénération automatique du texte sur un 403 *guardrail* Mistral.
  `tts_call` distingue désormais ce cas via `TTSGuardrailError` et accepte un
  callback `regen_fn` (re-génération à `temperature=0.9` puis rejeu de la requête),
  câblé sur les 4 points de synthèse de l'horoscope. Voir
  `DEBUG_NOTES_TTS_GUARDRAIL_2026-06-22.md`.

### Ajouté
- `CLAUDE.md` — guide d'architecture pour Claude Code.
- `CHANGELOG.md` — ce fichier, pour suivre les versions.
- Visuel `docs/Lyannaj_Kiltirèl.png`.

---

[Non publié]: https://github.com/famibelle/FlashInfoKarukera/commits/main
