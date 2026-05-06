# Analyse Stratégique — FlashInfoKarukera

*Expertise radio & audience growth pour la diaspora caribéenne au Luxembourg*

---

## 📊 Diagnostic Actuel

### Grille de Programmation

| Format | Durée | Fréquence | Persona | Points Forts | Risques |
|--------|-------|-----------|---------|--------------|---------|
| **Flash Info** | ~2-3 min | Hebdomadaire | Harry | Actualité fraîche, ton punchy | Peut sembler répétitif |
| **Horoscope** | ~2-3 min | Hebdomadaire | Maryse | Engagement émotionnel, fidélisation | Format statique |
| **Capsules** | 15-20s | Multiple/jour | Solitude | Variété culturelle, digestible | **Trop court** pour impact |
| **Émission Culturelle** | 10-15 min | Hebdomadaire | Monique | Profondeur, identité forte | **Trop long** pour radio digitale |
| **Liners** | 5-10s | Transition | Corinne | Lien entre segments | Souvent ignorés |

### Problèmes Identifiés

1. **Durées inadaptées** :
   - Capsules de 15s = invisibles dans le flux
   - Émissions de 10-15 min = taux de drop élevé (attention moyenne : 3-5 min)

2. **Segmentation excessive** : Pas de fluidité entre les formats

3. **Manque de signature sonore** : Pas de jingles distinctifs

4. **CTA inefficaces** : Pas de calls-to-action stratégiques

---

## 🎯 10 Conseils pour Captiver l'Audience

### 1. 🔄 Réorganiser la Rotation (Priorité)

**Grille optimisée (cycle de 1h) :**
```
00:00 - Liner d'accroche (Corinne)
00:10 - Capsule Culturelle (Solitude, 20-25s)
00:30 - Flash Info (Harry, 2 min)
02:40 - Liner de transition
02:50 - Extrait Émission (Monique, 3-4 min)
06:30 - Horoscope (Maryse, 2 min)
08:40 - Liner + CTA
```

**Pourquoi ?** Alterner rythme rapide (capsules/liners) et contenu profond.

### 2. ⏳ Optimiser les Durées

| Format | Durée Actuelle | Durée Idéale | Impact |
|--------|----------------|--------------|--------|
| Capsules | 15-20s | **20-25s** | +30% rétention |
| Émissions | 10-15 min | **3-5 min (extraits)** | -50% taux de drop |
| Liners | 5-10s | **7-10s** | Message clair sans lasser |

### 3. 🎤 Renforcer l'Identité Vocale

- **Jingles d'intro** : 2-3s par format (vagues pour Solitude, tonnerre pour Harry)
- **Voix cohérente** : Même voix TTS pour tous les liners
- **Signature sonore** : Bip de 0.5s avant chaque capsule

### 4. 🔗 Créer des Ponts entre Formats

**Technique du "Teasing" :**
```
Fin Flash Info → "Et demain, Solitude vous révèlera l'histoire du rhum arrangé…"
Horoscope → "Un conseil pour les Taureau : écoutez le Flash Info de demain !"
```

### 5. 📢 Call-To-Action Stratégiques

| Moment | CTA | Exemple |
|--------|-----|---------|
| Fin Flash Info | Partage | "Un scoop ? DM @FlashInfoKarukera !" |
| Fin Horoscope | Engagement | "Quel est votre signe ? Dites-le en commentaire !" |
| Fin Capsule | Découverte | "Émission complète ce soir à 18h" |
| Liners | Fidélisation | "Abonnez-vous pour ne rien rater !" |

**Règle d'or** : 1 CTA par segment maximum.

### 6. 🎶 Musiquer les Transitions

- Fond sonore léger (-12dB) pendant les liners
- Sweeps (0.5s) entre les segments
- Exemple : `[FIN FLASH] → [SWEEP] → [LINER] → [SWEEP] → [CAPSULE]`

### 7. 📅 Créer des Rendez-Vous Fixes

| Jour | Matin | Midi | Soir |
|------|-------|------|------|
| **Lundi** | Flash Info | Horoscope | Émission (extraits) |
| **Mardi** | Capsule Histoire | Flash Info | Horoscope + Teasing |
| **Mercredi** | Flash Info | Capsule Musique | Émission Spéciale |
| **Jeudi** | Horoscope | Capsule Cuisine | Flash Info Réactions |
| **Vendredi** | Capsule Tourisme | Flash Info | Best-Of |

### 8. 🔄 Recycler le Contenu

Transformer les émissions longues en capsules :
- Émission de 10 min → 3-4 capsules de 20-25s
- Exemple : "Les origines du carnival", "Les costumes", "La musique"

**Bénéfice** : Maximiser le ROI sans redondance.

### 9. 🎯 Cibler les Moments Clés

| Moment | Besoin | Format |
|--------|--------|--------|
| 7h-9h (Réveil) | Infos rapides | Flash Info + Horoscope |
| 12h-14h (Pause Déj) | Détente | Capsules Culture + Musique |
| 18h-20h (Retour) | Approfondissement | Extraits Émission + Interviews |
| 22h+ (Soirée) | Ambiance | Capsules Musicales |

### 10. 📊 Mesurer et Ajuster

**Métriques à suivre :**
- Taux d'écoute complet → raccourcir les segments si ⬇️
- Taux de partage → ajouter CTA si ⬇️
- Temps moyen d'écoute → réorganiser la grille si ⬇️
- Taux de rebond → améliorer les transitions si ⬇️

**Test A/B :**
- Version A : Capsules de 15s
- Version B : Capsules de 20-25s
- Mesurer le taux de rétention.

---

## 🛠️ Actions Immédiates à Implémenter

### Priorité 1 : Modifier les Templates

```bash
# Dans private/prompts/solitude_capsule.md
# Changer :
"15-20 mots" → "20-25 mots"
"~15s" → "~20-25s"
```

### Priorité 2 : Découper les Émissions

Créer un script `split_emission.py` :
```python
def split_emission(text, max_words=400):  # ~3-4 min
    sentences = text.split('. ')
    chunks = []
    current_chunk = []
    for sentence in sentences:
        if len(' '.join(current_chunk + [sentence]).split()) <= max_words:
            current_chunk.append(sentence)
        else:
            chunks.append('. '.join(current_chunk) + '.')
            current_chunk = [sentence]
    return chunks
```

### Priorité 3 : Ajouter Jingles et Transitions

Structure :
```
assets/jingles/
├── intro_flashinfo.mp3 (2s)
├── intro_horoscope.mp3 (2s)
├── intro_capsule.mp3 (2s)
└── transition.mp3 (0.5s)
```

### Priorité 4 : Automatiser les CTA

Dans chaque template :
```markdown
[CTA: "Pour plus d'histoires, abonnez-vous à notre newsletter !"]
```

---

## 📌 Résumé des Changements Critiques

| Élément | Action | Impact Attendu |
|---------|--------|----------------|
| Durée Capsules | 15s → 20-25s | +30% rétention |
| Émissions Culturelles | 10-15 min → 3-5 min | -50% taux de drop |
| Grille Hebdo | Rotation intelligente | +40% écoutes répétées |
| Jingles | Ajout systématique | +25% reconnaissance |
| CTA | 1 par segment | +20% engagement |

---

## 🎯 Team Editorial

| Rôle | Persona | Fichier Prompt | Durée Cible |
|------|----------|----------------|-------------|
| Flash Info | Harry | `harry_flash_info.md` | 2-3 min |
| Horoscope | Maryse | `maryse_horoscope.md` | 2-3 min |
| Capsules | Solitude | `solitude_capsule.md` | **20-25s** |
| Émission Culturelle | Monique | `monique_ame.md` + `monique.md` + `emission_instruction.md` | **3-5 min (extraits)** |
| Liners | Corinne | `corinne_liner.md` | 7-10s |

---

## 📚 Contraintes Techniques

### TTS Voxtral Compatibility
- **Interdit** : `[ ]`, `*`, listes numérotées, markdown, métadonnées
- **Autorisé** : Texte pur ASCII + ponctuation française standard
- **Durée** : 20-25 mots/phrase pour fluidité

### Workflow
- Vérifier existence fichiers avant régénération
- Commit avec `[skip ci]` pour éviter boucles
- Sequential execution : `needs:` dans GitHub Actions

---

## 📈 Prochaines Étapes

- [ ] Tester grille avec nouvelles durées
- [ ] Produire jingles audio
- [ ] Implémenter CTA automatiques
- [ ] Mesurer impact sur 2 semaines
- [ ] A/B test capsules 15s vs 20-25s
