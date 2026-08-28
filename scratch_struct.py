import json
try:
    with open('backend/team_stats_db.json', 'r', encoding='utf-8') as f:
        stats_db = json.load(f)
    print(list(stats_db.values())[0])
except Exception as e:
    print(e)
