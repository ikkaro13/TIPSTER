import json
try:
    with open('backend/team_stats_db.json', 'r', encoding='utf-8') as f:
        stats_db = json.load(f)
    print("Total equipos ahora:", len(stats_db.keys()))
    
    veik = sum(1 for v in stats_db.values() if v.get('league') == 121)
    eerste = sum(1 for v in stats_db.values() if v.get('league') == 89)
    aleague = sum(1 for v in stats_db.values() if v.get('league') == 188)
    
    print(f"A-League: {aleague}")
    print(f"Veikkausliiga: {veik}")
    print(f"Eerste Divisie: {eerste}")
except Exception as e:
    print(e)
