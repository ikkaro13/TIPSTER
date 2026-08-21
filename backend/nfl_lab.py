import requests
import json
import statistics

API_KEY = "4e9ed7e82f648f0ea89f8cab32123953"
SPORT = "americanfootball_nfl"
REGIONS = "us,uk" # Expandimos para ver casinos europeos afilados
MARKETS = "spreads" # Solo buscaremos hándicaps (donde están los números clave)
ODDS_FORMAT = "decimal"

# Números clave en la NFL
KEY_NUMBERS = [3.0, 7.0, 10.0]

def analyze_key_numbers():
    print("🏈 Escaneando discrepancias de Hándicaps y Números Clave...")
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/?apiKey={API_KEY}&regions={REGIONS}&markets={MARKETS}&oddsFormat={ODDS_FORMAT}"
    
    response = requests.get(url, verify=False)
    
    if response.status_code != 200:
        print("❌ Error al conectar.")
        return
        
    games = response.json()
    print(f"✅ Analizando {len(games)} juegos...\n")
    
    for game in games:
        home_team = game['home_team']
        away_team = game['away_team']
        
        # Diccionario para agrupar las líneas que ofrece cada casino por equipo
        # Ejemplo: "Kansas City Chiefs": {"DraftKings": -3.5, "BetUS": -2.5, ...}
        spreads_by_team = {home_team: {}, away_team: {}}
        
        for bookie in game.get('bookmakers', []):
            bookie_name = bookie['title']
            for market in bookie.get('markets', []):
                if market['key'] == 'spreads':
                    for outcome in market['outcomes']:
                        team = outcome['name']
                        point = outcome.get('point')
                        if point is not None and team in spreads_by_team:
                            spreads_by_team[team][bookie_name] = point
                            
        # Analizar si hay discrepancias importantes por equipo
        for team, lines in spreads_by_team.items():
            if len(lines) < 3:
                continue # No hay suficientes casinos para comparar
                
            all_points = list(lines.values())
            most_common_line = statistics.mode(all_points) # El consenso de Las Vegas
            
            # Buscar si algún casino despistado nos ofrece una línea mucho mejor
            for bookie_name, point in lines.items():
                if point > most_common_line:
                    # Diferencia matemática. Ej: Consenso es +2.5, pero el casino nos da +3.5
                    
                    # Verificamos si esta discrepancia cruza un Número Clave (3, 7, 10)
                    crossed_key_num = None
                    for kn in KEY_NUMBERS:
                        if most_common_line < kn and point >= kn:
                            crossed_key_num = kn
                            break
                        if most_common_line < -kn and point >= -kn:
                            crossed_key_num = -kn
                            break
                    
                    if crossed_key_num is not None:
                        print("==================================================")
                        print(f"🚨 ¡ALERTA DE VENTAJA MATEMÁTICA (KEY NUMBER)! 🚨")
                        print(f"Juego: {away_team} @ {home_team}")
                        print(f"Equipo a apostar: {team}")
                        print(f"Consenso de Las Vegas: {most_common_line}")
                        print(f"🔥 CASINO LENTO: {bookie_name} está regalando la línea en {point}")
                        print(f"📈 Cruzaste el número clave de {abs(crossed_key_num)} puntos.")
                        print("==================================================\n")

if __name__ == "__main__":
    analyze_key_numbers()
