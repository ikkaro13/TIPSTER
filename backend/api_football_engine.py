import requests
import time
from datetime import datetime

API_KEYS = [
    "7419e977170de5db2ea68791e952179f"
]
current_key_index = 0

BASE_URL = "https://v3.football.api-sports.io"

def get_headers():
    return {'x-apisports-key': API_KEYS[current_key_index]}

def make_api_request(endpoint):
    global current_key_index
    attempts = 0
    while attempts < len(API_KEYS):
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, headers=get_headers(), timeout=5, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                errors = data.get('errors')
                if errors and isinstance(errors, dict) and ('token' in errors or 'rateLimit' in errors or 'requests' in errors or 'access' in errors):
                    print(f"[API-Football] Límite o Error en llave {API_KEYS[current_key_index][:8]}... Cambiando a la siguiente...")
                    current_key_index = (current_key_index + 1) % len(API_KEYS)
                    attempts += 1
                    continue
                return data
            else:
                print(f"[API-Football] Error HTTP {response.status_code}. Cambiando llave...")
                current_key_index = (current_key_index + 1) % len(API_KEYS)
                attempts += 1
                continue
                
        except Exception as e:
            print(f"[API-Football] Error/Timeout. Cambiando llave... {e}")
            current_key_index = (current_key_index + 1) % len(API_KEYS)
            attempts += 1
            continue
            
    return None

# Sistema de Caché Inteligente (Para ahorrar peticiones)
# Se almacenan las respuestas y su timestamp
CACHE = {
    'fixtures': {'data': [], 'timestamp': 0},
    'calendar': {'data': [], 'timestamp': 0, 'date': ''},
    'stats': {},
    'odds': {}
}

# TTL (Time To Live) en segundos
TTL_FIXTURES = 180 # 3 minutos para ahorrar tokens diarios (antes era 30s)
TTL_STATS = 60 # 1 minuto (Solo durante ventana primaria, si no, se podría ampliar)

def get_live_fixtures():
    """ Obtiene todos los partidos en vivo actuales """
    current_time = time.time()
    
    if current_time - CACHE['fixtures']['timestamp'] < TTL_FIXTURES:
        print("[API-Football] Usando caché de Fixtures")
        return CACHE['fixtures']['data']
        
    print("[API-Football] Petición a /fixtures?live=all")
    try:
        data = make_api_request("/fixtures?live=all")
        if data:
            data = data.get('response', [])
            CACHE['fixtures'] = {'data': data, 'timestamp': current_time}
            return data
    except Exception as e:
        print(f"Error fetching live fixtures: {e}")
        
    return []

def get_daily_fixtures(date_str, timezone_str="America/Mexico_City"):
    """ Obtiene todos los partidos para una fecha dada (YYYY-MM-DD) """
    current_time = time.time()
    
    # Usar caché de 1 hora para el calendario del día
    if CACHE['calendar']['date'] == date_str and (current_time - CACHE['calendar']['timestamp']) < 3600:
        print("[API-Football] Usando caché de Calendario")
        return CACHE['calendar']['data']
        
    print(f"[API-Football] Petición a /fixtures?date={date_str}")
    try:
        # Añadimos verify=False de forma preventiva para el entorno local
        data = make_api_request(f"/fixtures?date={date_str}&timezone={timezone_str}")
        if data:
            data = data.get('response', [])
            CACHE['calendar']['data'] = data
            CACHE['calendar']['timestamp'] = current_time
            CACHE['calendar']['date'] = date_str
            return data
    except Exception as e:
        print(f"Error fetching daily fixtures: {e}")
        
    return []

def get_live_stats(fixture_id, minute, mock=False):
    """
    Obtiene las estadísticas en vivo.
    Implementa caché y control de ventana primaria (min 12 al 25).
    """
    if mock:
        return {
            "dangerous_attacks": 45,
            "shots_on_target": 2,
            "shots_off_target": 4,
            "corners": 3,
            "possession": 68
        }
        
    # Verificar si estamos fuera de la ventana primaria para ahorrar peticiones
    # Si el minuto es > 30, extendemos el caché a 5 minutos.
    ttl = TTL_STATS if (10 <= minute <= 30) else 300 
    
    current_time = time.time()
    if fixture_id in CACHE['stats'] and (current_time - CACHE['stats'][fixture_id]['timestamp']) < ttl:
        print(f"[API-Football] Usando caché de Stats para {fixture_id}")
        return CACHE['stats'][fixture_id]['data']
        
    print(f"[API-Football] Petición a /fixtures/statistics para {fixture_id}")
    try:
        data = make_api_request(f"/fixtures/statistics?fixture={fixture_id}")
        if data:
            teams_data = data.get('response', [])
            
            # Mapear estadísticas de API-Football a nuestro motor ATHENA
            stats = {
                "dangerous_attacks": 0,
                "shots_on_target": 0,
                "shots_off_target": 0,
                "corners": 0,
                "possession": 50
            }
            
            if len(teams_data) > 0:
                # Usualmente queremos las estadísticas combinadas o la mayor presión
                # Para simplificar el indicador global, sumaremos la presión de ambos equipos
                # (En una versión PRO se calcula el diferencial, pero usaremos el total como indicador de ritmo)
                for team in teams_data:
                    for stat in team.get('statistics', []):
                        val = stat['value']
                        if val is None:
                            val = 0
                        
                        if isinstance(val, str) and "%" in val:
                            val = int(val.replace("%", ""))
                            
                        val = int(val)
                        
                        t = stat['type']
                        if t == "Dangerous Attacks": stats["dangerous_attacks"] += val
                        elif t == "Shots on Goal": stats["shots_on_target"] += val
                        elif t == "Shots off Goal": stats["shots_off_target"] += val
                        elif t == "Corner Kicks": stats["corners"] += val
                
                # Promediar la posesión del equipo dominante
                if len(teams_data) == 2:
                    p1 = next((s['value'] for s in teams_data[0]['statistics'] if s['type'] == 'Ball Possession'), "50%")
                    if p1 is not None:
                        stats["possession"] = max(int(p1.replace("%", "")), 100 - int(p1.replace("%", "")))
            
            CACHE['stats'][fixture_id] = {'data': stats, 'timestamp': current_time}
            return stats
    except Exception as e:
        print(f"Error fetching stats for {fixture_id}: {e}")
        
    return None

def get_fixture_details(fixture_id):
    """ Obtiene los detalles de un partido específico (incluye IDs de equipos) """
    if fixture_id == "mock_12345":
        return {"teams": {"home": {"id": 1, "name": "LocalMock"}, "away": {"id": 2, "name": "VisitaMock"}}}
        
    print(f"[API-Football] Petición a /fixtures?id={fixture_id}")
    try:
        data = make_api_request(f"/fixtures?id={fixture_id}")
        if data:
            response_data = data.get('response', [])
            if response_data:
                return response_data[0]
    except Exception as e:
        print(f"Error fetching fixture details for {fixture_id}: {e}")
    return None

def get_team_historical_stats(team_id, last_n=10):
    """ Obtiene los últimos N partidos de un equipo para construir su Memoria Histórica """
    if team_id in [1, 2]: # Mock
        return []
        
    print(f"[API-Football] Petición a /fixtures?team={team_id}&last={last_n}")
    try:
        data = make_api_request(f"/fixtures?team={team_id}&last={last_n}")
        if data:
            return data.get('response', [])
    except Exception as e:
        print(f"Error fetching historical stats for team {team_id}: {e}")
    return []

def get_fixture_odds(fixture_id):
    import odds_connector
    return odds_connector.fetch_real_odds(fixture_id)

