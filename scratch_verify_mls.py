import json
with open('backend/team_stats_db.json', 'r', encoding='utf-8') as f:
    stats_db = json.load(f)
mls = sum(1 for tid, data in stats_db.items() if data.get("league") == 253)
col = sum(1 for tid, data in stats_db.items() if data.get("league") == 239)
print(f"MLS: {mls}, Colombia: {col}")
