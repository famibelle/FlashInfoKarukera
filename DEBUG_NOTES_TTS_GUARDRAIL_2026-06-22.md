# Note technique — TTS bloqué par guardrail (403) & régénération automatique

**Date** : 2026-06-22
**Fichiers touchés** : `tts_utils.py`, `horoscope-gwada.py`

---

## Symptôme

Le workflow **Horoscope Quotidien** (édition matin, run `27899815347`, 2026-06-21 ~09:18 UTC)
a échoué à l'étape « Générer l'horoscope » :

```
RuntimeError: TTS HTTP 403 (Forbidden):
{"object":"error","message":"Request blocked by guardrail policy",
 "type":"guardrail_violation","param":null,"code":"1920","raw_status_code":403}
```

L'orchestrateur tourne en `continue-on-error`, donc la chaîne du jour n'a pas été
totalement bloquée, et le cycle suivant (~4h plus tard) est repassé tout seul.

## Cause

Le texte d'horoscope généré par Mistral (`mistral-large-latest`) a déclenché le
**garde-fou de modération de l'API Mistral** au moment de l'envoi vers le TTS
Voxtral (`/v1/audio/speech`). Ce n'est **pas** un problème de credentials ni de
config : c'est un blocage **dépendant du contenu**, donc transitoire et aléatoire
selon la formulation produite.

L'ancien `tts_call` traitait ce 403 comme une erreur fatale générique
(`RuntimeError`), sans distinction ni récupération.

## Correctif

### `tts_utils.py`
- Nouvelle exception dédiée **`TTSGuardrailError`** (sous-classe de `RuntimeError`).
- Détection ciblée du garde-fou : 403 **et** (`"guardrail"` dans le corps **ou**
  `"code":"1920"`).
- Nouveau paramètre **`regen_fn`** sur `tts_call` : sur un 403 guardrail, le
  callback est appelé pour produire un **texte de remplacement déjà normalisé**,
  et la requête est rejouée — jusqu'à `_guardrail_retries=2` fois. Sans `regen_fn`,
  une `TTSGuardrailError` explicite est levée (diagnostic immédiat dans les logs).
- Les retries transitoires (429/5xx) restent inchangés, dans leur propre compteur.

### `horoscope-gwada.py`
Les **4 points de synthèse de la production** passent un `regen_fn` qui ré-appelle
Mistral avec **`temperature=0.9`** (au lieu de 0.75) pour varier la formulation :
intro, signe du jour (flore/faune), boucle par signe, outro.

> Les chemins de debug `--test-flora` / `--test-faune` ne sont pas des étapes du
> run quotidien et restent inchangés.

## Comportement attendu

```
🛡️  TTS bloqué par guardrail — régénération du texte (tentative 1/2)…
```

Le segment est régénéré et le run continue. Après 2 tentatives infructueuses,
le job échoue sur `TTSGuardrailError` — motif clair plutôt qu'un message opaque.

## Limite assumée

La régénération relance Mistral avec les **mêmes prompts** à température plus
haute. Efficace pour une tournure malheureuse (cas le plus fréquent), mais pas si
le contenu source lui-même (un fait de l'index culturel, une actu) est
intrinsèquement problématique. Piste si récurrent : injecter dans le prompt de
régénération une consigne « reformule en termes neutres ».

## Réutilisable ailleurs

`flash-info-gwada.py`, `generate_emission.py` et les autres pipelines appellent le
même `tts_call`. Le paramètre `regen_fn` y est disponible mais **pas encore câblé** —
à ajouter de la même façon si un de ces pipelines se met à trébucher sur le guardrail.
