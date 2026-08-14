import requests
import time
from api_football_engine import make_api_request

# Mapeo de IDs de apuestas de API-Football
BET_ID_MATCH_WINNER = 1
BET_ID_GOALS_OVER_UNDER = 5
BET_ID_BTTS = 8
BET_ID_ASIAN_HANDICAP = 3

# Nombres de bookmakers deseados
PREFERRED_BOOKMAKERS = ["Caliente", "Novibet", "Bet365", "1xBet", "Pinnacle"]

def parse_odds_data(bookmaker_data):
    """
    Traduce el payload de API-Football a nuestro formato interno.
    """
    odds = {}
    bookie_name = bookmaker_data.get('name', 'Unknown')
    bets = bookmaker_data.get('bets', [])
    
    for bet in bets:
        bet_id = bet.get('id')
        values = bet.get('values', [])
        
        if bet_id == BET_ID_MATCH_WINNER:
            for v in values:
                val_str = str(v.get('value')).lower()
                price = float(v.get('odd', 0))
                if val_str == "home":
                    odds['home'] = {"price": price, "bookie": bookie_name}
                elif val_str == "draw":
                    odds['draw'] = {"price": price, "bookie": bookie_name}
                elif val_str == "away":
                    odds['away'] = {"price": price, "bookie": bookie_name}
                    
        elif bet_id == BET_ID_GOALS_OVER_UNDER:
            for v in values:
                val_str = str(v.get('value')).lower()
                price = float(v.get('odd', 0))
                if val_str == "over 1.5":
                    odds['over_1_5'] = {"price": price, "bookie": bookie_name}
                elif val_str == "under 1.5":
                    odds['under_1_5'] = {"price": price, "bookie": bookie_name}
                elif val_str == "over 2.5":
                    odds['over_2_5'] = {"price": price, "bookie": bookie_name}
                elif val_str == "under 2.5":
                    odds['under_2_5'] = {"price": price, "bookie": bookie_name}
                elif val_str == "over 3.5":
                    odds['over_3_5'] = {"price": price, "bookie": bookie_name}
                elif val_str == "under 3.5":
                    odds['under_3_5'] = {"price": price, "bookie": bookie_name}
                    
        elif bet_id == BET_ID_BTTS:
            for v in values:
                val_str = str(v.get('value')).lower()
                price = float(v.get('odd', 0))
                if val_str == "yes":
                    odds['btts_yes'] = {"price": price, "bookie": bookie_name}
                elif val_str == "no":
                    odds['btts_no'] = {"price": price, "bookie": bookie_name}
                    
    # Asegurar defaults si no se encontraron
    default_bookie = bookie_name
    expected_keys = [
        'home', 'draw', 'away', 
        'over_1_5', 'under_1_5', 'over_2_5', 'under_2_5', 'over_3_5', 'under_3_5',
        'btts_yes', 'btts_no', 'home_minus_1_5', 'away_minus_1_5'
    ]
    for key in expected_keys:
        if key not in odds:
            odds[key] = {"price": 0.0, "bookie": default_bookie}
            
    return odds

def get_simulated_odds(bookie_name="Caliente.mx"):
    """
    Fallback cuando no hay tokens o es el mock match.
    """
    return {
        "home": {"price": 2.50, "bookie": bookie_name}, "draw": {"price": 3.10, "bookie": bookie_name}, "away": {"price": 2.90, "bookie": bookie_name},
        "over_1_5": {"price": 1.40, "bookie": bookie_name}, "under_1_5": {"price": 2.80, "bookie": bookie_name},
        "over_2_5": {"price": 2.10, "bookie": bookie_name}, "under_2_5": {"price": 1.70, "bookie": bookie_name},
        "over_3_5": {"price": 3.50, "bookie": bookie_name}, "under_3_5": {"price": 1.25, "bookie": bookie_name},
        "btts_yes": {"price": 1.80, "bookie": bookie_name}, "btts_no": {"price": 1.95, "bookie": bookie_name},
        "home_minus_1_5": {"price": 5.00, "bookie": bookie_name}, "away_minus_1_5": {"price": 6.00, "bookie": bookie_name}
    }

def fetch_real_odds(fixture_id):
    """
    Extrae las cuotas reales de API-Football y busca preferentemente Caliente o Novibet.
    """
    if fixture_id == "mock_12345":
        return get_simulated_odds("Caliente.mx (Simulado)")
        
    try:
        data = make_api_request(f"/odds?fixture={fixture_id}")
        if data:
            # Chequeo de límite de tokens o error de autenticación
            if data.get('errors') or not data.get('response'):
                print(f"[OddsConnector] Error o sin datos: {data.get('errors')}. Usando Fallback.")
                return get_simulated_odds("Caliente.mx (Límite API)")
                
            response_list = data.get('response', [])
            if len(response_list) == 0:
                return get_simulated_odds("Caliente.mx (Sin Cuotas)")
                
            bookmakers = response_list[0].get('bookmakers', [])
            
            # 1. Buscar Caliente o Novibet
            selected_bookie = None
            for pref in PREFERRED_BOOKMAKERS:
                selected_bookie = next((b for b in bookmakers if pref.lower() in b['name'].lower()), None)
                if selected_bookie:
                    break
                    
            # 2. Fallback a la primera disponible si no hay favoritas
            if not selected_bookie and len(bookmakers) > 0:
                selected_bookie = bookmakers[0]
                
            if selected_bookie:
                # Renombramos visualmente a Caliente si estamos usando un proxy
                if not any(pref.lower() in selected_bookie['name'].lower() for pref in ["caliente", "novibet"]):
                    selected_bookie['name'] = f"{selected_bookie['name']} (Proxy Caliente)"
                    
                return parse_odds_data(selected_bookie)
                
    except Exception as e:
        print(f"[OddsConnector] Excepción al extraer cuotas: {e}")
        
    return get_simulated_odds("Caliente.mx (Fallback Error)")

import json
import os

ODDS_CACHE_FILE = "odds_cache_persistent.json"

def load_odds_cache():
    if os.path.exists(ODDS_CACHE_FILE):
        try:
            with open(ODDS_CACHE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_odds_cache(cache):
    try:
        with open(ODDS_CACHE_FILE, "w") as f:
            json.dump(cache, f)
    except:
        pass

ODDS_DATE_CACHE = load_odds_cache()

def fetch_odds_by_date(date_str):
    """
    Extrae las cuotas reales de API-Football para TODOS los partidos de una fecha (YYYY-MM-DD).
    Devuelve un diccionario { fixture_id: odds_data }
    """
    import time
    current_time = time.time()
    
    # Caché de 2 horas (7200s) para cuotas históricas/pre-match
    if date_str in ODDS_DATE_CACHE:
        cache_entry = ODDS_DATE_CACHE[date_str]
        if current_time - cache_entry['timestamp'] < 7200:
            print(f"[OddsConnector] Usando caché PERSISTENTE de cuotas para {date_str}")
            return cache_entry['data']
            
    print(f"[OddsConnector] Descargando cuotas frescas para {date_str}...")
    try:
        data = make_api_request(f"/odds?date={date_str}")
        if data and not data.get('errors') and data.get('response'):
            results = {}
            for item in data.get('response', []):
                fixture_id = str(item.get('fixture', {}).get('id'))
                bookmakers = item.get('bookmakers', [])
                
                selected_bookie = None
                for pref in PREFERRED_BOOKMAKERS:
                    selected_bookie = next((b for b in bookmakers if pref.lower() in b['name'].lower()), None)
                    if selected_bookie:
                        break
                        
                if not selected_bookie and len(bookmakers) > 0:
                    selected_bookie = bookmakers[0]
                    
                if selected_bookie:
                    if not any(pref.lower() in selected_bookie['name'].lower() for pref in ["caliente", "novibet"]):
                        selected_bookie['name'] = f"{selected_bookie['name']} (Proxy Caliente)"
                    results[fixture_id] = parse_odds_data(selected_bookie)
                    
            # Guardar en memoria
            ODDS_DATE_CACHE[date_str] = {
                'timestamp': current_time,
                'data': results
            }
            # Mantener solo los últimos 3 días para evitar saturación de RAM/Disco
            if len(ODDS_DATE_CACHE) > 3:
                oldest = min(ODDS_DATE_CACHE.keys(), key=lambda k: ODDS_DATE_CACHE[k]['timestamp'])
                del ODDS_DATE_CACHE[oldest]
                
            save_odds_cache(ODDS_DATE_CACHE)
            return results
    except Exception as e:
        print(f"[OddsConnector] Excepción al extraer cuotas globales: {e}")
        
    return {}
