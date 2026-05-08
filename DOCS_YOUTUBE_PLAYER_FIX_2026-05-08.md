# 📝 Correction du Player YouTube - 8 Mai 2026

**Date :** 2026-05-08  
**Auteur :** Mistral Vibe (assisté)  
**Fichier concerné :** `docs/radio.html`  
**Statut :** ✅ Résolu et déployé

---

## 🚨 Problème Reporté

> *"Le player n'affiche pas les vidéos/musiques YouTube dans `radio.html`"*

Symptômes observés :
- Écran noir dans la zone YouTube
- Pas d'erreurs visibles dans la console (initialement)
- Les items MP3 (Flash Info, Horoscope, Liners) fonctionnaient
- Les items de type `music` (YouTube) ne s'affichaient pas

---

## 🔍 Diagnostic

### Cause racine principale

**L'initialisation du player YouTube (`_initYT()`) n'était déclenchée que si le premier item de la séquence était de type `music`.**

Dans `radio_sequence.json`, le premier item est systématiquement une **`transition`** (Flash Info) :
```json
{
  "type": "transition",
  "subtype": "flash_info",
  "url": "...flash-info-20260508-matin.mp3",
  ...
}
```

→ Résultat : `_initYT()` **n'était jamais appelé** → `radio.yt` = `null` → `radio.ytReady` = `false` → les vidéos YouTube ne se chargeaient jamais.

### Problèmes secondaires identifiés

1. **Ordre de chargement du script YouTube** : Le script `<script src="https://www.youtube.com/iframe_api"></script>` était chargé **avant** que le callback `onYouTubeIframeAPIReady` ne soit défini, empêchant YouTube d'appeler le callback.

2. **API YouTube déjà chargée** : Si l'API était déjà dans le cache du navigateur, le callback `onYouTubeIframeAPIReady` n'était jamais appelé, bloquant la promesse d'initialisation.

3. **Erreurs postMessage** : Le paramètre `origin: window.location.origin` dans les `playerVars` provoquait des erreurs de type :
   ```
   Failed to execute 'postMessage' on 'DOMWindow': 
   The target origin provided does not match the recipient window's origin
   ```

---

## ✅ Solutions Appliquées

### Commit `e071ab0` - Chargement dynamique du script YouTube

**Problème :** Script chargé avant le callback  
**Solution :** Chargement dynamique **après** définition du callback

```javascript
// AVANT : Script statique chargé trop tôt
<script src="https://www.youtube.com/iframe_api"></script>

// APRÈS : Chargement dynamique
window.onYouTubeIframeAPIReady = () => { resolve(); };
const tag = document.createElement('script');
tag.src = 'https://www.youtube.com/iframe_api';
document.getElementsByTagName('script')[0].parentNode.insertBefore(tag, firstScriptTag);
```

### Commit `1df237b` - Gestion du cache YouTube

**Problème :** API déjà chargée → callback non appelé  
**Solution :** Vérification préalable + polling de secours

```javascript
const ytApiPromise = new Promise(resolve => {
  // 1. Si déjà disponible, résoudre immédiatement
  if (window.YT && window.YT.Player) return resolve();
  
  // 2. Sinon, attendre le callback
  window.onYouTubeIframeAPIReady = () => resolve();
  
  // 3. Polling de secours (15s max)
  let waited = 0;
  const poll = setInterval(() => {
    if (window.YT && window.YT.Player) {
      clearInterval(poll);
      resolve();
    }
    if ((waited += 200) >= 15000) {
      clearInterval(poll);
      console.warn('[YT] API non chargée après 15s');
      resolve();
    }
  }, 200);
});

// Charger le script UNIQUEMENT si pas déjà chargé
if (!window.YT || !window.YT.Player) {
  // injection du script...
}
```

### Commit `9ef0224` - Initialisation systématique de YouTube

**Problème :** YouTube non initialisé si le premier item n'est pas une `music`  
**Solution :** Initialisation délocalisée du code d'initialisation

```javascript
// AVANT : Initialisation uniquement si premier item = music
if (firstItem.type === 'music') {
  radio._ytApiReady.then(() => { 
    if (YT) radio._initYT(); 
  });
}

// APRÈS : Initialisation TOUJOURS appelée
radio._ytApiReady.then(() => {
  if (window.YT && window.YT.Player && !radio.yt) {
    return radio._initYT();
  }
});
```

Amélioration supplémentaire dans `_playAt()` :
```javascript
if (item.type === 'music') {
  if (this.ytReady) {
    this.yt.loadVideoById(item.videoId);
  } else if (this.yt) {
    this._pendingVideo = { videoId: item.videoId, vol: this._vol() };
  } else {
    this._pendingVideo = { videoId: item.videoId, vol: this._vol() };
    this._ytApiReady.then(() => {
      if (window.YT && window.YT.Player && !this.yt) {
        return this._initYT();
      }
    });
  }
}
```

### Commit `5b7b9bc` - Suppression du paramètre `origin`

**Problème :** Erreurs `postMessage` dues à un mismatch d'origine  
**Solution :** Suppression du paramètre obsolète `origin`

```javascript
// AVANT
playerVars: {
  autoplay: 0,
  controls: 1,
  rel: 0,
  modestbranding: 1,
  origin: window.location.origin,  // ❌ Provoquait des erreurs
  enablejsapi: 1
}

// APRÈS
playerVars: {
  autoplay: 0,
  controls: 1,
  rel: 0,
  modestbranding: 1,
  enablejsapi: 1  // ✅ Fonctionne sans 'origin'
}
```

> **Note :** YouTube recommande de ne plus utiliser le paramètre `origin`. Il est obsolète et peut causer des problèmes de communication cross-origin.

---

## 📊 Séquence des commits

| Commit | Date | Message | Problème résolu |
|--------|------|---------|-----------------|
| `e071ab0` | 2026-05-08 | fix(radio): charger YouTube IFrame API dynamiquement après callback | Ordre de chargement incorrect |
| `1df237b` | 2026-05-08 | fix(radio): corrige le cas où YouTube API est déjà chargée | API cache → callback non appelé |
| `9ef0224` | 2026-05-08 | fix(radio): initialise toujours YouTube au démarrage | YouTube non initialisé si 1er item ≠ music |
| `5b7b9bc` | 2026-05-08 | fix(radio): supprime param origin des playerVars YouTube | Erreurs postMessage |

---

## 🎯 Vérification

### Étapes de validation

1. ✅ Workflows GitHub Actions fonctionnels (Flash Info + Horoscope)
2. ✅ `radio_sequence.json` généré et déployé sur GitHub Pages
3. ✅ Player YouTube affiche les vidéos
4. ✅ Pas d'erreurs bloquantes dans la console
5. ✅ Navigation entre les items (musique, liners, transitions) fonctionnelle

### URL de test
https://famibelle.github.io/FlashInfoKarukera/radio.html

---

## 💡 Leçons apprises

1. **L'ordre d'exécution matière** : YouTube IFrame API **requiert** que `onYouTubeIframeAPIReady` soit défini **avant** que le script ne soit chargé.

2. **Gérer le cache** : Toujours vérifier si l'API est déjà chargée avant de la charger.

3. **Initialisation systématique** : Ne pas conditionner l'initialisation de dépendances critiques au type du premier élément.

4. **Paramètres obsolètes** : Vérifier la documentation des APIs tierces (ex: `origin` est déprécié par YouTube).

5. **Logging** : Les erreurs `postMessage` et les warnings `passive event listener` sont visibles dans la console et aident au diagnostic.

---

## 📚 Références

- [YouTube IFrame Player API Documentation](https://developers.google.com/youtube/iframe_player_reference)
- [GitHub Pages Deployment](https://pages.github.com/)
- [MDN: postMessage](https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage)

---

*Document généré par Mistral Vibe - 2026-05-08*
