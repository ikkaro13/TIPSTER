import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "tipster.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS portfolio (key TEXT PRIMARY KEY, value REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bets (
        id TEXT PRIMARY KEY,
        match_id TEXT,
        pick TEXT,
        odds REAL,
        stake REAL,
        status TEXT,
        profit REAL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        evidence_snapshot TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS bankroll_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bet_id TEXT,
        action TEXT,
        amount REAL,
        balance_after REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS delfos_picks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        league TEXT,
        match TEXT,
        market TEXT,
        confidence REAL,
        edge REAL,
        odds REAL,
        status TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        evidence_snapshot TEXT
    )''')
    
    # Initialize bankroll if empty
    c.execute("SELECT * FROM portfolio WHERE key = 'bankroll'")
    if not c.fetchone():
        c.execute("INSERT INTO portfolio (key, value) VALUES ('bankroll', 1000.0)")
        c.execute("INSERT INTO portfolio (key, value) VALUES ('initial_bankroll', 1000.0)")
    
    conn.commit()
    conn.close()

init_db()
