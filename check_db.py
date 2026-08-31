import sqlite3
import sys
try:
    conn = sqlite3.connect('tipster.db')
    c = conn.cursor()
    c.execute("SELECT count(*) FROM bets")
    print(f"BETS IN ROOT DB: {c.fetchone()[0]}")
    conn.close()
except Exception as e:
    print(e)
