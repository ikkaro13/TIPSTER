import sqlite3
import pandas as pd

conn = sqlite3.connect('backend/tipster.db')
df = pd.read_sql_query("SELECT league_id, COUNT(*) as count FROM historical_matches GROUP BY league_id", conn)
print(df)
