from flask import Flask, render_template, g, request, redirect, url_for, flash
import sqlite3
import os
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(__file__)
DATABASE = os.path.join(BASE_DIR, 'kvk.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        init_schema(db)
    return db


def init_schema(db):
    cur = db.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS preregistrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date TEXT NOT NULL,
            event_day TEXT DEFAULT 'monday',
            player_name TEXT NOT NULL,
            speedup_days INTEGER NOT NULL,
            preferred_slots TEXT NOT NULL,
            created_at TEXT NOT NULL,
            assigned_slot TEXT,
            list_type TEXT DEFAULT 'main'
        );
        """
    )
    # Ajouter la colonne list_type si elle n'existe pas déjà
    try:
        cur.execute("ALTER TABLE preregistrations ADD COLUMN list_type TEXT DEFAULT 'main';")
    except:
        pass  # Colonne existe déjà
    # Ajouter la colonne event_day si elle n'existe pas déjà
    try:
        cur.execute("ALTER TABLE preregistrations ADD COLUMN event_day TEXT DEFAULT 'monday';")
    except:
        pass  # Colonne existe déjà
    # Ajouter la colonne preferred_slots si elle n'existe pas déjà
    try:
        cur.execute("ALTER TABLE preregistrations ADD COLUMN preferred_slots TEXT;")
    except:
        pass  # Colonne existe déjà
    # Ajouter la colonne assigned_slot si elle n'existe pas déjà
    try:
        cur.execute("ALTER TABLE preregistrations ADD COLUMN assigned_slot TEXT;")
    except:
        pass  # Colonne existe déjà
    
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS selection_state (
            event_date TEXT PRIMARY KEY,
            ready_at TEXT,
            completed INTEGER DEFAULT 0,
            completed_at TEXT
        );
        """
    )
    
    # Create conflicts table for manual resolution
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS slot_conflicts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date TEXT NOT NULL,
            event_day TEXT NOT NULL,
            slot_iso TEXT NOT NULL,
            player_names TEXT NOT NULL,
            speedup_days INTEGER NOT NULL,
            resolved INTEGER DEFAULT 0,
            winner TEXT
        );
        """
    )
    
    # Create reservations table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date TEXT NOT NULL,
            event_day TEXT DEFAULT 'monday',
            player_name TEXT NOT NULL,
            slot_index INTEGER NOT NULL,
            speedup_days INTEGER NOT NULL,
            reserved_at TEXT NOT NULL,
            list_type TEXT DEFAULT 'main'
        );
        """
    )
    
    # Create config table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )
    
    # Create training_players table for KVK Training team balancer
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS training_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            power REAL NOT NULL,
            alliance TEXT NOT NULL,
            infantry_tg INTEGER DEFAULT 0,
            archery_tg INTEGER DEFAULT 0,
            cavalry_tg INTEGER DEFAULT 0,
            team INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    
    db.commit()

app = Flask(__name__)
app.secret_key = 'dev-secret'

# Add custom Jinja2 filter for JSON parsing
import json
@app.template_filter('from_json')
def from_json_filter(value):
    """Parse JSON string to Python object"""
    if not value:
        return []
    try:
        return json.loads(value)
    except:
        return []

SLOT_MIN_SPEEDUP_DAYS = 20
DEFAULT_EVENT_DATE = '2025-12-02'  # YYYY-MM-DD format
ADMIN_PASSWORD = 'kvk2025'  # Change this to your desired password
SELECTION_TOP_N = 20

# Event types by weekday (0=Monday, 1=Tuesday, etc.)
EVENT_TYPES = {
    0: {'name': 'Construction', 'emoji': '🏗️'},
    1: {'name': 'Research', 'emoji': '🔬'},
    3: {'name': 'Troop Training', 'emoji': '⚔️', 'dual_list': True},  # Jeudi = double liste
}

def is_dual_list_event(weekday):
    """Check if event has dual list system (main + secondary)"""
    return EVENT_TYPES.get(weekday, {}).get('dual_list', False)

def get_event_date(day='monday'):
    """Get event date from config table for specific day, or use default."""
    db = get_db()
    cur = db.cursor()
    config_key = f'event_date_{day}'
    cur.execute("SELECT value FROM config WHERE key = ?;", (config_key,))
    row = cur.fetchone()
    if row:
        return row['value']
    return DEFAULT_EVENT_DATE

def set_event_date(date_str: str, day='monday'):
    """Set event date in config table for specific day."""
    db = get_db()
    cur = db.cursor()
    config_key = f'event_date_{day}'
    cur.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?);",(config_key, date_str))
    db.commit()

def get_registration_open(day='monday'):
    """Get registration open datetime from config table for specific day."""
    db = get_db()
    cur = db.cursor()
    config_key = f'registration_open_{day}'
    cur.execute("SELECT value FROM config WHERE key = ?;", (config_key,))
    row = cur.fetchone()
    if row:
        return row['value']
    return None  # None means always open

def set_registration_open(datetime_str: str, day='monday'):
    """Set registration open datetime in config table for specific day."""
    db = get_db()
    cur = db.cursor()
    config_key = f'registration_open_{day}'
    cur.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?);",(config_key, datetime_str))
    db.commit()

def clear_registration_open(day='monday'):
    """Clear registration open datetime for specific day (make registrations always open)."""
    db = get_db()
    cur = db.cursor()
    config_key = f'registration_open_{day}'
    cur.execute("DELETE FROM config WHERE key = ?;", (config_key,))
    db.commit()

def get_current_theme():
    """Get current theme - auto-detect Christmas season or use config."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT value FROM config WHERE key = 'theme';")
    row = cur.fetchone()
    if row:
        return row['value']
    # Auto-detect: December = Christmas theme
    now = datetime.now()
    if now.month == 12:
        return 'christmas'
    return 'kingshot'

def set_theme(theme: str):
    """Set theme in config table."""
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('theme', ?);",(theme,))
    db.commit()


def get_selection_state(event_date: str):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT ready_at, completed, completed_at FROM selection_state WHERE event_date = ?;", (event_date,))
    row = cur.fetchone()
    if row:
        return {'ready_at': row['ready_at'], 'completed': bool(row['completed']), 'completed_at': row['completed_at']}
    return None


def set_selection_ready(event_date: str, ready_at_iso: str):
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT OR REPLACE INTO selection_state (event_date, ready_at, completed) VALUES (?, ?, COALESCE((SELECT completed FROM selection_state WHERE event_date = ?), 0));",
                (event_date, ready_at_iso, event_date))
    db.commit()


def mark_selection_completed(event_date: str):
    db = get_db()
    cur = db.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()
    cur.execute("UPDATE selection_state SET completed = 1, completed_at = ? WHERE event_date = ?;", (now_iso, event_date))
    db.commit()


def optimize_slot_assignments(event_date: str, event_day: str):
    """
    Algorithme d'optimisation pour attribuer les créneaux.
    Utilise l'algorithme hongrois pour maximiser le total de speedups.
    - 1 créneau maximum par joueur
    - 1 joueur maximum par créneau
    - Pour jeudi (dual list) : optimise d'abord la liste principale, puis la liste secondaire avec les joueurs restants
    """
    db = get_db()
    cur = db.cursor()
    
    # Vérifier si c'est un événement dual-list (jeudi)
    is_dual = (event_day == 'thursday')
    
    # PHASE 1 : Optimisation de la liste principale
    # Récupérer les pré-inscriptions pour la liste principale
    if is_dual:
        cur.execute(
            "SELECT id, player_name, speedup_days, preferred_slots, list_type FROM preregistrations WHERE event_date = ? AND event_day = ? AND list_type = 'main';",
            (event_date, event_day)
        )
    else:
        cur.execute(
            "SELECT id, player_name, speedup_days, preferred_slots, list_type FROM preregistrations WHERE event_date = ? AND event_day = ?;",
            (event_date, event_day)
        )
    
    preregistrations = cur.fetchall()
    
    if not preregistrations:
        db.commit()
        return 0
    
    import json
    from scipy.optimize import linear_sum_assignment
    import numpy as np
    
    # Construire le mapping joueur -> préférences
    players = []
    all_slots = set()
    player_preferences = {}
    
    for prereg in preregistrations:
        player_id = prereg['id']
        player_name = prereg['player_name']
        speedup_days = prereg['speedup_days']
        list_type = prereg['list_type']
        try:
            preferred_slots = json.loads(prereg['preferred_slots'])
        except:
            preferred_slots = []
        
        if not preferred_slots:
            continue
            
        players.append({
            'id': player_id,
            'name': player_name,
            'speedups': speedup_days,
            'list_type': list_type
        })
        
        # Ajouter les slots préférés avec list_type
        player_prefs = []
        for slot in preferred_slots:
            slot_key = f"{slot}_{list_type}"
            all_slots.add(slot_key)
            player_prefs.append(slot_key)
        
        player_preferences[player_id] = {
            'slots': player_prefs,
            'speedups': speedup_days
        }
    
    if not players or not all_slots:
        db.commit()
        return 0
    
    # Créer les listes indexées
    slot_list = sorted(list(all_slots))
    player_list = players
    
    # Construire la matrice de coûts (on veut maximiser, donc on utilise les speedups)
    # Taille: nb_players x nb_slots
    cost_matrix = np.full((len(player_list), len(slot_list)), -1e9, dtype=float)
    
    for p_idx, player in enumerate(player_list):
        player_id = player['id']
        speedups = player['speedups']
        prefs = player_preferences[player_id]['slots']
        
        for slot_key in prefs:
            if slot_key in slot_list:
                s_idx = slot_list.index(slot_key)
                cost_matrix[p_idx, s_idx] = speedups
    
    # Utiliser l'algorithme hongrois pour maximiser (on inverse les coûts)
    row_ind, col_ind = linear_sum_assignment(cost_matrix, maximize=True)
    
    # Extraire les assignations valides (coût > 0)
    assignments = {}
    assigned_players = set()
    
    for p_idx, s_idx in zip(row_ind, col_ind):
        if cost_matrix[p_idx, s_idx] > 0:
            player = player_list[p_idx]
            slot_key = slot_list[s_idx]
            # Extraire le slot ISO (enlever le suffix _list_type)
            slot_iso = slot_key.rsplit('_', 1)[0]
            
            assignments[player['id']] = {
                'slot_iso': slot_iso,
                'player_name': player['name'],
                'speedups': player['speedups']
            }
            assigned_players.add(player['id'])
    
    # Enregistrer les attributions de la liste principale dans la DB
    for player_id, assignment in assignments.items():
        cur.execute(
            "UPDATE preregistrations SET assigned_slot = ? WHERE id = ?;",
            (assignment['slot_iso'], player_id)
        )
    
    # Copier les assignations vers la table reservations pour affichage
    cur.execute("DELETE FROM reservations WHERE event_date LIKE ? AND event_day = ?;", (event_date + '%', event_day))
    
    for player_id, assignment in assignments.items():
        # Récupérer les infos du joueur
        cur.execute("SELECT list_type FROM preregistrations WHERE id = ?;", (player_id,))
        player_data = cur.fetchone()
        list_type = player_data['list_type'] if player_data else 'main'
        
        now = datetime.now(timezone.utc)
        cur.execute(
            'INSERT INTO reservations (event_date, event_day, player_name, speedup_days, reserved_at, list_type, slot_index) VALUES (?, ?, ?, ?, ?, ?, ?);',
            (assignment['slot_iso'], event_day, assignment['player_name'], assignment['speedups'], now.isoformat(), list_type, 0)
        )
    
    # PHASE 2 : Pour jeudi uniquement, optimiser la liste secondaire avec les joueurs restants
    if is_dual:
        # Récupérer TOUS les joueurs qui se sont pré-inscrits
        cur.execute(
            "SELECT id, player_name, speedup_days, preferred_slots FROM preregistrations WHERE event_date = ? AND event_day = ?;",
            (event_date, event_day)
        )
        all_preregistrations = cur.fetchall()
        
        # Filtrer les joueurs qui n'ont PAS obtenu de créneau (assigned_slot is NULL)
        remaining_players = []
        for prereg in all_preregistrations:
            cur.execute("SELECT assigned_slot FROM preregistrations WHERE id = ?;", (prereg['id'],))
            result = cur.fetchone()
            if result and (result['assigned_slot'] is None or result['assigned_slot'] == ''):
                remaining_players.append(prereg)
        
        # Si des joueurs restants, les mettre dans la liste secondaire et optimiser
        if remaining_players:
            # Mettre à jour list_type = 'secondary' pour ces joueurs
            for prereg in remaining_players:
                cur.execute(
                    "UPDATE preregistrations SET list_type = 'secondary' WHERE id = ?;",
                    (prereg['id'],)
                )
            
            # Relancer l'optimisation pour la liste secondaire
            players_secondary = []
            all_slots_secondary = set()
            player_preferences_secondary = {}
            
            for prereg in remaining_players:
                player_id = prereg['id']
                player_name = prereg['player_name']
                speedup_days = prereg['speedup_days']
                try:
                    preferred_slots = json.loads(prereg['preferred_slots'])
                except:
                    preferred_slots = []
                
                if not preferred_slots:
                    continue
                    
                players_secondary.append({
                    'id': player_id,
                    'name': player_name,
                    'speedups': speedup_days,
                    'list_type': 'secondary'
                })
                
                # Ajouter les slots préférés avec list_type = 'secondary'
                player_prefs = []
                for slot in preferred_slots:
                    slot_key = f"{slot}_secondary"
                    all_slots_secondary.add(slot_key)
                    player_prefs.append(slot_key)
                
                player_preferences_secondary[player_id] = {
                    'slots': player_prefs,
                    'speedups': speedup_days
                }
            
            if players_secondary and all_slots_secondary:
                # Créer les listes indexées pour la liste secondaire
                slot_list_secondary = sorted(list(all_slots_secondary))
                player_list_secondary = players_secondary
                
                # Construire la matrice de coûts pour la liste secondaire
                cost_matrix_secondary = np.full((len(player_list_secondary), len(slot_list_secondary)), -1e9, dtype=float)
                
                for p_idx, player in enumerate(player_list_secondary):
                    player_id = player['id']
                    speedups = player['speedups']
                    prefs = player_preferences_secondary[player_id]['slots']
                    
                    for slot_key in prefs:
                        if slot_key in slot_list_secondary:
                            s_idx = slot_list_secondary.index(slot_key)
                            cost_matrix_secondary[p_idx, s_idx] = speedups
                
                # Algorithme hongrois pour la liste secondaire
                row_ind_secondary, col_ind_secondary = linear_sum_assignment(cost_matrix_secondary, maximize=True)
                
                # Extraire les assignations valides pour la liste secondaire
                assignments_secondary = {}
                
                for p_idx, s_idx in zip(row_ind_secondary, col_ind_secondary):
                    if cost_matrix_secondary[p_idx, s_idx] > 0:
                        player = player_list_secondary[p_idx]
                        slot_key = slot_list_secondary[s_idx]
                        # Extraire le slot ISO (enlever le suffix _secondary)
                        slot_iso = slot_key.rsplit('_', 1)[0]
                        
                        assignments_secondary[player['id']] = {
                            'slot_iso': slot_iso,
                            'player_name': player['name'],
                            'speedups': player['speedups']
                        }
                
                # Enregistrer les attributions de la liste secondaire
                for player_id, assignment in assignments_secondary.items():
                    cur.execute(
                        "UPDATE preregistrations SET assigned_slot = ? WHERE id = ?;",
                        (assignment['slot_iso'], player_id)
                    )
                    
                    now = datetime.now(timezone.utc)
                    cur.execute(
                        'INSERT INTO reservations (event_date, event_day, player_name, speedup_days, reserved_at, list_type, slot_index) VALUES (?, ?, ?, ?, ?, ?, ?);',
                        (assignment['slot_iso'], event_day, assignment['player_name'], assignment['speedups'], now.isoformat(), 'secondary', 0)
                    )
    
    # Pas de conflits avec l'algorithme hongrois
    cur.execute("DELETE FROM slot_conflicts WHERE event_date = ? AND event_day = ?;", (event_date, event_day))
    
    db.commit()
    return 0


def run_selection_if_ready(event_date: str, event_day: str):
    """If selection time is reached and not completed, run optimization algorithm."""
    state = get_selection_state(event_date)
    if not state or not state.get('ready_at') or state.get('completed'):
        return state

    try:
        ready_at_dt = datetime.fromisoformat(state['ready_at']).replace(tzinfo=timezone.utc)
    except Exception:
        return state

    if datetime.now(timezone.utc) < ready_at_dt:
        return state

    # Lancer l'optimisation
    num_conflicts = optimize_slot_assignments(event_date, event_day)
    
    mark_selection_completed(event_date)
    return get_selection_state(event_date)

def slot_aligned(dt: datetime) -> bool:
    return dt.second == 0 and dt.minute in (0, 30)

def parse_iso_slot(s: str) -> datetime:
    # Expect ISO with or without timezone info
    try:
        if s.endswith('Z'):
            s = s[:-1]
        # Handle +00:00 suffix
        if '+' in s:
            s = s.split('+')[0]
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except Exception:
        return None

def slots_between(start: datetime, end: datetime):
    cur = start
    while cur < end:
        yield cur
        cur += timedelta(minutes=30)

@app.route('/', methods=['GET', 'POST'])
def home():
    """Page d'accueil avec choix du jour"""
    theme = get_current_theme()
    return render_template('home.html', theme=theme)

@app.route('/event', methods=['GET', 'POST'])
@app.route('/event/<day>', methods=['GET', 'POST'])
def index(day='monday'):
    """Booking page for specific event day"""
    # Valider le jour
    valid_days = ['monday', 'tuesday', 'thursday']
    if day not in valid_days:
        flash('Invalid event day. Redirecting to Monday.', 'error')
        return redirect(url_for('index', day='monday'))
    
    # Get event date from config for this day
    event_date_str = get_event_date(day)
    try:
        event_date_parts = [int(p) for p in event_date_str.split('-')]
        event_start = datetime(event_date_parts[0], event_date_parts[1], event_date_parts[2], 0, 0, 0, tzinfo=timezone.utc)
    except Exception:
        event_start = datetime(2025, 12, 2, 0, 0, 0, tzinfo=timezone.utc)
    event_end = event_start.replace(hour=23, minute=59)

    # Check if registrations are open for this day
    registration_open_str = get_registration_open(day)
    registrations_open = True
    countdown_target = None

    if registration_open_str:
        try:
            open_dt = datetime.fromisoformat(registration_open_str)
            # Ensure timezone is set
            if open_dt.tzinfo is None:
                open_dt = open_dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            if now < open_dt:
                registrations_open = False
                countdown_target = registration_open_str
        except Exception:
            pass

    db = get_db()
    cur = db.cursor()

    # Run selection if the deadline is reached
    selection_state = run_selection_if_ready(event_date_str, day)
    
    # Check if this is a dual-list event (Thursday)
    # Thursday = weekday 3
    is_dual = (day == 'thursday')
    is_dual_list = is_dual

    action = request.form.get('action', '') if request.method == 'POST' else ''

    # Handle pre-registration with slot selection
    if request.method == 'POST' and action in ('preregister', 'preregister_secondary'):
        import json
        player_name = request.form.get('player_name', '').strip()
        list_type = 'secondary' if action == 'preregister_secondary' else 'main'
        
        try:
            speedup_days = int(request.form.get('speedup_days', '0'))
        except ValueError:
            speedup_days = 0
        
        # Récupérer les créneaux sélectionnés
        selected_slots = request.form.getlist('selected_slots[]')

        if not player_name:
            flash('Name is required to pre-register.', 'error')
        elif speedup_days <= 0 and list_type == 'main':
            flash('Speedup days must be a positive number.', 'error')
        elif not selected_slots:
            flash('You must select at least one preferred slot.', 'error')
        else:
            # Check if player already registered in ANY list
            cur.execute(
                "SELECT id, list_type FROM preregistrations WHERE event_date = ? AND event_day = ? AND player_name = ? LIMIT 1;",
                (event_date_str, day, player_name)
            )
            existing = cur.fetchone()
            
            if existing:
                # Update existing registration
                preferred_slots_json = json.dumps(selected_slots)
                cur.execute(
                    'UPDATE preregistrations SET speedup_days = ?, preferred_slots = ? WHERE id = ?;',
                    (speedup_days, preferred_slots_json, existing['id'])
                )
                db.commit()
                flash(f'Pre-registration updated with {len(selected_slots)} preferred slots!', 'success')
            else:
                # New registration
                now = datetime.now(timezone.utc)
                preferred_slots_json = json.dumps(selected_slots)
                cur.execute(
                    'INSERT INTO preregistrations (event_date, event_day, player_name, speedup_days, preferred_slots, created_at, list_type) VALUES (?, ?, ?, ?, ?, ?, ?);',
                    (event_date_str, day, player_name, speedup_days, preferred_slots_json, now.isoformat(), list_type)
                )
                db.commit()
                
                # If this is the first prereg for this event, set selection ready time to +1 day
                state = get_selection_state(event_date_str)
                if not state or not state.get('ready_at'):
                    ready_at = (now + timedelta(days=1)).isoformat()
                    set_selection_ready(event_date_str, ready_at)
                    selection_state = get_selection_state(event_date_str)
                
                list_msg = 'secondary list' if list_type == 'secondary' else 'main list'
                flash(f'Pre-registration saved in {list_msg} with {len(selected_slots)} preferred slots! Optimization will run in 24h.', 'success')

    # Handle pre-registration (OLD - keep for compatibility)
    elif request.method == 'POST' and action == 'preregister_old_compat':
        player_name = request.form.get('player_name', '').strip()
        try:
            speedup_days = int(request.form.get('speedup_days', '0'))
        except ValueError:
            speedup_days = 0

        if not player_name:
            flash('Name is required to pre-register.', 'error')
        elif speedup_days <= 0:
            flash('Speedup days must be a positive number.', 'error')
        else:
            now = datetime.now(timezone.utc)
            cur.execute(
                'INSERT INTO preregistrations (event_date, event_day, player_name, speedup_days, created_at, status, list_type) VALUES (?, ?, ?, ?, ?, ?, ?);',
                (event_date_str, day, player_name, speedup_days, now.isoformat(), 'pending', 'main')
            )
            db.commit()
            # If this is the first prereg for this event, set selection ready time to +1 day
            state = get_selection_state(event_date_str)
            if not state or not state.get('ready_at'):
                ready_at = (now + timedelta(days=1)).isoformat()
                set_selection_ready(event_date_str, ready_at)
                selection_state = get_selection_state(event_date_str)
            flash('Pre-registration saved! Selection will pick the top 20 once the timer ends.', 'success')

    # Handle switch from waitlist to secondary list
    if request.method == 'POST' and action == 'switch_to_secondary':
        player_name = request.form.get('player_name', '').strip()
        
        if not player_name:
            flash('Player name is required.', 'error')
        else:
            # Check player exists and is on waitlist
            cur.execute(
                "SELECT id, status FROM preregistrations WHERE event_date = ? AND event_day = ? AND player_name = ? AND list_type = 'main' LIMIT 1;",
                (event_date_str, day, player_name)
            )
            row = cur.fetchone()
            
            if not row:
                flash('Player not found in main list.', 'error')
            elif row['status'] not in ('selected', 'waitlist'):
                flash('Only selected or waitlisted players can switch to secondary list.', 'error')
            else:
                was_selected = row['status'] == 'selected'
                
                # Switch to secondary list
                cur.execute(
                    "UPDATE preregistrations SET list_type = 'secondary', status = 'selected', waitlist_position = NULL WHERE id = ?;",
                    (row['id'],)
                )
                
                # If a selected player switched, promote first waitlist player
                if was_selected:
                    # Get first waitlist player
                    cur.execute(
                        """SELECT id FROM preregistrations 
                        WHERE event_date = ? AND event_day = ? AND list_type = 'main' AND status = 'waitlist' 
                        ORDER BY waitlist_position ASC LIMIT 1;""",
                        (event_date_str, day)
                    )
                    first_waitlist = cur.fetchone()
                    
                    if first_waitlist:
                        # Promote to selected
                        cur.execute(
                            "UPDATE preregistrations SET status = 'selected', waitlist_position = NULL WHERE id = ?;",
                            (first_waitlist['id'],)
                        )
                        # Recalculate waitlist positions
                        cur.execute(
                            """SELECT id FROM preregistrations 
                            WHERE event_date = ? AND event_day = ? AND list_type = 'main' AND status = 'waitlist' 
                            ORDER BY speedup_days DESC, datetime(created_at) ASC;""",
                            (event_date_str, day)
                        )
                        remaining_waitlist = cur.fetchall()
                        for pos, wl_row in enumerate(remaining_waitlist, start=1):
                            cur.execute(
                                "UPDATE preregistrations SET waitlist_position = ? WHERE id = ?;",
                                (pos, wl_row['id'])
                            )
                        
                        # Get promoted player name
                        cur.execute("SELECT player_name FROM preregistrations WHERE id = ?;", (first_waitlist['id'],))
                        promoted_name = cur.fetchone()['player_name']
                        flash(f'{player_name} switched to secondary list. {promoted_name} promoted to Top 20!', 'success')
                    else:
                        flash(f'{player_name} switched to secondary list!', 'success')
                else:
                    # Just recalculate waitlist positions
                    cur.execute(
                        """SELECT id FROM preregistrations 
                        WHERE event_date = ? AND event_day = ? AND list_type = 'main' AND status = 'waitlist' 
                        ORDER BY speedup_days DESC, datetime(created_at) ASC;""",
                        (event_date_str, day)
                    )
                    remaining_waitlist = cur.fetchall()
                    for pos, wl_row in enumerate(remaining_waitlist, start=1):
                        cur.execute(
                            "UPDATE preregistrations SET waitlist_position = ? WHERE id = ?;",
                            (pos, wl_row['id'])
                        )
                    flash(f'{player_name} switched to secondary list!', 'success')
                
                db.commit()
                # Re-run to get updated state
                selection_state = get_selection_state(event_date_str)

    # Handle reservation POST (only if registrations open and selection allows)
    if request.method == 'POST' and action in ('reserve', 'move') and registrations_open:
        # Move reservation action
        if action == 'move':
            password = request.form.get('password', '').strip()
            if password != ADMIN_PASSWORD:
                flash('Incorrect admin password.', 'error')
            else:
                old_slot = request.form.get('old_slot', '')
                new_slot = request.form.get('new_slot', '')
                if old_slot and new_slot:
                    # Get the list_type of the old reservation
                    cur.execute('SELECT list_type FROM reservations WHERE event_date = ?;', (old_slot,))
                    old_res = cur.fetchone()
                    if not old_res:
                        flash('Old slot reservation not found.', 'error')
                    else:
                        list_type = old_res['list_type']
                        # Check new slot is free in the same list
                        cur.execute('SELECT COUNT(*) FROM reservations WHERE event_date = ? AND event_day = ? AND list_type = ?;', (new_slot, day, list_type))
                        if cur.fetchone()[0] > 0:
                            flash('New slot is already taken.', 'error')
                        else:
                            # Move the reservation
                            cur.execute('UPDATE reservations SET event_date = ? WHERE event_date = ? AND event_day = ? AND list_type = ?;', (new_slot, old_slot, day, list_type))
                            db.commit()
                        new_dt = parse_iso_slot(new_slot)
                        flash(f'Reservation moved to {new_dt.strftime("%H:%M")} UTC!', 'success')
                else:
                    flash('Missing slot information.', 'error')
        else:
            # Normal reservation but only if selected
            slot_iso = request.form.get('slot', '')
            player_name = request.form.get('player_name', '').strip()

            slot_dt = parse_iso_slot(slot_iso)

            # Selection gate
            if not selection_state or not selection_state.get('completed'):
                ready_txt = selection_state['ready_at'] if selection_state and selection_state.get('ready_at') else 'soon'
                flash(f'Selection not completed yet. It will unlock at {ready_txt}.', 'error')
            else:
                # Verify player is selected and get their speedup_days and list_type (from ANY list)
                cur.execute("SELECT status, waitlist_position, speedup_days, list_type FROM preregistrations WHERE event_date = ? AND event_day = ? AND player_name = ? ORDER BY datetime(created_at) ASC LIMIT 1;", (event_date_str, day, player_name))
                row = cur.fetchone()
                if not row:
                    flash('You must pre-register first. Your name is not in the selection list.', 'error')
                elif row['status'] != 'selected':
                    pos = row['waitlist_position']
                    flash(f'You are on the waitlist (position {pos}). Only the top {SELECTION_TOP_N} can book.', 'error')
                else:
                    # Get speedup_days and list_type from preregistration
                    speedup_days = row['speedup_days']
                    list_type = row['list_type']
                    
                    # Validations
                    if slot_dt is None:
                        flash('Invalid slot.', 'error')
                    elif not slot_aligned(slot_dt):
                        flash('Slot must be on the hour or half-hour.', 'error')
                    elif speedup_days < SLOT_MIN_SPEEDUP_DAYS:
                        flash(f'You need at least {SLOT_MIN_SPEEDUP_DAYS} days of speedups.', 'error')
                    else:
                        # Check availability for this list type
                        cur.execute('SELECT COUNT(*) FROM reservations WHERE event_date = ? AND event_day = ? AND list_type = ?;', (slot_iso, day, list_type))
                        if cur.fetchone()[0] > 0:
                            flash('This slot is already reserved.', 'error')
                        else:
                            # Insert reservation with list_type
                            now = datetime.now(timezone.utc)
                            cur.execute('INSERT INTO reservations (event_date, event_day, player_name, speedup_days, reserved_at, list_type, slot_index) VALUES (?, ?, ?, ?, ?, ?, ?);',
                                        (slot_iso, day, player_name, speedup_days, now.isoformat(), list_type, 0))
                            db.commit()
                            list_name = 'Main List' if list_type == 'main' else 'Secondary List'
                            flash(f'Reservation confirmed for {slot_dt.strftime("%H:%M")} UTC on {list_name}!', 'success')

    # Build slots lists for main and secondary
    slots_list_main = []
    slots_list_secondary = []
    for s in slots_between(event_start, event_end + timedelta(minutes=1)):
        key = s.isoformat()
        
        # Main list slots
        cur.execute("SELECT player_name, speedup_days FROM reservations WHERE event_date = ? AND event_day = ? AND list_type = 'main';", (key, day))
        row = cur.fetchone()
        reserved_main = row is not None
        player_main = row['player_name'] if reserved_main else None
        days_main = row['speedup_days'] if reserved_main else None
        slots_list_main.append({'slot': s, 'iso': key, 'reserved': reserved_main, 'player': player_main, 'days': days_main})
        
        # Secondary list slots (only for dual-list events)
        if is_dual_list:
            cur.execute("SELECT player_name, speedup_days FROM reservations WHERE event_date = ? AND event_day = ? AND list_type = 'secondary';", (key, day))
            row = cur.fetchone()
            reserved_secondary = row is not None
            player_secondary = row['player_name'] if reserved_secondary else None
            days_secondary = row['speedup_days'] if reserved_secondary else None
            slots_list_secondary.append({'slot': s, 'iso': key, 'reserved': reserved_secondary, 'player': player_secondary, 'days': days_secondary})

    free_slots_main = [s for s in slots_list_main if not s['reserved']]
    free_slots_secondary = [s for s in slots_list_secondary if not s['reserved']] if is_dual_list else []
    event_display = event_start.strftime('%A, %B %d, %Y')
    # Get event type based on weekday
    weekday = event_start.weekday()
    event_type = EVENT_TYPES.get(weekday, {'name': 'Event', 'emoji': '🗓️'})
    # Get current theme
    theme = get_current_theme()

    # Fetch assigned slots and conflicts
    cur.execute("SELECT player_name, speedup_days, preferred_slots, assigned_slot, list_type FROM preregistrations WHERE event_date = ? AND event_day = ?;", (event_date_str, day))
    all_preregistrations = cur.fetchall()
    
    # Get conflicts
    cur.execute("SELECT id, slot_iso, player_names, speedup_days, resolved, winner FROM slot_conflicts WHERE event_date = ? AND event_day = ? AND resolved = 0;", (event_date_str, day))
    conflicts = cur.fetchall()

    selection_state = selection_state or get_selection_state(event_date_str)

    # Calculate statistics for main and secondary lists
    stats_main = None
    stats_secondary = None
    
    if selection_state and selection_state.get('completed'):
        # Main list stats
        cur.execute("""
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(speedup_days), 0) as total,
                COALESCE(MIN(speedup_days), 0) as min,
                COALESCE(MAX(speedup_days), 0) as max,
                COALESCE(AVG(speedup_days), 0) as avg
            FROM preregistrations 
            WHERE event_day = ? AND list_type = 'main' AND assigned_slot IS NOT NULL AND assigned_slot != '';
        """, (day,))
        row_main = cur.fetchone()
        if row_main and row_main['count'] > 0:
            stats_main = {
                'count': row_main['count'],
                'total': row_main['total'],
                'min': row_main['min'],
                'max': row_main['max'],
                'avg': row_main['avg']
            }
        
        # Secondary list stats (only for dual-list events)
        if is_dual_list:
            cur.execute("""
                SELECT 
                    COUNT(*) as count,
                    COALESCE(SUM(speedup_days), 0) as total,
                    COALESCE(MIN(speedup_days), 0) as min,
                    COALESCE(MAX(speedup_days), 0) as max,
                    COALESCE(AVG(speedup_days), 0) as avg
                FROM preregistrations 
                WHERE event_day = ? AND list_type = 'secondary' AND assigned_slot IS NOT NULL AND assigned_slot != '';
            """, (day,))
            row_secondary = cur.fetchone()
            if row_secondary and row_secondary['count'] > 0:
                stats_secondary = {
                    'count': row_secondary['count'],
                    'total': row_secondary['total'],
                    'min': row_secondary['min'],
                    'max': row_secondary['max'],
                    'avg': row_secondary['avg']
                }

    return render_template(
        'index.html',
        slots_main=slots_list_main,
        slots_secondary=slots_list_secondary,
        free_slots_main=free_slots_main,
        free_slots_secondary=free_slots_secondary,
        event_date=event_display,
        min_speedup=SLOT_MIN_SPEEDUP_DAYS,
        event_type=event_type,
        registrations_open=registrations_open,
        countdown_target=countdown_target,
        theme=theme,
        selection_state=selection_state,
        all_preregistrations=all_preregistrations,
        conflicts=conflicts,
        is_dual_list=is_dual_list,
        selection_top_n=SELECTION_TOP_N,
        stats_main=stats_main,
        stats_secondary=stats_secondary
    )

# Admin route to reset reservations and set new event date
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    db = get_db()
    cur = db.cursor()
    
    # Get selected day from form or default to monday
    selected_day = request.form.get('selected_day', 'monday') if request.method == 'POST' else request.args.get('day', 'monday')
    
    if request.method == 'POST':
        action = request.form.get('action')
        password = request.form.get('password', '').strip()
        
        # Verify password for all admin actions
        if password != ADMIN_PASSWORD:
            flash('Incorrect password.', 'error')
            return redirect(url_for('admin', day=selected_day))
        
        if action == 'reset':
            # Delete all reservations for this day
            cur.execute('DELETE FROM reservations WHERE event_day = ?;', (selected_day,))
            db.commit()
            flash(f'All reservations for {selected_day} have been cleared.', 'success')
        
        elif action == 'set_date':
            new_date = request.form.get('new_date', '').strip()
            # Validate date format YYYY-MM-DD
            try:
                datetime.strptime(new_date, '%Y-%m-%d')
                set_event_date(new_date, selected_day)
                # Also clear reservations when changing date
                cur.execute('DELETE FROM reservations WHERE event_day = ?;', (selected_day,))
                db.commit()
                flash(f'Event date for {selected_day} changed to {new_date}. All reservations cleared.', 'success')
            except ValueError:
                flash('Invalid date format. Use YYYY-MM-DD.', 'error')
        
        elif action == 'delete_one':
            reservation_id = request.form.get('reservation_id', '').strip()
            if reservation_id:
                cur.execute('DELETE FROM reservations WHERE id = ?;', (reservation_id,))
                db.commit()
                flash('Reservation deleted.', 'success')
            else:
                flash('No reservation selected.', 'error')

        elif action == 'delete_prereg':
            # Delete a single pre-registration and any of their reservations
            prereg_id = request.form.get('prereg_id', '').strip()
            current_date = get_event_date(selected_day)
            if prereg_id:
                # Find player name for feedback and cleanup
                cur.execute('SELECT player_name FROM preregistrations WHERE id = ?;', (prereg_id,))
                row = cur.fetchone()
                player_name = row['player_name'] if row else None

                # Delete preregistration
                cur.execute('DELETE FROM preregistrations WHERE id = ?;', (prereg_id,))
                # Also delete any reservations for this player on the selected day
                if player_name:
                    cur.execute('DELETE FROM reservations WHERE event_day = ? AND player_name = ?;', (selected_day, player_name))
                db.commit()
                flash(f'Pré-inscription de {player_name} supprimée avec succès.', 'success')
            else:
                flash('No pre-registration selected.', 'error')
        
        elif action == 'set_event_settings':
            # Combined event date + registration open time
            event_date = request.form.get('event_date', '').strip()
            open_date = request.form.get('open_date', '').strip()
            open_time = request.form.get('open_time', '').strip()
            clear_reservations = request.form.get('clear_reservations') == '1'
            
            # Set event date for this day
            try:
                datetime.strptime(event_date, '%Y-%m-%d')
                set_event_date(event_date, selected_day)
            except ValueError:
                flash('Invalid event date format.', 'error')
                return redirect(url_for('admin', day=selected_day))
            
            # Set registration open time (or clear if empty)
            if open_date and open_time:
                try:
                    open_datetime_str = f"{open_date}T{open_time}:00"
                    datetime.fromisoformat(open_datetime_str)  # Validate
                    set_registration_open(open_datetime_str, selected_day)
                except ValueError:
                    flash('Invalid registration open date/time.', 'error')
                    return redirect(url_for('admin', day=selected_day))
            else:
                # Clear registration open (open immediately)
                clear_registration_open(selected_day)
            
            # Clear reservations if requested
            if clear_reservations:
                cur.execute('DELETE FROM reservations WHERE event_day = ?;', (selected_day,))
                db.commit()
                flash(f'Settings saved for {selected_day}. All reservations cleared.', 'success')
            else:
                flash(f'Settings saved for {selected_day}.', 'success')
        
        elif action == 'set_open_time':
            open_date = request.form.get('open_date', '').strip()
            open_time = request.form.get('open_time', '').strip()
            if open_date and open_time:
                try:
                    open_datetime_str = f"{open_date}T{open_time}:00"
                    datetime.fromisoformat(open_datetime_str)  # Validate
                    set_registration_open(open_datetime_str, selected_day)
                    flash(f'Registrations for {selected_day} will open at {open_date} {open_time} UTC.', 'success')
                except ValueError:
                    flash('Invalid date/time format.', 'error')
            else:
                flash('Please provide both date and time.', 'error')
        
        elif action == 'clear_open_time':
            clear_registration_open(selected_day)
            flash(f'Registrations for {selected_day} are now open immediately.', 'success')
        
        elif action == 'set_theme':
            new_theme = request.form.get('theme', 'kingshot').strip()
            if new_theme in ['kingshot', 'christmas', 'auto']:
                if new_theme == 'auto':
                    # Remove theme config to use auto-detection
                    db = get_db()
                    cur = db.cursor()
                    cur.execute("DELETE FROM config WHERE key = 'theme';")
                    db.commit()
                    flash('Theme set to auto-detect (Christmas in December).', 'success')
                else:
                    set_theme(new_theme)
                    flash(f'Theme changed to {new_theme}.', 'success')
            else:
                flash('Invalid theme.', 'error')
        
        elif action == 'resolve_conflict':
            # Résoudre un conflit manuellement
            import json
            conflict_id = request.form.get('conflict_id', '').strip()
            winner_name = request.form.get('winner_name', '').strip()
            
            if not conflict_id or not winner_name:
                flash('Missing conflict ID or winner name.', 'error')
            else:
                # Get conflict details
                cur.execute("SELECT event_date, event_day, slot_iso, player_names FROM slot_conflicts WHERE id = ?;", (conflict_id,))
                conflict = cur.fetchone()
                
                if not conflict:
                    flash('Conflict not found.', 'error')
                else:
                    player_names = json.loads(conflict['player_names'])
                    if winner_name not in player_names:
                        flash('Winner must be one of the conflicting players.', 'error')
                    else:
                        # Mark conflict as resolved
                        cur.execute("UPDATE slot_conflicts SET resolved = 1, winner = ? WHERE id = ?;", (winner_name, conflict_id))
                        
                        # Find the winner's preregistration and assign the slot
                        cur.execute(
                            "SELECT id FROM preregistrations WHERE event_date = ? AND event_day = ? AND player_name = ?;",
                            (conflict['event_date'], conflict['event_day'], winner_name)
                        )
                        winner_prereg = cur.fetchone()
                        
                        if winner_prereg:
                            cur.execute(
                                "UPDATE preregistrations SET assigned_slot = ? WHERE id = ?;",
                                (conflict['slot_iso'], winner_prereg['id'])
                            )
                        
                        db.commit()
                        flash(f'Conflict resolved! {winner_name} gets the slot.', 'success')
        
        return redirect(url_for('admin', day=selected_day))
    
    # GET: show admin page for selected day
    current_date = get_event_date(selected_day)
    # Only count and show reservations for the current event date and day
    cur.execute("SELECT COUNT(*) FROM reservations WHERE event_date LIKE ? AND event_day = ?;", (current_date + '%', selected_day))
    reservation_count = cur.fetchone()[0]
    # Get reservations for the current event date and day (include list_type)
    cur.execute("SELECT id, event_date, player_name, speedup_days, list_type FROM reservations WHERE event_date LIKE ? AND event_day = ? ORDER BY list_type, event_date;", (current_date + '%', selected_day))
    reservations = cur.fetchall()
    # Get preregistrations for this day/date
    cur.execute("SELECT id, player_name, speedup_days, list_type, created_at FROM preregistrations WHERE event_date = ? AND event_day = ? ORDER BY list_type, datetime(created_at) ASC;", (current_date, selected_day))
    preregistrations = cur.fetchall()
    # Get registration open time for this day
    registration_open = get_registration_open(selected_day)
    # Get current theme
    theme = get_current_theme()
    # Check if theme is in auto mode
    cur.execute("SELECT value FROM config WHERE key = 'theme';")
    theme_config = cur.fetchone()
    theme_mode = 'auto' if theme_config is None else theme_config['value']
    
    # Get unresolved conflicts for this day
    import json
    cur.execute("SELECT id, slot_iso, player_names, speedup_days FROM slot_conflicts WHERE event_day = ? AND resolved = 0;", (selected_day,))
    conflicts_raw = cur.fetchall()
    conflicts = []
    for c in conflicts_raw:
        conflicts.append({
            'id': c['id'],
            'slot_iso': c['slot_iso'],
            'player_names': json.loads(c['player_names']),
            'speedup_days': c['speedup_days']
        })
    
    return render_template('admin.html', current_date=current_date, reservation_count=reservation_count, reservations=reservations, registration_open=registration_open, theme=theme, theme_mode=theme_mode, selected_day=selected_day, conflicts=conflicts, preregistrations=preregistrations)

# Keep /slots as alias
@app.route('/slots')
def slots():
    return redirect(url_for('index'))

# /reserve now redirects to index
@app.route('/reserve')
def reserve():
    return redirect(url_for('index'))

# Rydak Wheel - "Quel type de Rydak es-tu ?"
@app.route('/rydak-wheel')
def rydak_wheel():
    # List of all Rydak images with fun names
    rydaks = [
        {'file': 'Rydak1.png', 'name': 'Don Rydak 🎩'},
        {'file': 'Rydak2.png', 'name': 'Rydaddy 😎'},
        {'file': 'Rydak3.png', 'name': 'Rural Rydak 🌾'},
        {'file': 'Rydak4.png', 'name': 'Urban Rydak 🏙️'},
        {'file': 'Rydak5.png', 'name': 'Hillbilly Rydak 🤠'},
        {'file': 'Rydak6.png', 'name': 'Rich Rydak 💰'},
        {'file': 'Rydak7.png', 'name': 'Homeless Rydak 🛒'},
        {'file': 'Rydak8.png', 'name': 'Crazy Rydak 🤪'},
        {'file': 'Rydak9.png', 'name': 'Professor Rydak 🎓'},
        {'file': 'Rydak10.png', 'name': 'Trailer Park Rydak 🏕️'},
        {'file': 'Rydak111.png', 'name': 'Hunter Rydak 🦌'},
        {'file': 'Rydak12.png', 'name': 'Rydak the Clown 🤡'},
        {'file': 'Rydak13.png', 'name': 'Jester Rydak 🃏'},
        {'file': 'Rydak14.png', 'name': 'Rydaddy 👑'},
    ]
    theme = get_current_theme()
    return render_template('rydak-wheel.html', rydaks=rydaks, theme=theme)

@app.route('/kvk-training', methods=['GET', 'POST'])
def kvk_training():
    """KVK Training team balancer - auto-balance teams by power"""
    db = get_db()
    cur = db.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_player':
            name = request.form.get('player_name', '').strip()
            try:
                power = float(request.form.get('power', 0))
            except ValueError:
                power = 0
            alliance = request.form.get('alliance', '').strip().upper()[:3]
            
            # Get Infantry TG
            try:
                infantry_tg = int(request.form.get('infantry_tg', 0))
            except ValueError:
                infantry_tg = 0
            
            # Get Archery TG
            try:
                archery_tg = int(request.form.get('archery_tg', 0))
            except ValueError:
                archery_tg = 0
            
            # Get Cavalry TG
            try:
                cavalry_tg = int(request.form.get('cavalry_tg', 0))
            except ValueError:
                cavalry_tg = 0
            
            if not name or power <= 0 or len(alliance) != 3:
                flash('Please fill all fields correctly (Alliance must be 3 letters).', 'error')
            else:
                # Add player and auto-balance
                cur.execute(
                    'INSERT INTO training_players (name, power, alliance, infantry_tg, archery_tg, cavalry_tg, team) VALUES (?, ?, ?, ?, ?, ?, ?);',
                    (name, power, alliance, infantry_tg, archery_tg, cavalry_tg, 0)  # Team 0 = unassigned
                )
                db.commit()
                
                # Auto-balance teams
                balance_teams(db)
                flash(f'{name} added and teams rebalanced!', 'success')
        
        elif action == 'switch_team':
            player_id = request.form.get('player_id', '').strip()
            if player_id:
                # Get current team
                cur.execute('SELECT team FROM training_players WHERE id = ?;', (player_id,))
                row = cur.fetchone()
                if row:
                    current_team = row['team']
                    new_team = 2 if current_team == 1 else 1
                    cur.execute('UPDATE training_players SET team = ? WHERE id = ?;', (new_team, player_id))
                    db.commit()
                    flash('Player switched teams!', 'success')
        
        elif action == 'rebalance':
            balance_teams(db)
            flash('Teams rebalanced!', 'success')
        
        elif action == 'remove_player':
            player_id = request.form.get('player_id', '').strip()
            if player_id:
                cur.execute('DELETE FROM training_players WHERE id = ?;', (player_id,))
                db.commit()
                balance_teams(db)
                flash('Player removed and teams rebalanced!', 'success')
        
        elif action == 'reset_all':
            cur.execute('DELETE FROM training_players;')
            db.commit()
            flash('All teams reset!', 'success')
        
        return redirect(url_for('kvk_training'))
    
    # GET: Fetch teams
    cur.execute('SELECT id, name, power, alliance, infantry_tg, archery_tg, cavalry_tg, team FROM training_players ORDER BY power DESC;')
    players = cur.fetchall()
    
    team1 = [{'id': p['id'], 'name': p['name'], 'power': p['power'], 'alliance': p['alliance'], 'infantry_tg': p['infantry_tg'], 'archery_tg': p['archery_tg'], 'cavalry_tg': p['cavalry_tg']} 
             for p in players if p['team'] == 1]
    team2 = [{'id': p['id'], 'name': p['name'], 'power': p['power'], 'alliance': p['alliance'], 'infantry_tg': p['infantry_tg'], 'archery_tg': p['archery_tg'], 'cavalry_tg': p['cavalry_tg']} 
             for p in players if p['team'] == 2]
    
    team1_total = round(sum(p['power'] for p in team1), 1)
    team2_total = round(sum(p['power'] for p in team2), 1)
    power_diff = round(abs(team1_total - team2_total), 1)
    player_diff = abs(len(team1) - len(team2))
    
    theme = get_current_theme()
    return render_template('kvk_training.html', 
                         team1=team1, team2=team2,
                         team1_total=team1_total, team2_total=team2_total,
                         power_diff=power_diff, player_diff=player_diff,
                         theme=theme)

def balance_teams(db):
    """Auto-balance teams to minimize power difference while keeping player counts equal"""
    cur = db.cursor()
    
    # Get all players sorted by power (descending)
    cur.execute('SELECT id, power FROM training_players ORDER BY power DESC;')
    players = cur.fetchall()
    
    if not players:
        return
    
    # Reset all teams
    cur.execute('UPDATE training_players SET team = 0;')
    
    team1_power = 0
    team2_power = 0
    team1_count = 0
    team2_count = 0
    
    # Greedy algorithm: assign each player to the team with lower total power
    # But also try to keep player counts balanced
    for player in players:
        player_id = player['id']
        power = player['power']
        
        # Decide which team gets this player
        if team1_count < team2_count:
            # Team 1 has fewer players, assign there
            assign_to = 1
            team1_power += power
            team1_count += 1
        elif team2_count < team1_count:
            # Team 2 has fewer players, assign there
            assign_to = 2
            team2_power += power
            team2_count += 1
        else:
            # Equal player counts, assign to team with lower power
            if team1_power <= team2_power:
                assign_to = 1
                team1_power += power
                team1_count += 1
            else:
                assign_to = 2
                team2_power += power
                team2_count += 1
        
        cur.execute('UPDATE training_players SET team = ? WHERE id = ?;', (assign_to, player_id))
    
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db:
        db.close()

if __name__ == '__main__':
    app.run(debug=True)
