# 📋 Notes Techniques - Correction Player YouTube & Radio - 8 Mai 2026

**Projet :** FlashInfoKarukera - Radio Botiran  
**Date :** 2026-05-08  
**Auteur :** Mistral Vibe (assisté)  
**Statut :** ✅ Tous problèmes résolus

---

## 📚 TABLE DES MATIÈRES

1. [Contexte](#-contexte)
2. [Problèmes rencontrés](#-problèmes-rencontrés)
3. [Solutions appliquées](#-solutions-appliquées)
4. [Leçons apprises](#-leçons-apprises)
5. [Checklist pour la prochaine fois](#-checklist-pour-la-prochaine-fois)
6. [Architecture du projet](#-architecture-du-projet)
7. [Workflows GitHub Actions](#-workflows-github-actions)

---

## 📌 Contexte

Le projet **Radio Botiran** génère automatiquement une playlist radio combinant :
- **Flash Info** (actualités Guadeloupe, MP3)
- **Horoscope** (prédictions, MP3)
- **Liners** (transitions, MP3)
- **Musiques** (YouTube, vidéo)

**Technologies :**
- GitHub Pages (déploiement)
- YouTube IFrame API (player vidéo)
- HTML5 Audio (player MP3)
- Python (génération de contenu)

---

## ⚠️ Problèmes rencontrés

### 1️⃣ **Player YouTube ne s'affichait pas**
- **Symptôme :** Écran noir, pas de vidéo YouTube
- **Cause racine :** `onYouTubeIframeAPIReady` non appelé car script chargé avant le callback
- **Impact :** Player YouTube non initialisé

### 2️⃣ **Erreurs `postMessage`**
- **Symptôme :** `Failed to execute 'postMessage' on 'DOMWindow'`
- **Cause :** Paramètre `origin: window.location.origin` obsolète
- **Impact :** Communication cross-origin bloquée

### 3️⃣ **YouTube visible à l'ouverture (alors que 1er item = transition)**
- **Symptôme :** Rectangle noir YouTube visible au démarrage
- **Cause :** `#yt-wrap` n'avait pas `display: none` par défaut
- **Impact :** Confusion visuelle avec `#transition-overlay`

### 4️⃣ **Erreur au clic sur play**
- **Symptôme :** "Une erreur s'est produite. Veuillez réessayer ultérieurement."
- **Cause :** `togglePlay()` passait par la branche audio pour les items music quand YT n'était pas prêt
- **Impact :** Tentative de jouer un MP3 au lieu d'une vidéo YouTube

### 5️⃣ **Date incorrecte du Flash Info (6 mai au lieu de 8 mai)**
- **Symptôme :** Flash Info du 6 mai affiché le 8 mai
- **Cause :** Merge conflict qui a rétrogradé `radio_sequence.json` vers une ancienne version
- **Impact :** Contenu obsolète

### 6️⃣ **Fichiers liners introuvables (404)**
- **Symptôme :** Les liners semblaient vides, pas de son
- **Cause :** Fichiers `.mp3` générés non commités/poussés
- **Impact :** 81 fichiers untracked (29 liners × 2 formats + archives)

### 7️⃣ **Warnings `passive event listener`**
- **Symptôme :** `[Violation] Added non-passive event listener to a scroll-blocking event`
- **Cause :** `{ passive: false }` sur touchstart/touchmove
- **Impact :** Performances dégradées sur mobile

---

## ✅ Solutions appliquées

### Solution 1: Chargement dynamique de YouTube IFrame API
```javascript
// AVANT (statique, chargé trop tôt)
<script src="https://www.youtube.com/iframe_api"></script>

// APRÈS (dynamique, après callback)
window.onYouTubeIframeAPIReady = () => resolve();
const tag = document.createElement('script');
tag.src = 'https://www.youtube.com/iframe_api';
document.head.appendChild(tag);
```

**Commit :** `e071ab0`

---

### Solution 2: Gestion du cache YouTube
```javascript
const ytApiPromise = new Promise(resolve => {
  // 1. Déjà chargé ?
  if (window.YT && window.YT.Player) return resolve();
  
  // 2. Sinon, attendre callback
  window.onYouTubeIframeAPIReady = () => resolve();
  
  // 3. Polling de secours (15s)
  let waited = 0;
  const poll = setInterval(() => {
    if (window.YT && window.YT.Player) {
      clearInterval(poll); resolve();
    }
    if ((waited += 200) >= 15000) {
      clearInterval(poll); resolve();
    }
  }, 200);
});
```

**Commit :** `1df237b`

---

### Solution 3: Initialisation systématique de YouTube
```javascript
// AVANT (seulement si 1er item = music)
if (firstItem.type === 'music') {
  radio._ytApiReady.then(() => radio._initYT());
}

// APRÈS (toujours)
radio._ytApiReady.then(() => {
  if (window.YT && window.YT.Player && !radio.yt) {
    return radio._initYT();
  }
});
```

**Commit :** `9ef0224`

---

### Solution 4: Suppression du paramètre `origin`
```javascript
// AVANT
playerVars: {
  autoplay: 0,
  controls: 1,
  rel: 0,
  modestbranding: 1,
  origin: window.location.origin,  // ❌ Obsolète
  enablejsapi: 1
}

// APRÈS
playerVars: {
  autoplay: 0,
  controls: 1,
  rel: 0,
  modestbranding: 1,
  enablejsapi: 1  // ✅ Fonctionne sans origin
}
```

**Commit :** `5b7b9bc`

---

### Solution 5: Masquage de `#yt-wrap` par défaut
```css
/* AVANT */
#yt-wrap {
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
}

/* APRÈS */
#yt-wrap {
  display: none;  /* ✅ Masqué par défaut */
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
}
```

**Commit :** `af26683`

---

### Solution 6: Correction de `togglePlay()`
```javascript
// AVANT (bug: passait par audio pour music si !ytReady)
if (item.type === 'music' && this.ytReady) {
  // YouTube
} else {
  this.trAudio.play();  // ❌ Essayait de jouer audio pour music
}

// APRÈS (branches séparées)
if (item.type === 'music') {
  if (this.ytReady) {
    this.yt.playVideo();
  } else {
    this._showYT();
    // Initialisation + chargement
  }
} else {
  this._showTransition(item);
  this.trAudio.play();
}
```

**Commit :** `6859b1f`

---

### Solution 7: Restauration de `radio_sequence.json`
```bash
# Le merge commit 2b6a0e3 avait rétrogradé le fichier
# vers la version du 6 mai

# Restauration depuis le bon commit:
git show 97d7818:docs/radio_sequence.json > docs/radio_sequence.json
git add docs/radio_sequence.json
git commit -m "fix: restore radio_sequence.json avec les données du 8 mai"
```

**Commit :** `d6bac25`

---

### Solution 8: Chemin relatif corrigé
```javascript
// AVANT (absolu, ne fonctionnait pas en local)
fetch('/radio_sequence.json?t=' + Date.now())

// APRÈS (relatif, fonctionne partout)
fetch('radio_sequence.json?t=' + Date.now())
```

**Commit :** `528de83` → `92d182d`

---

### Solution 9: Commit des fichiers générés
```bash
# 81 fichiers étaient untracked:
- 29 liners (matin/midi/soir) × 2 (JSON + MP3)
- 4 capsules
- 4 archives
- 1 note de debug

git add DEBUG_NOTES_2026-05-08.md archives/*.json docs/liners/*.json docs/liners/*.mp3
git commit -m "chore: ajoute les liners générés pour le 8 mai 2026"
```

**Commit :** `5d5e32d`

---

### Solution 10: Event listeners passifs
```css
/* CSS */
#transition-overlay {
  touch-action: none;  /* Désactive scroll natif */
}
```

```javascript
// AVANT
transitionOverlay.addEventListener('touchstart', fn, { passive: false });
transitionOverlay.addEventListener('touchmove', fn, { passive: false });

// APRÈS
transitionOverlay.addEventListener('touchstart', fn);  // Passif par défaut
transitionOverlay.addEventListener('touchmove', fn);   // Passif, mais touch-action: none permet preventDefault
```

**Commit :** `d2af6b3`

---

## 💡 Leçons apprises

### 1. YouTube IFrame API
- **Ordre critique** : `onYouTubeIframeAPIReady` **DOIT** être défini **AVANT** que le script ne soit chargé
- **Cache navigateur** : Toujours vérifier si `window.YT` est déjà défini
- **Paramètres obsolètes** : `origin` n'est plus nécessaire et peut causer des erreurs

### 2. Gestion des dépendances tierces
- **Ne pas supposer** que le callback sera toujours appelé
- **Toujours prévoir** un mécanisme de secours (polling)
- **Vérifier la documentation** : Certains paramètres sont dépréciés

### 3. Initialisation de code
- **Ne pas conditionner** l'initialisation critique au type du premier élément
- **Toujours initialiser** les dépendances nécessaires au démarrage
- **Séparer les responsabilités** : YouTube vs Audio HTML5

### 4. Chemins de fichiers
- **Comprendre l'architecture** : Où sont les fichiers dans le dépôt vs sur GitHub Pages
- **GitHub Pages** déploie `docs/` à la racine → Les chemins relatifs fonctionnent
- **Tester en local** : Utiliser `python3 -m http.server` depuis `docs/`

### 5. Git et workflows
- **Commiter les fichiers générés** : Les workflows génèrent des fichiers, mais il faut les commiter pour qu'ils soient déployés
- **Vérifier les untracked files** : `git status` avant de pousser
- **Merge conflicts** : Toujours vérifier les fichiers après un merge

### 6. Cache navigateur
- **GitHub Pages** a un cache CDN qui peut prendre 5-10 min à se rafraîchir
- **Toujours tester** avec `Ctrl+F5` ou en navigation privée
- **Cache-busting** : Utiliser `?t=timestamp` pour forcer le rafraîchissement

### 7. Développement mobile
- **`passive: false`** bloque le scroll → À éviter sauf nécessité
- **`touch-action: none`** permet de désactiver le scroll natif tout en gardant `preventDefault()`
- **Tester sur mobile** : Les problèmes de performance sont souvent visibles uniquement sur mobile

---

## 📋 Checklist pour la prochaine fois

### ✅ Avant de pousser du code
- [ ] Vérifier `git status` pour les fichiers untracked
- [ ] Commiter **tous** les fichiers générés (liners, capsules, etc.)
- [ ] Tester en local avec `python3 -m http.server` depuis `docs/`
- [ ] Vérifier que tous les chemins sont corrects (relatifs/absolus)

### ✅ Après un merge
- [ ] Vérifier les fichiers critiques (`radio_sequence.json`, `radio.html`)
- [ ] Tester le déploiement sur GitHub Pages
- [ ] Vérifier la console pour les erreurs 404

### ✅ Quand un problème survient
- [ ] **1. Vérifier la console** (F12) pour les erreurs
- [ ] **2. Tester l'URL directe** des ressources (MP3, JSON)
- [ ] **3. Vider le cache** (`Ctrl+F5` ou navigation privée)
- [ ] **4. Vérifier GitHub Pages** : Le fichier est-il déployé ?
- [ ] **5. Tester en local** : Le problème vient-il du code ou du déploiement ?

### ✅ Pour les problèmes YouTube
- [ ] Vérifier que `onYouTubeIframeAPIReady` est défini **avant** le script
- [ ] Vérifier que `window.YT` et `window.YT.Player` sont définis
- [ ] Supprimer le paramètre `origin` des `playerVars`
- [ ] Masquer `#yt-wrap` par défaut dans le CSS

### ✅ Pour les problèmes audio
- [ ] Vérifier que les fichiers MP3 sont commités/poussés
- [ ] Vérifier que les URLs dans `radio_sequence.json` sont correctes
- [ ] Tester l'URL directe du MP3 dans le navigateur

---

## 🏗️ Architecture du projet

```
FlashInfoKarukera/
├── .github/
│   └── workflows/
│       ├── flash-info.yml          # Génère Flash Info
│       ├── horoscope-daily.yml     # Génère Horoscope  
│       └── pages.yml               # Déploie sur GitHub Pages
│
├── docs/
│   ├── radio.html                 # Player principal
│   ├── radio_sequence.json        # Playlist (généré)
│   ├── liners/                    # Transitions (généré)
│   │   ├── *.json
│   │   └── *.mp3
│   ├── capsules/                  # Capsules culturelles (généré)
│   │   ├── *.json
│   │   └── *.mp3
│   └── audio/
│       └── flash-info/             # Flash Info (généré)
│           └── *.mp3
│
├── scripts/
│   ├── flash-info-gwada.py
│   └── horoscope-gwada.py
│
└── archives/                      # Historique
    ├── radio_sequence_*.json
    └── youtube_playlist_*.json
```

### Points clés :
- **GitHub Pages** déploie le contenu de `docs/` à la racine du site
- **`radio.html`** est le point d'entrée principal
- **`radio_sequence.json`** est généré par les workflows Python
- **Tous les fichiers audio** (liners, capsules, flash-info) sont générés et stockés dans `docs/`

---

## 🔄 Workflows GitHub Actions

### 1. `flash-info.yml`
- **Déclenchement** : `push` sur `main` (fichiers modifiés dans `scripts/`, `data/`, ou `prompts/`)
- **Action** : Exécute `python flash-info-gwada.py` pour générer les fichiers
- **Sortie** : Flash Info MP3 + mise à jour de `radio_sequence.json`

### 2. `horoscope-daily.yml`
- **Déclenchement** : `push` sur `main` + `schedule` (quotidien)
- **Action** : Exécute `python horoscope-gwada.py`
- **Sortie** : Horoscope MP3 + mise à jour de `radio_sequence.json`

### 3. `pages.yml`
- **Déclenchement** : `push` sur `main` (modifications dans `docs/`) ou `workflow_dispatch`
- **Action** : Déploie le contenu de `docs/` sur GitHub Pages
- **Sortie** : Site accessible à `https://famibelle.github.io/FlashInfoKarukera/`

### 💡 Conseils workflows :
1. **Ordre d'exécution** : `flash-info.yml` et `horoscope-daily.yml` doivent s'exécuter **avant** `pages.yml`
2. **Dependencies** : `pages.yml` dépend des modifications dans `docs/`
3. **Cache** : Les workflows peuvent mettre en cache des dépendances (Python, etc.)

---

## 📞 Contacts & Ressources

- **Documentation YouTube IFrame API** : [https://developers.google.com/youtube/iframe_player_reference](https://developers.google.com/youtube/iframe_player_reference)
- **GitHub Pages** : [https://pages.github.com/](https://pages.github.com/)
- **MDN : postMessage** : [https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage](https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage)
- **MDN : touch-action** : [https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action](https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action)

---

## 🔖 Historique des commits

| Date | Commit | Problème | Solution |
|------|--------|----------|----------|
| 2026-05-08 | `e071ab0` | Script YouTube chargé avant callback | Chargement dynamique après callback |
| 2026-05-08 | `1df237b` | API YouTube en cache | Polling de secours + vérification |
| 2026-05-08 | `9ef0224` | YouTube non initialisé | Initialisation systématique |
| 2026-05-08 | `5b7b9bc` | Erreurs postMessage | Suppression param `origin` |
| 2026-05-08 | `af26683` | YouTube visible à l'ouverture | `display: none` par défaut |
| 2026-05-08 | `6859b1f` | Erreur au clic | Correction `togglePlay()` |
| 2026-05-08 | `d6bac25` | Date incorrecte | Restauration bon fichier |
| 2026-05-08 | `528de83` | Chemin incorrect | Chemin relatif corrigé |
| 2026-05-08 | `92d182d` | Merge du chemin | Merge de la correction |
| 2026-05-08 | `5d5e32d` | Liners introuvables | Commit des fichiers générés |
| 2026-05-08 | `d2af6b3` | Warnings passive | `touch-action: none` |

---

*Document généré par Mistral Vibe - 2026-05-08*
*À conserver pour référence future*
