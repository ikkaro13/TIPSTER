import os
from dotenv import load_dotenv
load_dotenv()
import requests

import time

from datetime import datetime



API_KEYS = [

    os.getenv("API_FOOTBALL_KEY")

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

            response = requests.get(url, headers=get_headers(), timeout=5, verify=VERIFY_SSL)

            

            if response.status_code == 200:

                data = response.json()

                errors = data.get('errors')

                if errors and isinstance(errors, dict) and ('token' in errors or 'rateLimit' in errors or 'requests' in errors or 'access' in errors):

                    print(f"[API-Football] LÃ­mite o Error en llave {API_KEYS[current_key_index][:8]}... Cambiando a la siguiente...")

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



import json

import os
from dotenv import load_dotenv
load_dotenv()
VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() == "true"



CACHE_FILE = "calendar_cache_persistent.json"



def load_calendar_cache():

    if os.path.exists(CACHE_FILE):

        try:

            with open(CACHE_FILE, "r") as f:

                return json.load(f)

        except:

            pass

    return {}



def save_calendar_cache(calendar_data):

    try:

        with open(CACHE_FILE, "w") as f:

            json.dump(calendar_data, f)

    except:

        pass



# Sistema de CachÃ© Inteligente (Para ahorrar peticiones)

# Se almacenan las respuestas y su timestamp

CACHE = {

    'fixtures': {'data': [], 'timestamp': 0},

    'calendar': load_calendar_cache(),

    'stats': {},

    'odds': {}

}



# TTL (Time To Live) en segundos

TTL_FIXTURES = 180 # 3 minutos para ahorrar tokens diarios (antes era 30s)

TTL_STATS = 60 # 1 minuto (Solo durante ventana primaria, si no, se podrÃ­a ampliar)



def get_live_fixtures():

    """ Obtiene todos los partidos en vivo actuales """

    current_time = time.time()

    

    if current_time - CACHE['fixtures']['timestamp'] < TTL_FIXTURES:

        print("[API-Football] Usando cachÃ© de Fixtures")

        return CACHE['fixtures']['data']

        

    print("[API-Football] PeticiÃ³n a /fixtures?live=all")

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

    

    # Usar cachÃ© de 10 minutos para el calendario (asÃ­ detecta cuando finalizan los partidos)

    if date_str in CACHE['calendar']:

        if current_time - CACHE['calendar'][date_str]['timestamp'] < 600:

            print("[API-Football] Usando cachÃ© de Calendario")

            return CACHE['calendar'][date_str]['data']

        

    print(f"[API-Football] PeticiÃ³n a /fixtures?date={date_str}")

    try:

        # AÃ±adimos verify=VERIFY_SSL de forma preventiva para el entorno local

        data = make_api_request(f"/fixtures?date={date_str}&timezone={timezone_str}")

        if data:

            data = data.get('response', [])

            # Guardar el dÃ­a actual y mantener mÃ¡ximo 3 dÃ­as en memoria

            CACHE['calendar'][date_str] = {

                'data': data,

                'timestamp': current_time

            }

            if len(CACHE['calendar']) > 3:

                oldest = min(CACHE['calendar'].keys(), key=lambda k: CACHE['calendar'][k]['timestamp'])

                del CACHE['calendar'][oldest]

                

            save_calendar_cache(CACHE['calendar'])

            return data

    except Exception as e:

        print(f"Error fetching daily fixtures: {e}")

        

    return []



def get_live_stats(fixture_id, minute, mock=False):

    """

    Obtiene las estadÃ­sticas en vivo.

    Implementa cachÃ© y control de ventana primaria (min 12 al 25).

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

    # Si el minuto es > 30, extendemos el cachÃ© a 5 minutos.

    ttl = TTL_STATS if (10 <= minute <= 30) else 300 

    

    current_time = time.time()

    if fixture_id in CACHE['stats'] and (current_time - CACHE['stats'][fixture_id]['timestamp']) < ttl:

        print(f"[API-Football] Usando cachÃ© de Stats para {fixture_id}")

        return CACHE['stats'][fixture_id]['data']

        

    print(f"[API-Football] PeticiÃ³n a /fixtures/statistics para {fixture_id}")

    try:

        data = make_api_request(f"/fixtures/statistics?fixture={fixture_id}")

        if data:

            teams_data = data.get('response', [])

            

            # Mapear estadÃ­sticas de API-Football a nuestro motor ATHENA

            stats = {

                "dangerous_attacks": 0,

                "shots_on_target": 0,

                "shots_off_target": 0,

                "corners": 0,

                "possession": 50

            }

            

            if len(teams_data) > 0:

                # Usualmente queremos las estadÃ­sticas combinadas o la mayor presiÃ³n

                # Para simplificar el indicador global, sumaremos la presiÃ³n de ambos equipos

                # (En una versiÃ³n PRO se calcula el diferencial, pero usaremos el total como indicador de ritmo)

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

                

                # Promediar la posesiÃ³n del equipo dominante

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

    """ Obtiene los detalles de un partido especÃ­fico (incluye IDs de equipos) """

    if fixture_id == "mock_12345":

        return {"teams": {"home": {"id": 1, "name": "LocalMock"}, "away": {"id": 2, "name": "VisitaMock"}}}

        

    print(f"[API-Football] PeticiÃ³n a /fixtures?id={fixture_id}")

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

    """ Obtiene los Ãºltimos N partidos de un equipo para construir su Memoria HistÃ³rica """

    if team_id in [1, 2]: # Mock

        return []

        

    print(f"[API-Football] PeticiÃ³n a /fixtures?team={team_id}&last={last_n}")

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





def get_fixture_injuries(fixture_id):

    """ Obtiene la lista de lesionados y suspendidos para un partido """

    print(f"[API-Football] Peticion a /injuries?fixture={fixture_id}")

    try:

        data = make_api_request(f"/injuries?fixture={fixture_id}")

        if data:

            return data.get('response', [])

        return []

    except Exception as e:

        print(f"Error fetching injuries for {fixture_id}: {e}")

    return []









