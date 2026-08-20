import requests
import json
import datetime

API_KEY = "7419e977170de5db2ea68791e952179f"
BASE_URL = "https://v1.american-football.api-sports.io"

HEADERS = {
    'x-apisports-key': API_KEY,
}

def get_nfl_games(date_str):
    print(f"🏈 Buscando juegos de NFL para la fecha: {date_str}...")
    url = f"{BASE_URL}/games?date={date_str}"
    
    response = requests.get(url, headers=HEADERS, verify=False)
    if response.status_code == 200:
        data = response.json()
        games = data.get('response', [])
        print(f"✅ Se encontraron {len(games)} juegos.")
        
        for game in games:
            game_id = game['game']['id']
            home = game['teams']['home']['name']
            away = game['teams']['away']['name']
            status = game['game']['status']['short']
            print(f"\nID: {game_id} | {away} @ {home} [{status}]")
            
            # Buscar cuotas para este juego
            get_nfl_odds(game_id)
    else:
        print(f"❌ Error en la API: {response.status_code}")
        print(response.text)

def get_nfl_odds(game_id):
    url = f"{BASE_URL}/odds?game={game_id}"
    response = requests.get(url, headers=HEADERS, verify=False)
    
    if response.status_code == 200:
        data = response.json()
        odds_data = data.get('response', [])
        if not odds_data:
            print("  ↳ Sin cuotas (odds) disponibles aún.")
            return
            
        bookmakers = odds_data[0].get('bookmakers', [])
        # Tratamos de buscar a Bet365 o la primera que aparezca
        if bookmakers:
            bookie = bookmakers[0]
            print(f"  ↳ Casa de Apuestas: {bookie['name']}")
            for bet in bookie['bets']:
                if bet['name'] == 'Moneyline': # Ganador del partido
                    print("    💰 Moneyline (Ganador):")
                    for val in bet['values']:
                        print(f"      - {val['value']}: {val['odd']}")
                elif bet['name'] == 'Handicap': # Spread
                    print("    🎯 Spread (Handicap):")
                    # Solo mostramos los 2 primeros para no saturar la pantalla
                    for val in bet['values'][:2]:
                        print(f"      - {val['value']}: {val['odd']}")
                elif bet['name'] == 'Over/Under': # Totales
                    print("    📊 Totales (Over/Under):")
                    for val in bet['values'][:2]:
                        print(f"      - {val['value']}: {val['odd']}")
    else:
        print(f"  ↳ Error al buscar cuotas: {response.status_code}")

if __name__ == "__main__":
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    print("====================================")
    print(" 🏈 LABORATORIO NFL - ATHENA ALPHA 🏈")
    print("====================================")
    get_nfl_games(today)
