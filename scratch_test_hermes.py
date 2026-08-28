import sys
import json
sys.path.append('backend')
from analytics import calculate_match_probabilities, find_value_bets
from odds_connector import parse_odds_data
import sqlite3

# Cargar odds
with open('odds_dump.json', 'r', encoding='utf-8') as f:
    odds_data = json.load(f)

# Buscar Bet365 u otro
selected_bookie = odds_data['bookmakers'][0]
for b in odds_data.get('bookmakers', []):
    if b['name'] == 'Bet365':
        selected_bookie = b
        break

bookmaker_odds = parse_odds_data(selected_bookie)

real_probs = calculate_match_probabilities("Platense", "Instituto", {}, historical_context={"home": {}, "away": {}})

print("--- PROBABILIDADES MATEMÁTICAS (PLATENSE VS INSTITUTO) ---")
print(f"Ganador Local: {real_probs['home']:.1f}%")
print(f"Empate No Acción (DNB Local): {real_probs['dnb_home']:.1f}%")
print(f"Medio Tiempo (Gana Local): {real_probs['ht_home']:.1f}%")
print(f"Doble Oportunidad 1X: {real_probs['dc_1x']:.1f}%")
print(f"Hándicap -1.0 Local: {real_probs.get('home_minus_1_0', 0):.1f}%\n")

value_analysis = find_value_bets(real_probs, bookmaker_odds)

print("--- REPORTE DE HERMES (VALUE BETS) ---")
for key in ['main_line', 'medium_risk', 'dreamer']:
    bet = value_analysis.get(key)
    if bet:
        print(f"Nivel [{key.upper()}]: {bet['pick']} (Cuota {bet['odds']}) -> Edge de valor: +{bet['edge']:.1f}%")
    else:
        print(f"Nivel [{key.upper()}]: Sin valor detectado.")
