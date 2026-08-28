import sqlite3
import pandas as pd

conn = sqlite3.connect('backend/tipster.db')
cursor = conn.cursor()

# Get table schema
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tablas:", tables)

try:
    df = pd.read_sql_query("SELECT * FROM elo_history LIMIT 1", conn)
    print("Columnas en elo_history:", df.columns.tolist())
    
    # Unfortunately elo_history only has team_name, match_id, date, elo_before, elo_after
    # It doesn't have league_id directly, but we can query team_stats_db.json or just report the known seeded leagues.
    
    cursor.execute("SELECT COUNT(*) FROM elo_history;")
    print("Total ELO entries:", cursor.fetchone()[0])
except Exception as e:
    print(e)
