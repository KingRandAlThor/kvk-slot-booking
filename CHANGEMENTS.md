# Résumé des Modifications - Système de Pré-inscription KVK

## 🎯 Objectif
Transformer le système de réservation directe en un système de pré-inscription où:
- Les utilisateurs se pré-inscrivent avec leur nom et jours de speedup
- Après 1 jour (ou délai configuré), les 20 meilleurs sont automatiquement sélectionnés
- Les autres vont en liste d'attente avec leur position visible
- Seuls les sélectionnés peuvent réserver des créneaux

---

## 📝 Fichiers Modifiés

### 1. **app.py** (Backend principal)

#### Nouvelles constantes
```python
SELECTION_TOP_N = 20  # Nombre de joueurs sélectionnés
```

#### Nouvelles fonctions
- `init_schema(db)` - Crée les tables preregistrations et selection_state
- `get_selection_state(event_date)` - Récupère l'état de sélection
- `set_selection_ready(event_date, ready_at_iso)` - Définit le moment de sélection
- `mark_selection_completed(event_date)` - Marque la sélection comme terminée
- `run_selection_if_ready(event_date)` - Logique principale de sélection

#### Route index() modifiée
- Appel automatique de `run_selection_if_ready()` sur chaque chargement
- Nouvelle action POST `preregister` pour les pré-inscriptions
- Vérification du statut avant autorisation de réservation
- Passage des listes sélectionnés/attente au template

### 2. **templates/index.html** (Interface utilisateur)

#### Ajouts
- Formulaire de pré-inscription (avant la sélection)
- Formulaire de réservation (après sélection, sélectionnés uniquement)
- Table "Sélectionnés (Top 20)" avec nom et speedups
- Table "Liste d'attente" avec position, nom et speedups
- Messages informatifs sur l'état de la sélection

---

## 🗄️ Schéma de Base de Données

### Nouvelle table: `preregistrations`
```sql
CREATE TABLE IF NOT EXISTS preregistrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_date TEXT NOT NULL,
    player_name TEXT NOT NULL,
    speedup_days INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT DEFAULT 'pending',  -- 'pending', 'selected', 'waitlist'
    waitlist_position INTEGER       -- NULL pour sélectionnés, 1-N pour attente
);
```

### Nouvelle table: `selection_state`
```sql
CREATE TABLE IF NOT EXISTS selection_state (
    event_date TEXT PRIMARY KEY,
    ready_at TEXT,              -- Moment où la sélection se déclenche
    completed INTEGER DEFAULT 0, -- 0=non complété, 1=complété
    completed_at TEXT           -- Timestamp de complétion
);
```

---

## 🔄 Flux de Fonctionnement

### Phase 1: Pré-inscription
1. Utilisateur remplit: nom + jours de speedup
2. POST action=`preregister`
3. Insertion dans `preregistrations` avec status='pending'
4. Si première inscription: `ready_at` = now + 1 jour

### Phase 2: Sélection automatique
1. Chaque chargement de page appelle `run_selection_if_ready()`
2. Si `ready_at` atteint ET non complété:
   - Récupère tous les candidats
   - Tri: speedup_days DESC, created_at ASC (FIFO)
   - Top 20 → status='selected', waitlist_position=NULL
   - Suivants → status='waitlist', waitlist_position=1..N
   - Marque completed=1

### Phase 3: Réservation (sélectionnés uniquement)
1. Utilisateur remplit le formulaire de réservation
2. POST action=`reserve`
3. Vérifications:
   - Sélection complétée?
   - Nom dans la table preregistrations?
   - Status='selected'?
4. Si OK → réservation autorisée
5. Sinon → message avec position d'attente

---

## 🧪 Scripts de Test Créés

### Tests et utilitaires
- `test_preregistration.py` - Vérification du schéma et données
- `add_test_data.py` - Ajout de 25 pré-inscriptions test
- `check_selection.py` - Affichage des résultats de sélection
- `debug_selection.py` - Debug de la logique de sélection
- `check_config.py` - Affichage de la configuration
- `fix_event_date.py` - Correction de la date d'événement
- `trigger_selection.py` - Déclenchement manuel via HTTP

### Rapport final
- `TEST_REPORT.md` - Rapport complet des tests effectués

---

## ✅ Validation

### Tests réussis
- ✅ Création des tables
- ✅ Pré-inscription de 25 joueurs
- ✅ Sélection automatique des Top 20
- ✅ Attribution positions d'attente (1-5)
- ✅ Affichage correct dans l'UI
- ✅ Blocage réservations non-sélectionnés
- ✅ Idempotence (une seule sélection)

### Résultats
- 20 joueurs sélectionnés (Alice 100j → Tina 25j)
- 5 en liste d'attente (Uma pos.1 → Yuki pos.5)
- Sélection complétée: 2025-12-07 09:59:28 UTC

---

## 🚀 Déploiement

### Prérequis
- Flask installé (`pip install -r requirements.txt`)
- Base de données SQLite (kvk.db)
- Les nouvelles tables sont créées automatiquement au premier lancement

### Lancement
```bash
python app.py
```

L'application sera accessible sur http://127.0.0.1:5000

---

## 📌 Points Importants

1. **SELECTION_TOP_N = 20** est configurable
2. La sélection se déclenche automatiquement (pas de cron nécessaire)
3. Une sélection par événement (pas de duplication)
4. Le tri privilégie les speedups, puis FIFO
5. Les positions d'attente sont dynamiques et visibles
6. L'UI est adaptée au thème (Christmas/Kingshot)

---

## 🎨 Interface Utilisateur

### Avant sélection
- Formulaire "Pré-enregistrement" visible
- Message avec le temps restant
- Formulaire réservation grisé/bloqué

### Après sélection
- Table "Sélectionnés (Top 20)"
- Table "Liste d'attente"
- Formulaire réservation actif (sélectionnés)
- Messages d'erreur si non sélectionné

---

**Version**: 2.0 - Système de pré-inscription avec sélection Top 20  
**Date**: 7 décembre 2025  
**Status**: ✅ Testé et validé
