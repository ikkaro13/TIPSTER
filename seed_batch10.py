import os
import time
import json
import sqlite3
import sys
sys.path.append('backend')
from api_football_engine import make_api_request

LEAGUES = {
    'A-League': 188,
    'Veikkausliiga': 121,
    'Eerste Divisie': 89
}
SEASONS = [2023, 2024]
conn = sqlite3.connect('backend/tipster.db')
cursor = conn.cursor()

def fetch_and_save_elo():
    all_fixtures = []
    for name, lid in LEAGUES.items():
        cursor.execute("SELECT COUNT(*) FROM historical_matches WHERE league_id=?", (lid,))
        c = cursor.fetchone()[0]
        if c < 50:
            print(f"Descargando fixtures (ELO) para {name}...")
            for s in SEASONS:
                data = make_api_request(f"/fixtures?league={lid}&season={s}&status=FT")
                if data and "response" in data:
                    all_fixtures.extend(data["response"])
                time.sleep(1.5)
                
    if all_fixtures:
        print(f"Guardando {len(all_fixtures)} partidos en tipster.db...")
        from elo_updater import process_match_for_elo
        for match in sorted(all_fixtures, key=lambda x: x["fixture"]["timestamp"]):
            home_team = match["teams"]["home"]["name"]
            away_team = match["teams"]["away"]["name"]
            home_goals = match["goals"]["home"]
            away_goals = match["goals"]["away"]
            league_id = match["league"]["id"]
            if home_goals is None or away_goals is None: continue
            
            home_elo_before, away_elo_before, new_home_elo, new_away_elo = process_match_for_elo(home_team, away_team, home_goals, away_goals)
            
            cursor.execute('''
                INSERT OR REPLACE INTO historical_matches 
                (id, league_id, home_team, away_team, home_elo, away_elo, elo_diff, home_goals, away_goals, total_goals, btts, outcome, home_momentum, away_momentum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(match["fixture"]["id"]),
                league_id,
                home_team,
                away_team,
                home_elo_before,
                away_elo_before,
                home_elo_before - away_elo_before,
                home_goals,
                away_goals,
                home_goals + away_goals,
                1 if (home_goals > 0 and away_goals > 0) else 0,
                1 if home_goals > away_goals else (2 if away_goals > home_goals else 0),
                0, 0
            ))
        conn.commit()

fetch_and_save_elo()

stats_file = 'backend/team_stats_db.json'
try:
    with open(stats_file, 'r', encoding='utf-8') as f:
        stats_db = json.load(f)
except:
    stats_db = {}

for name, lid in LEAGUES.items():
    print(f"Inyectando Estadísticas Híbridas para {name}...")
    team_res = make_api_request(f"/teams?league={lid}&season=2024")
    time.sleep(1.5)
    if not team_res or "response" not in team_res:
        continue
        
    teams = team_res["response"]
    for t in teams:
        team_id = str(t["team"]["id"])
        team_name = t["team"]["name"]
        
        if team_id in stats_db:
            print(f"  {team_name} ya existe. Saltando...")
            continue
            
        print(f"  -> Descargando {team_name}...")
        stat_data = make_api_request(f"/teams/statistics?league={lid}&season=2024&team={team_id}")
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
                
        time.sleep(1.5)

print("¡INYECCIÓN COMPLETADA!")
