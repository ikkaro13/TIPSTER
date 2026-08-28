import sqlite3
conn = sqlite3.connect('backend/tipster.db')
cursor = conn.cursor()

leagues = {
    'A-League': 188,
    'Veikkausliiga': 121,
    'Eerste Divisie': 89
}

total_tokens = 0
for name, lid in leagues.items():
    cursor.execute('SELECT COUNT(DISTINCT home_team) FROM historical_matches WHERE league_id=?', (lid,))
    count = cursor.fetchone()[0]
    print(f"{name}: {count} equipos")
    total_tokens += count

print(f"\nTotal exacto: {total_tokens} tokens")
