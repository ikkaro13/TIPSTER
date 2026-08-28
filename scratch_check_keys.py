import json
try:
    with open('backend/team_stats_db.json', 'r', encoding='utf-8') as f:
        db = json.load(f)
    print(list(db.keys())[:15])
except Exception as e:
    print(e)
