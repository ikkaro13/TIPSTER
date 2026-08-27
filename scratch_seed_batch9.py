import requests
import json
import os
import time

API_KEY = "7419e977170de5db2ea68791e952179f"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {'x-apisports-key': API_KEY}
DB_FILE = "backend/team_stats_db.json"

# 40 = Championship (England)
# 141 = Segunda División (Spain)
# 136 = Serie B (Italy)
LEAGUES_TO_PROCESS = [40, 141, 136]
SEASON = 2024
TOKENS_LEFT = 95 # Límite seguro

def make_request(endpoint):
    url = f"{BASE_URL}{endpoint}"
    requests.packages.urllib3.disable_warnings()
    res = requests.get(url, headers=HEADERS, verify=False)
    if res.status_code == 200:
        return res.json()
    return None

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def main():
    db = load_db()
    tokens_used = 0
    
    for league_id in LEAGUES_TO_PROCESS:
        if tokens_used >= TOKENS_LEFT: break
            
        print(f"Obteniendo equipos para la liga {league_id}...")
        teams_data = make_request(f"/teams?league={league_id}&season={SEASON}")
        
        tokens_used += 1 
        
        if not teams_data or not teams_data.get('response'):
            print(f"Error obteniendo liga {league_id}")
            continue
            
        teams = teams_data['response']
        print(f"La liga {league_id} tiene {len(teams)} equipos.")
        
        for t in teams:
            if tokens_used >= TOKENS_LEFT:
                print("Límite de tokens alcanzado. Misión cumplida por hoy.")
                break
                
            team_id = str(t['team']['id'])
            team_name = t['team']['name']
            
            if team_id in db:
                print(f"Equipo {team_name} ya existe. Saltando sin gastar token...")
                continue
                
            print(f"[{tokens_used+1}/{TOKENS_LEFT}] Descargando stats de {team_name}...")
            time.sleep(6.1) # Respetar límite 10 req/min
            
            stats = make_request(f"/teams/statistics?league={league_id}&season={SEASON}&team={team_id}")
            tokens_used += 1
            
            if stats and stats.get('response'):
                r = stats['response']
                fixt = r.get('fixtures', {})
                goals = r.get('goals', {})
                
                clean_sheet = r.get('clean_sheet', {}).get('total', 0)
                failed_to_score = r.get('failed_to_score', {}).get('total', 0)
                total_matches = fixt.get('played', {}).get('total', 1)
                if total_matches == 0: total_matches = 1
                
                form_str = r.get('form', '')
                if not form_str: form_str = ''
                
                db[team_id] = {
                    "name": team_name,
                    "league": league_id,
                    "clean_sheet_rate": clean_sheet / total_matches,
                    "failed_rate": failed_to_score / total_matches,
                    "form": form_str[-5:]
                }
                save_db(db)
                print(f"  -> Guardado {team_name}")
            else:
                print(f"  -> Error API con {team_name}")
                
    print(f"Proceso finalizado. Tokens usados: {tokens_used}")

if __name__ == "__main__":
    main()
