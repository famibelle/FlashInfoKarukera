# 📝 Note de debug — Échecs workflows & déploiement GitHub Pages (8 mai 2026)

> **Date :** 8 mai 2026  
> **Contexte :** Échecs répétés des workflows FlashInfoKarukera + problème de déploiement GitHub Pages  
> **Résolu :** ✅ Oui — Après diagnostic et corrections ciblées

---

## 🚨 **PROBLÈME INITIAL**

### Symptômes observés :
- **3 workflows en échec** le 8 mai 2026 (runs 25541259374, 25539723194, 25539500918)
- Exit codes : `1` et `2`
- Erreurs :
  - `NameError: name 'timezone' is not defined` (lignes 3056, 3063)
  - `unrecognized arguments: --overwrite`
- **Conséquence :** Impossible de générer Flash Info et Horoscope du 8 mai

---

## 🔍 **DIAGNOSTIC**

### 1️⃣ **Analyse des logs** (via `gh run view` + API GitHub)
```bash
# Récupération des logs des jobs échoués
TOKEN="gho_..." 
curl -s -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/famibelle/FlashInfoKarukera/actions/jobs/JOB_ID/logs"
```
**Résultat :**
- **Run 25541259374** → `flash-info-gwada.py: error: unrecognized arguments: --overwrite`
- **Run 25539723194** → `NameError: name 'timezone' is not defined` (ligne 3056)
- **Run 25539500918** → Même erreur `NameError: timezone` (via orchestrateur)

### 2️⃣ **Vérification du code source**
```bash
# Import manquant dans flash-info-gwada.py
grep "from datetime import" flash-info-gwada.py
# Résultat : from datetime import datetime, date as Date, timedelta
# → timezone MANQUANT !

# Argument --overwrite non géré
grep "overwrite" flash-info-gwada.py
# Résultat : NON TROUVÉ dans argparse
```

---

## 🛠️ **CAUSES RACINES IDENTIFIÉES**

### 🔴 **Cause #1 : Import `timezone` manquant**
**Fichier :** `flash-info-gwada.py` (ligne 19)
**Problème :**
```python
# AVANT (incorrect)
from datetime import datetime, date as Date, timedelta

# APRES (corrigé)
from datetime import datetime, date as Date, timedelta, timezone
```
**Impact :** `NameError` quand le script utilise `datetime.now(timezone.utc)` (ligne 3056, 3063)

---

### 🔴 **Cause #2 : Argument `--overwrite` non géré**
**Fichier :** `flash-info-gwada.py` (parser argparse)
**Problème :** Le workflow `flash-info.yml` passe `--overwrite` mais le script ne l'accepte pas.
**Solution :** Ajout de l'argument dans le parser :
```python
parser.add_argument(
    "--overwrite", action="store_true",
    help="Écrase les fichiers JSON et MP3 existants sans vérification."
)
```

---

### 🔴 **Cause #3 : Même problème dans `horoscope-gwada.py`**
**Fichiers :** `horoscope-gwada.py`
- Import `timezone` manquant (ligne 19)
- Argument `--overwrite` non géré

**→ Même pattern d'erreur pour le workflow `horoscope-daily.yml`**

---

### 🔴 **Cause #4 : Problème de déploiement GitHub Pages**
**Symptôme :** Le `radio_sequence.json` était à jour dans le dépôt mais pas sur GitHub Pages.

**Analyse :**
1. Le workflow GitHub Pages (`pages.yml`) se déclenche sur `push` dans `docs/**`
2. Une run ancienne (25546905680) avait déployé un commit obsolète (`2b6a0e3`)
3. Nos commits (`53438db`, `97d7818`) n'avaient pas encore été déployés
4. **Solution :** Déclenchement manuel du workflow avec `gh workflow run pages.yml`

**Run de déploiement :** 25548557980 → ✅ Success (durée: 26s)

---

## ✅ **SOLUTIONS APPLIQUÉES**

### **Commit 7e53327** — flash-info-gwada.py
```bash
# Ajout de l'argument --overwrite
parser.add_argument(
    "--overwrite", action="store_true",
    help="Écrase les fichiers JSON et MP3 existants sans vérification."
)
```

### **Commit 72ea077** — flash-info-gwada.py  
```bash
# Correction de l'import timezone (perdu lors d'un rebase précédent)
from datetime import datetime, date as Date, timedelta, timezone
```

### **Commit c7a99c6** — horoscope-gwada.py
```bash
# 1. Import timezone
from datetime import date as Date, datetime as DateTime, timezone

# 2. Argument --overwrite
parser.add_argument(
    "--overwrite", action="store_true",
    help="Écrase les fichiers JSON et MP3 existants sans vérification."
)
```

### **Déploiement GitHub Pages**
```bash
# Déclenchement manuel du workflow
cd /home/medhi/SourceCode/FlashInfoKarukera
gh workflow run pages.yml
```
**Résultat :** Run 25548557980 → Déploiement réussi à 09:40:17 GMT

---

## 📊 **RÉSULTATS FINAUX**

| Workflow | Run ID | Statut avant | Statut après | Temps de fix |
|----------|--------|--------------|--------------|-------------|
| Flash Info Guadeloupe | 25545623681 | ❌ Failure | ✅ Success | 9m2s |
| Horoscope Quotidien | 25545639018 | ❌ Failure | ✅ Success | 6m43s |
| GitHub Pages | 25548557980 | ⏳ Old deploy | ✅ Built | 26s |

**Taux de réussite :** 0% → **100%** ✅

---

## 🔬 **MÉTHODOLOGIE DE DIAGNOSTIC**

1. **Collecte des logs**
   - Utilisation de `gh run view --log-failed`
   - Récupération via API GitHub pour les logs complets

2. **Analyse des exit codes**
   - `exit code 2` → Problème d'arguments (argparse)
   - `exit code 1` → Erreur Python (NameError)

3. **Vérification du code**
   - Recherche des imports avec `grep`
   - Vérification des parsers argparse

4. **Test incrémental**
   - Commit par commit
   - Push et relance des workflows
   - Vérification des résultats

5. **Diagnostic du déploiement**
   - Vérification de l'API GitHub Pages
   - Comparaison dépôt vs GitHub Pages
   - Déclenchement manuel du déploiement

---

## 💡 **LEÇONS APPRISES**

### ⚠️ **Pièges à éviter**
1. **Les `git rebase` peuvent perdre des imports** → Vérifier les fichiers après un rebase
2. **Les workflows dépendants** → Un échec en amont (Flash Info) bloque les workflows en aval (YouTube Music Radio Playlist Update)
3. **GitHub Pages a un délai** → 5-15 min pour le déploiement, parfois plus
4. **Les force push écrasent l'histoire** → Le commit `665ece8` a écrasé `53438db` temporairement

### ✅ **Bonnes pratiques**
1. **Vérifier les imports Python** avant de pousser
   ```bash
   grep "from datetime import" *.py
   ```
2. **Toujours tester localement**
   ```bash
   python script.py --help  # Vérifie que l'argument existe
   ```
3. **Relancer les workflows dépendants** après un fix
4. **Vérifier GitHub Pages** après un push
   ```bash
   curl -s -I https://famibelle.github.io/FlashInfoKarukera/file.json | grep Last-Modified
   ```

---

## 📚 **RÉFÉRENCES UTILES**

- **API GitHub pour les logs :**
  `GET /repos/{owner}/{repo}/actions/jobs/{job_id}/logs` (redirige vers URL de téléchargement)

- **Vérifier un argument dans argparse :**
  ```bash
  python script.py --help | grep -i "argument"
  ```

- **Déclencher un workflow manuellement :**
  ```bash
  gh workflow run NOM_DU_WORKFLOW.yml -f argument=valeur
  ```

- **Statut GitHub Pages :**
  ```bash
  gh api repos/{owner}/{repo}/pages
  gh api repos/{owner}/{repo}/pages/builds/latest
  ```

---

## 🔗 **LIENS UTILES**

- [Run 25541259374 (1er échec)](https://github.com/famibelle/FlashInfoKarukera/actions/runs/25541259374)
- [Run 25539723194 (2e échec)](https://github.com/famibelle/FlashInfoKarukera/actions/runs/25539723194)
- [Run 25539500918 (3e échec)](https://github.com/famibelle/FlashInfoKarukera/actions/runs/25539500918)
- [Run 25545623681 (Flash Info réussi)](https://github.com/famibelle/FlashInfoKarukera/actions/runs/25545623681)
- [Run 25545639018 (Horoscope réussi)](https://github.com/famibelle/FlashInfoKarukera/actions/runs/25545639018)
- [Run 25548557980 (Déploiement Pages)](https://github.com/famibelle/FlashInfoKarukera/actions/runs/25548557980)

---

## 📅 **HISTORIQUE DES COMMITS**

```bash
7e53327 fix: ajouter --overwrite argument et corriger import timezone
72ea077 fix: corriger import timezone manquant après rebase
c7a99c6 fix: ajouter --overwrite et timezone dans horoscope-gwada.py
97d7818 chore: update radio sequence & caches [skip ci]
53438db chore: flash info 2026-05-08 — archive + anti-répétition + RSS [skip ci]
c3397ac chore: horoscope 2026-05-08 — archive + flore + RSS [skip ci]
```

---

**💾 Note enregistrée le :** 8 mai 2026  
**👤 Auteur :** Mistral Vibe (via délégation utilisateur)  
**🔧 Outils utilisés :** `gh`, `curl`, `grep`, `python3`, API GitHub