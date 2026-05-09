# Notes de développement — Observations techniques

## 1. `[skip ci]` bloque le déploiement GitHub Pages

**Symptôme** : le site `radio.html` affichait du contenu vieux de plusieurs jours.

**Cause** : tous les commits générés par les workflows contiennent `[skip ci]`. Ce tag annule **tous** les déclencheurs GitHub Actions sur ce commit, y compris `pages.yml`. Le site restait figé sur le dernier commit humain.

**Fix** : chaque workflow qui commite dans `docs/` appelle explicitement `gh workflow run pages.yml --ref main` après son push. Un `workflow_dispatch` ne peut pas être annulé par `[skip ci]`.

**Workflows concernés** : `botiran-radio-daily`, `flash-info`, `horoscope-daily`, `emission-daily`, `dreams-daily`.

---

## 2. `radio.html` lit uniquement `radio_sequence.json` — aucune découverte dynamique

Le player ne scanne pas les fichiers audio. Il lit **exclusivement** `docs/radio_sequence.json` via :
```js
const r = await fetch('radio_sequence.json?t=' + Date.now());
```

Si un fichier n'est pas dans ce JSON au moment où la page se charge, il n'existe pas pour le player. Cela inclut les éditions midi et soir générées après la séquence du matin.

---

## 3. Les noms de fichiers sont déterministes

Tous les fichiers audio suivent un pattern fixe basé sur la date et l'édition :
- `flash-info-YYYYMMDD-{matin|midi|soir}.mp3`
- `horoscope-YYYYMMDD-{matin|soir}.mp3`
- `emission-YYYY-MM-DD.mp3`

**Conséquence** : `generate_radio_sequence.py` peut pré-remplir tous les slots du jour avec leurs URLs exactes, même si les fichiers ne sont pas encore générés (`"pending": true`). Quand le fichier est créé plus tard dans la journée, le player le trouve automatiquement à la bonne URL.

Le player saute gracieusement les items en 404 grâce au handler :
```js
this.trAudio.addEventListener('error', () => {
  if (this.trAudio.error) this._next();
});
```

---

## 4. Les slots RSS remontaient du contenu périmé

`load_transitions()` remplissait les slots (`flash_midi`, `flash_soir`, `horoscope_soir`) avec les éditions les plus récentes du RSS, qui pouvaient dater d'un ou deux jours. La pré-population force maintenant ces slots à pointer vers **aujourd'hui**, en remplaçant tout slot RSS dont l'URL ne contient pas la date du jour.

---

## 5. `git push origin +HEAD:main` — force push destructeur

`botiran-radio-daily` utilisait un force push qui écrasait silencieusement les commits poussés entre le checkout du workflow et sa fin (~10 min). L'émission du 9 mai a été perdue de cette façon.

**Fix** : remplacé par `git push || (git pull origin main --rebase -X ours --no-edit && git push)` dans tous les workflows.

---

## 6. Pattern `stash → rebase -X theirs` — conflits modify/delete

L'ancien pattern de gestion des conflits dans les workflows :
```bash
git commit ...
git stash --include-untracked
git pull --rebase -X theirs origin main
git stash drop
git push
```

Échouait avec des conflits modify/delete quand deux workflows modifiaient les mêmes fichiers en parallèle. `-X theirs` ne résout pas ce type de conflit.

**Fix** : pull **avant** le staging, puis commit, puis push+retry :
```bash
git pull origin main --no-rebase -X ours --no-edit 2>/dev/null || true
git add ...
git commit ...
git push || (git pull origin main --rebase -X ours --no-edit && git push)
```

---

## 7. `save_day_report()` supprime `texts_sample` — évaluation LLM silencieusement ignorée

`dream_radio.py` sauvegarde un DayReport JSON allégé (sans `texts_sample`) pour limiter la taille. Lors du rendu, `render_antenne_dream()` lisait ce JSON slim et trouvait `texts_sample` vide → le LLM n'était jamais appelé pour évaluer les journalistes.

**Fix** : `render_antenne_dream()` recharge les textes depuis les archives (`load_journalist_texts(date_str)`) en fallback quand `texts_sample` est absent du JSON slim.

---

## 8. `workflows_in_alert` toujours vide

Le calcul des workflows en alerte utilisait `last_status != "success"` (état du dernier run). Un workflow avec 16% de taux de succès mais dont le dernier run s'était bien passé n'apparaissait jamais en alerte.

**Fix** : `success_rate < 0.90` sur la fenêtre glissante de 7 jours.

---

## 9. Date hardcodée dans `radio.html`

Le fallback de `_extractDateAndMoment()` était `let dateStr = '8 mai'`. Si la regex échouait, la page affichait systématiquement "8 mai".

**Fix** : le fallback est maintenant calculé depuis `new Date()`.
