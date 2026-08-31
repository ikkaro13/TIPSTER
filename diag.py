import sqlite3
import json

conn = sqlite3.connect('backend/tipster.db')
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM bets')
total = c.fetchone()[0]

c.execute('SELECT status, COUNT(*) FROM bets GROUP BY status')
status_counts = dict(c.fetchall())

c.execute('SELECT COUNT(*) FROM bets WHERE evidence_snapshot IS NOT NULL AND evidence_snapshot != ""')
has_snap = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM bets WHERE evidence_snapshot IS NULL OR evidence_snapshot = ""')
no_snap = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM bets WHERE match_id IN ("-1", "mock12345")')
mock_matches = c.fetchone()[0]

# Check delfos picks sync
c.execute('''
    SELECT COUNT(*) FROM bets b
    JOIN delfos_picks d ON b.match_id = d.fixture_id AND b.pick = d.pick
''')
try:
    delfos_sync = c.fetchone()[0]
except:
    delfos_sync = 0

print("DIAGNOSTICO:")
print(f"Total: {total}")
print(f"Status: {status_counts}")
print(f"Con snapshot: {has_snap}")
print(f"Sin snapshot: {no_snap}")
print(f"Mock matches: {mock_matches}")
print(f"En delfos_picks: {delfos_sync}")
