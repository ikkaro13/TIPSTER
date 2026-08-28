import json
try:
    with open('backend/team_stats_db.json', 'r', encoding='utf-8') as f:
        db = json.load(f)
    keys = list(db.keys())
    print("Muestra de equipos en team_stats_db:")
    
    test_teams = ["Inter Miami", "Leeds", "Boca Juniors", "Al Nassr", "Malaga", "Cruz Azul", "Levante"]
    for t in test_teams:
        found = any(t.lower() in k.lower() for k in keys)
        print(f"{t}: {'SI' if found else 'NO'}")
except Exception as e:
    print(e)
