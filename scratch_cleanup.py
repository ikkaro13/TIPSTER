import json
with open('backend/team_stats_db.json', 'r', encoding='utf-8') as f:
    stats_db = json.load(f)

# Delete teams with league 121 (because they are Danish Cup teams downloaded by mistake)
to_delete = [tid for tid, data in stats_db.items() if data.get("league") == 121]
for tid in to_delete:
    del stats_db[tid]

print(f"Borrados {len(to_delete)} equipos fantasmas de Veikkausliiga.")

with open('backend/team_stats_db.json', 'w', encoding='utf-8') as f:
    json.dump(stats_db, f, indent=4)
