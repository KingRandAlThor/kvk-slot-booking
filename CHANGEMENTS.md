# Historique des modifications

## 2.0 — Pré-inscription et sélection du Top 20 (décembre 2025)

Avant cette version, les joueurs réservaient directement un créneau. La réservation passe désormais par une pré-inscription : après un délai, les 20 meilleurs sont sélectionnés et les autres rejoignent une liste d'attente.

### Fonctionnement

1. **Pré-inscription** : le joueur saisit son nom et son nombre de jours de speedup. À la première inscription, `ready_at` est fixé à maintenant + 1 jour.
2. **Sélection** : à chaque chargement de page, `run_selection_if_ready()` vérifie si `ready_at` est atteint. Si oui, les candidats sont triés par `speedup_days` décroissant puis `created_at` croissant. Les 20 premiers passent en `selected`, les suivants en `waitlist` avec leur position. La sélection n'a lieu qu'une fois par événement.
3. **Réservation** : seuls les joueurs `selected` peuvent réserver. Les autres voient leur position en liste d'attente.

### Code

- `app.py` : constante `SELECTION_TOP_N`, fonctions `init_schema`, `get_selection_state`, `set_selection_ready`, `mark_selection_completed`, `run_selection_if_ready`, et nouvelle action `preregister` dans la route `index()`.
- `templates/index.html` : formulaire de pré-inscription, tableaux « Sélectionnés » et « Liste d'attente », messages d'état de la sélection.

### Base de données

```sql
CREATE TABLE IF NOT EXISTS preregistrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_date TEXT NOT NULL,
    player_name TEXT NOT NULL,
    speedup_days INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT DEFAULT 'pending',   -- pending, selected, waitlist
    waitlist_position INTEGER        -- NULL pour les sélectionnés
);

CREATE TABLE IF NOT EXISTS selection_state (
    event_date TEXT PRIMARY KEY,
    ready_at TEXT,                   -- moment du déclenchement
    completed INTEGER DEFAULT 0,
    completed_at TEXT
);
```

Les tables sont créées automatiquement au premier lancement.

### Vérifications effectuées

Test avec 25 pré-inscriptions : les 20 premiers (de 100 à 25 jours de speedup) sont sélectionnés, les 5 suivants prennent les positions 1 à 5 de la liste d'attente, les joueurs non sélectionnés ne peuvent pas réserver, et une seconde exécution ne refait pas la sélection.
