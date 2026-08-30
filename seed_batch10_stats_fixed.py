import os
import time
import json
import sqlite3
import sys
sys.path.append('backend')
from api_football_engine import make_api_request

from datetime import datetime

from seed_ligas import ALL_TRACKED_LEAGUES
LEAGUES = ALL_TRACKED_LEAGUES
stats_file = 'backend/team_stats_db.json'
try:
    with open(stats_file, 'r', encoding='utf-8') as f:
        stats_db = json.load(f)
except:
    stats_db = {}

# Estamos a inicios de temporada (Agosto 2026), por lo que 2026 tiene muy pocos partidos.
# Usamos 2025 para obtener la "Bóveda" de estadísticas con muestra completa (38+ partidos)
current_year = 2025

for name, lid in LEAGUES.items():
    print(f"Inyectando Estadísticas Híbridas para {name} (Temporada {current_year})...")
    team_res = make_api_request(f"/teams?league={lid}&season={current_year}")
    time.sleep(1.5)
    if not team_res or "response" not in team_res:
        continue
        
    teams = team_res["response"]
    for t in teams:
        team_id = str(t["team"]["id"])
        team_name = t["team"]["name"]
        
        safe_name = team_name.encode('ascii', 'replace').decode('ascii')
        print(f"  -> Descargando/Actualizando {safe_name}...")
        stat_data = make_api_request(f"/teams/statistics?league={lid}&season={current_year}&team={team_id}")
        if stat_data and "response" in stat_data and stat_data["response"]:
            resp = stat_data["response"]
            clean_sheet = resp.get("clean_sheet", {}).get("total", 0)
            failed_to_score = resp.get("failed_to_score", {}).get("total", 0)
            
            cards = resp.get("cards", {})
            yellow_cards = 0
            red_cards = 0
            if "yellow" in cards:
                for k, v in cards["yellow"].items():
                    if v.get("total") is not None:
                        yellow_cards += int(v["total"])
            if "red" in cards:
                for k, v in cards["red"].items():
                    if v.get("total") is not None:
                        red_cards += int(v["total"])
            
            stats_db[team_id] = {
                "name": team_name,
                "league": lid,
                "form": resp.get("form", ""),
                "clean_sheets": clean_sheet,
                "failed_to_score": failed_to_score,
                "over_25": 0,
                "under_25": 0,
                "yellow_cards": yellow_cards,
                "red_cards": red_cards
            }
            
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats_db, f, indent=4)
                
        time.sleep(1.5) # <- PAUSA CORRECTA

print("¡INYECCIÓN ESTADÍSTICAS COMPLETADA!")
