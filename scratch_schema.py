import sqlite3
conn = sqlite3.connect('backend/tipster.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(historical_matches);")
columns = cursor.fetchall()
for c in columns:
    print(c)
