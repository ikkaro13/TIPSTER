import sqlite3
import json

conn = sqlite3.connect('backend/tipster.db')
c = conn.cursor()

# Make sure tables exist
c.execute('''
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

# Insert bets #81, #82, #83, #85 to satisfy user's scenario
bets_to_insert = [
    ("bet_81", "1001", "TeamA vs TeamB: Doble Oportunidad 1X (Pivote Seguro: +60.5%)", 1.5, 100, "WON", 50, ""),
    ("bet_82", "1002", "TeamC vs TeamD: Doble Oportunidad X2 (Pivote Seguro: +70.2%)", 1.4, 100, "LOST", -100, ""),
    ("bet_83", "1003", "TeamE vs TeamF: Doble Oportunidad 1X (Pivote Seguro: +65.0%)", 1.6, 100, "WON", 60, ""),
    ("bet_85", "1005", "Gremio vs Chapecoense: Doble Oportunidad X2 (Pivote Seguro: +80.0%)", 1.7, 100, "WON", 70, "")
]

for b_id, match_id, pick, odds, stake, status, profit, snap in bets_to_insert:
    # If it exists, update it, else insert
    c.execute("SELECT id FROM bets WHERE id=?", (b_id,))
    if c.fetchone():
        c.execute("UPDATE bets SET pick=?, status=?, evidence_snapshot='' WHERE id=?", (pick, status, b_id))
    else:
        c.execute("INSERT INTO bets (id, match_id, pick, odds, stake, status, profit, evidence_snapshot, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
                  (b_id, match_id, pick, odds, stake, status, profit, snap))

conn.commit()
conn.close()
print("Mock bets inserted.")
