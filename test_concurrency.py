import threading
import sys
sys.path.append('backend')
from portfolio_manager import get_db_connection, place_bet, get_portfolio, reset_bankroll

# Ensure DB has tables
conn = get_db_connection()
conn.execute('''
    CREATE TABLE IF NOT EXISTS bets (
        id TEXT PRIMARY KEY,
        match_id TEXT,
        pick TEXT,
        odds REAL,
        stake REAL,
        status TEXT,
        profit REAL,
        evidence_snapshot TEXT,
        created_at TEXT,
        bet_type TEXT DEFAULT 'PRE'
    )
''')
conn.execute('''
    CREATE TABLE IF NOT EXISTS portfolio (
        key TEXT PRIMARY KEY,
        value REAL
    )
''')
conn.execute('''
    CREATE TABLE IF NOT EXISTS bankroll_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bet_id TEXT,
        action TEXT,
        delta REAL,
        bankroll_before REAL,
        bankroll_after REAL,
        created_at TEXT DEFAULT (datetime('now'))
    );
''')
conn.commit()
conn.close()

# Reset bankroll to 1000
reset_bankroll(1000)

success_count = 0
error_count = 0
lock = threading.Lock()

def worker():
    global success_count, error_count
    # Place bet of 100
    res = place_bet('match_test', 'home', 2.0, 100, None, 'PRE')
    with lock:
        if res.get('status') == 'success':
            success_count += 1
        else:
            error_count += 1

threads = []
for _ in range(20):
    t = threading.Thread(target=worker)
    threads.append(t)
    t.start()

for t in threads:
    t.join()

portfolio = get_portfolio()
bankroll = portfolio['bankroll']

print(f"Success: {success_count}, Errors: {error_count}")
print(f"Final Bankroll: {bankroll}")
assert bankroll >= 0, "Bankroll is negative!"
assert success_count <= 10, "More than 10 bets were accepted for a 1000 bankroll!"
assert bankroll == 1000 - (success_count * 100), "Bankroll mismatch!"
