from app import app
from datetime import datetime, timedelta, timezone
import sqlite3, os

def run_test():
    with app.test_client() as c:
        now = datetime.now(timezone.utc)
        # compute next aligned slot
        if now.minute < 30:
            slot = now.replace(minute=30, second=0, microsecond=0)
        else:
            slot = (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
        slot_iso = slot.isoformat()
        data = {'slot': slot_iso, 'player_name': 'TestPlayer', 'speedup_days': '25'}
        resp = c.post('/reserve', data=data, follow_redirects=True)
        print('POST /reserve status:', resp.status_code)

        DB = os.path.join(os.path.dirname(__file__), 'kvk.db')
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM reservations WHERE slot_start = ?;', (slot_iso,))
        print('reservations for slot:', cur.fetchone()[0])
        conn.close()

if __name__ == '__main__':
    run_test()
