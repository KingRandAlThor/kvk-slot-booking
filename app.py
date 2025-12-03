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
    return db

app = Flask(__name__)
app.secret_key = 'dev-secret'

SLOT_MIN_SPEEDUP_DAYS = 20
DEFAULT_EVENT_DATE = '2025-12-02'  # YYYY-MM-DD format
ADMIN_PASSWORD = 'kvk2025'  # Change this to your desired password

# Event types by weekday (0=Monday, 1=Tuesday, etc.)
EVENT_TYPES = {
    0: {'name': 'Construction', 'emoji': '🏗️'},
    1: {'name': 'Research', 'emoji': '🔬'},
    3: {'name': 'Troop Training', 'emoji': '⚔️'},
}

def get_event_date():
    """Get event date from config table, or use default."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT value FROM config WHERE key = 'event_date';")
    row = cur.fetchone()
    if row:
        return row['value']
    return DEFAULT_EVENT_DATE

def set_event_date(date_str: str):
    """Set event date in config table."""
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('event_date', ?);",(date_str,))
    db.commit()

def get_registration_open():
    """Get registration open datetime from config table."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT value FROM config WHERE key = 'registration_open';")
    row = cur.fetchone()
    if row:
        return row['value']
    return None  # None means always open

def set_registration_open(datetime_str: str):
    """Set registration open datetime in config table."""
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('registration_open', ?);",(datetime_str,))
    db.commit()

def clear_registration_open():
    """Clear registration open datetime (make registrations always open)."""
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM config WHERE key = 'registration_open';")
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
def index():
    # Get event date from config
    event_date_str = get_event_date()
    try:
        event_date_parts = [int(p) for p in event_date_str.split('-')]
        event_start = datetime(event_date_parts[0], event_date_parts[1], event_date_parts[2], 0, 0, 0, tzinfo=timezone.utc)
    except:
        event_start = datetime(2025, 12, 2, 0, 0, 0, tzinfo=timezone.utc)
    event_end = event_start.replace(hour=23, minute=59)

    # Check if registrations are open
    registration_open_str = get_registration_open()
    registrations_open = True
    countdown_target = None
    
    if registration_open_str:
        try:
            open_dt = datetime.fromisoformat(registration_open_str).replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            if now < open_dt:
                registrations_open = False
                countdown_target = registration_open_str
        except:
            pass

    db = get_db()
    cur = db.cursor()

    # Handle reservation POST
    if request.method == 'POST' and registrations_open:
        action = request.form.get('action', 'reserve')
        
        # Move reservation action
        if action == 'move':
            password = request.form.get('password', '').strip()
            if password != ADMIN_PASSWORD:
                flash('Incorrect admin password.', 'error')
            else:
                old_slot = request.form.get('old_slot', '')
                new_slot = request.form.get('new_slot', '')
                if old_slot and new_slot:
                    # Check new slot is free
                    cur.execute('SELECT COUNT(*) FROM reservations WHERE slot_start = ?;', (new_slot,))
                    if cur.fetchone()[0] > 0:
                        flash('New slot is already taken.', 'error')
                    else:
                        # Move the reservation
                        cur.execute('UPDATE reservations SET slot_start = ? WHERE slot_start = ?;', (new_slot, old_slot))
                        db.commit()
                        new_dt = parse_iso_slot(new_slot)
                        flash(f'Reservation moved to {new_dt.strftime("%H:%M")} UTC!', 'success')
                else:
                    flash('Missing slot information.', 'error')
        else:
            # Normal reservation
            slot_iso = request.form.get('slot', '')
            player_name = request.form.get('player_name', '').strip()
            try:
                speedup_days = int(request.form.get('speedup_days', '0'))
            except ValueError:
                speedup_days = 0

            slot_dt = parse_iso_slot(slot_iso)

            # Validations
            if slot_dt is None:
                flash('Invalid slot.', 'error')
            elif not slot_aligned(slot_dt):
                flash('Slot must be on the hour or half-hour.', 'error')
            elif speedup_days < SLOT_MIN_SPEEDUP_DAYS:
                flash(f'You need at least {SLOT_MIN_SPEEDUP_DAYS} days of speedups.', 'error')
            else:
                # Check availability
                cur.execute('SELECT COUNT(*) FROM reservations WHERE slot_start = ?;', (slot_iso,))
                if cur.fetchone()[0] > 0:
                    flash('This slot is already reserved.', 'error')
                else:
                    # Insert reservation
                    now = datetime.now(timezone.utc)
                    cur.execute('INSERT INTO reservations (slot_start, player_name, speedup_days, created_at) VALUES (?, ?, ?, ?);',
                                (slot_iso, player_name, speedup_days, now.isoformat()))
                    db.commit()
                    flash(f'Reservation confirmed for {slot_dt.strftime("%H:%M")} UTC!', 'success')

    # Build slots list
    slots_list = []
    for s in slots_between(event_start, event_end + timedelta(minutes=1)):
        key = s.isoformat()
        cur.execute('SELECT player_name, speedup_days FROM reservations WHERE slot_start = ?;', (key,))
        row = cur.fetchone()
        reserved = row is not None
        player = row['player_name'] if reserved else None
        days = row['speedup_days'] if reserved else None
        slots_list.append({'slot': s, 'iso': key, 'reserved': reserved, 'player': player, 'days': days})

    free_slots = [s for s in slots_list if not s['reserved']]
    event_display = event_start.strftime('%A, %B %d, %Y')
    # Get event type based on weekday
    weekday = event_start.weekday()
    event_type = EVENT_TYPES.get(weekday, {'name': 'Event', 'emoji': '🗓️'})
    # Get current theme
    theme = get_current_theme()
    return render_template('index.html', slots=slots_list, free_slots=free_slots, event_date=event_display, min_speedup=SLOT_MIN_SPEEDUP_DAYS, event_type=event_type, registrations_open=registrations_open, countdown_target=countdown_target, theme=theme)

# Admin route to reset reservations and set new event date
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    db = get_db()
    cur = db.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        password = request.form.get('password', '').strip()
        
        # Verify password for all admin actions
        if password != ADMIN_PASSWORD:
            flash('Incorrect password.', 'error')
            return redirect(url_for('admin'))
        
        if action == 'reset':
            # Delete all reservations
            cur.execute('DELETE FROM reservations;')
            db.commit()
            flash('All reservations have been cleared.', 'success')
        
        elif action == 'set_date':
            new_date = request.form.get('new_date', '').strip()
            # Validate date format YYYY-MM-DD
            try:
                datetime.strptime(new_date, '%Y-%m-%d')
                set_event_date(new_date)
                # Also clear reservations when changing date
                cur.execute('DELETE FROM reservations;')
                db.commit()
                flash(f'Event date changed to {new_date}. All reservations cleared.', 'success')
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
        
        elif action == 'set_event_settings':
            # Combined event date + registration open time
            event_date = request.form.get('event_date', '').strip()
            open_date = request.form.get('open_date', '').strip()
            open_time = request.form.get('open_time', '').strip()
            clear_reservations = request.form.get('clear_reservations') == '1'
            
            # Set event date
            try:
                datetime.strptime(event_date, '%Y-%m-%d')
                set_event_date(event_date)
            except ValueError:
                flash('Invalid event date format.', 'error')
                return redirect(url_for('admin'))
            
            # Set registration open time (or clear if empty)
            if open_date and open_time:
                try:
                    open_datetime_str = f"{open_date}T{open_time}:00"
                    datetime.fromisoformat(open_datetime_str)  # Validate
                    set_registration_open(open_datetime_str)
                except ValueError:
                    flash('Invalid registration open date/time.', 'error')
                    return redirect(url_for('admin'))
            else:
                # Clear registration open (open immediately)
                clear_registration_open()
            
            # Clear reservations if requested
            if clear_reservations:
                cur.execute('DELETE FROM reservations;')
                db.commit()
                flash('Settings saved. All reservations cleared.', 'success')
            else:
                flash('Settings saved.', 'success')
        
        elif action == 'set_open_time':
            open_date = request.form.get('open_date', '').strip()
            open_time = request.form.get('open_time', '').strip()
            if open_date and open_time:
                try:
                    open_datetime_str = f"{open_date}T{open_time}:00"
                    datetime.fromisoformat(open_datetime_str)  # Validate
                    set_registration_open(open_datetime_str)
                    flash(f'Registrations will open at {open_date} {open_time} UTC.', 'success')
                except ValueError:
                    flash('Invalid date/time format.', 'error')
            else:
                flash('Please provide both date and time.', 'error')
        
        elif action == 'clear_open_time':
            clear_registration_open()
            flash('Registrations are now open immediately.', 'success')
        
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
        
        return redirect(url_for('admin'))
    
    # GET: show admin page
    current_date = get_event_date()
    # Only count and show reservations for the current event date
    cur.execute("SELECT COUNT(*) FROM reservations WHERE slot_start LIKE ?;", (current_date + '%',))
    reservation_count = cur.fetchone()[0]
    # Get reservations for the current event date only
    cur.execute("SELECT id, slot_start, player_name, speedup_days FROM reservations WHERE slot_start LIKE ? ORDER BY slot_start;", (current_date + '%',))
    reservations = cur.fetchall()
    # Get registration open time
    registration_open = get_registration_open()
    # Get current theme
    theme = get_current_theme()
    # Check if theme is in auto mode
    cur.execute("SELECT value FROM config WHERE key = 'theme';")
    theme_config = cur.fetchone()
    theme_mode = 'auto' if theme_config is None else theme_config['value']
    return render_template('admin.html', current_date=current_date, reservation_count=reservation_count, reservations=reservations, registration_open=registration_open, theme=theme, theme_mode=theme_mode)

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

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db:
        db.close()

if __name__ == '__main__':
    app.run(debug=True)
