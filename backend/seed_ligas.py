import sys
import os
import time

# Necesitamos añadir la ruta base para que pueda importar módulos
sys.path.append(os.path.dirname(__file__))

from api_football_engine import make_api_request
from data_engine import get_national_elo, save_national_elo, save_historical_match
from elo_updater import calculate_elo_change

TOP_10_LEAGUES = {
    "Superettan": 114,
    "K League 1": 292,
    "Serie B": 136,
    "Segunda Division": 141,
    "Saudi Pro League": 307,
    "Eerste Divisie": 89,
    "Liga Expansion MX": 263,
    "Scottish Premiership": 179,
    "A-League": 188,
    "Pro League Belgica": 144
}

SEASONS = [2023, 2024]

def seed_leagues():
    print("🧠 INICIANDO INYECCIÓN MASIVA DE ELO PARA CLUBES...")
    
    # 1. Cargar DB a la memoria RAM para no hacer 7000 escrituras al disco
    db = get_national_elo()
    
    matches_processed = 0
    
    for league_name, league_id in TOP_10_LEAGUES.items():
        print(f"\n🌍 Procesando {league_name} (ID: {league_id})...")
        
        all_league_matches = []
        
        for season in SEASONS:
            print(f"   Descargando Temporada {season}...")
            endpoint = f"/fixtures?league={league_id}&season={season}&status=FT"
            data = make_api_request(endpoint)
            
            if data and "response" in data:
                all_league_matches.extend(data["response"])
                print(f"   -> Obtenidos {len(data['response'])} partidos.")
            else:
                print(f"   -> Error o sin datos para la temporada {season}.")
                
            time.sleep(7) # Pausa larga para no rebasar el límite de 10 peticiones/minuto
            
        # 2. Ordenar cronológicamente (del más antiguo al más reciente)
        all_league_matches.sort(key=lambda x: x["fixture"]["timestamp"])
        
        # 3. Procesar resultados cronológicamente
        for match in all_league_matches:
            try:
                home_team = match["teams"]["home"]["name"]
                away_team = match["teams"]["away"]["name"]
                home_goals = match["goals"]["home"]
                away_goals = match["goals"]["away"]
                
                if home_goals is None or away_goals is None:
                    continue
                    
                # Si el equipo no existe, le asignamos 1500 (Promedio de Liga)
                # Nota: National Teams usan 1750, pero 1500 es el estándar mundial para clubes base
                r1 = db.get(home_team, 1500)
                r2 = db.get(away_team, 1500)
                
                new_r1, new_r2 = calculate_elo_change(r1, r2, home_goals, away_goals)
                
                # Guardar el partido historico para Machine Learning
                total_goals = home_goals + away_goals
                btts = 1 if home_goals > 0 and away_goals > 0 else 0
                outcome = 2 if home_goals > away_goals else 0 if away_goals > home_goals else 1
                
                match_data = {
                    "id": str(match["fixture"]["id"]),
                    "league_id": league_id,
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_elo": r1,
                    "away_elo": r2,
                    "elo_diff": r1 - r2,
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "total_goals": total_goals,
                    "btts": btts,
                    "outcome": outcome
                }
                save_historical_match(match_data)
                
                db[home_team] = new_r1
                db[away_team] = new_r2
                matches_processed += 1
            except Exception as e:
                continue
            
    # 4. Guardar DB de un solo golpe
    print(f"\n💾 Guardando {len(db)} equipos en tipster.db...")
    save_national_elo(db)
    print(f"✅ ¡Inyección Completada! {matches_processed} partidos analizados matemáticamente.")

if __name__ == "__main__":
    seed_leagues()
