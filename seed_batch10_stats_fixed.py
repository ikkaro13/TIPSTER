import os
import time
import json
import sqlite3
import sys
sys.path.append('backend')
from api_football_engine import make_api_request

from datetime import datetime

LEAGUES = {
    'Liga MX': 262,
    'Premier League': 39,
    'La Liga': 140,
    'Serie A': 135,
    'Bundesliga': 78,
    'Ligue 1': 61,
    'Eredivisie': 88
}

stats_file = 'backend/team_stats_db.json'
try:
    with open(stats_file, 'r', encoding='utf-8') as f:
        stats_db = json.load(f)
except:
    stats_db = {}

current_year = datetime.now().year

for name, lid in LEAGUES.items():
    print(f"Inyectando Estadísticas Híbridas para {name} (Temporada {current_year})...")
    team_res = make_api_request(f"/teams?league={lid}&season={current_year}")
    time.sleep(7)
    if not team_res or "response" not in team_res:
        continue
        
    teams = team_res["response"]
    for t in teams:
        team_id = str(t["team"]["id"])
        team_name = t["team"]["name"]
        
        print(f"  -> Descargando/Actualizando {team_name}...")
        stat_data = make_api_request(f"/teams/statistics?league={lid}&season={current_year}&team={team_id}")
        if stat_data and "response" in stat_data and stat_data["response"]:
            resp = stat_data["response"]
            clean_sheet = resp.get("clean_sheet", {}).get("total", 0)
            failed_to_score = resp.get("failed_to_score", {}).get("total", 0)
            
            stats_db[team_id] = {
                "name": team_name,
                "league": lid,
                "form": resp.get("form", ""),
                "clean_sheets": clean_sheet,
                "failed_to_score": failed_to_score,
                "over_25": 0,
                "under_25": 0
            }
            
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats_db, f, indent=4)
                
        time.sleep(7) # <- PAUSA CORRECTA

print("¡INYECCIÓN ESTADÍSTICAS COMPLETADA!")
