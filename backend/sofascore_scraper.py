import requests
import json
import urllib3

urllib3.disable_warnings()

# User-Agent para imitar navegador
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Origin': 'https://www.sofascore.com',
    'Referer': 'https://www.sofascore.com/'
}

def get_live_stats(mock=False, match_id=None):
    """
    Obtiene las estadísticas en vivo raspando la API de SofaScore.
    Se utiliza para alta frecuencia (GPI).
    """
    if mock:
        return {
            "minute": 13,
            "stats": {
                "dangerous_attacks": 45,
                "shots_on_target": 5, # Increased to simulate pressure
                "shots_off_target": 4,
                "corners": 3,
                "possession": 68
            },
            "xg_live": (45 * 0.01) + (5 * 0.11)
        }
        
    try:
        from api_football_engine import CACHE
        # 1. Obtener nombres de equipos desde API-Football usando el caché
        fixture_list = CACHE['fixtures']['data']
        target_fixture = next((f for f in fixture_list if str(f['fixture']['id']) == str(match_id)), None)
        
        if not target_fixture:
            print(f"[SofaScraper] Error: Fixture {match_id} no encontrado en el catálogo de API-Football.")
            return None
            
        home_name = target_fixture['teams']['home']['name']
        away_name = target_fixture['teams']['away']['name']
        minute = target_fixture['fixture']['status'].get('elapsed', 0)
        if minute is None: minute = 0
        
        # 2. Buscar evento en vivo en SofaScore
        print(f"[SofaScraper] Buscando: {home_name} vs {away_name}")
        res = requests.get('https://api.sofascore.com/api/v1/sport/football/events/live', headers=HEADERS, verify=False, timeout=5)
        if res.status_code != 200:
            return None
            
        events = res.json().get('events', [])
        
        # Fuzzy Match Mejorado
        home_words = home_name.lower().split()
        away_words = away_name.lower().split()
        
        target_word_home = home_words[0] if len(home_words) > 0 else ""
        if len(target_word_home) < 4 and len(home_words) > 1:
             target_word_home = home_words[1]
             
        target_word_away = away_words[0] if len(away_words) > 0 else ""
        if len(target_word_away) < 4 and len(away_words) > 1:
             target_word_away = away_words[1]
             
        sofascore_event_id = None
        for e in events:
            shome = e.get('homeTeam', {}).get('name', '').lower()
            saway = e.get('awayTeam', {}).get('name', '').lower()
            
            # Buscar coincidencia cruzada o directa
            if (target_word_home in shome or target_word_home in saway) or \
               (target_word_away in shome or target_word_away in saway):
                sofascore_event_id = e.get('id')
                break
                
        if not sofascore_event_id:
            print(f"[SofaScraper] Evento no encontrado en SofaScore para: {home_name}")
            return None
            
        # 3. Obtener estadísticas del evento en SofaScore
        stats_url = f"https://api.sofascore.com/api/v1/event/{sofascore_event_id}/statistics"
        sres = requests.get(stats_url, headers=HEADERS, verify=False, timeout=5)
        
        # Objeto de estadísticas para ATHENA
        stats_data = {
            "dangerous_attacks": 0,
            "shots_on_target": 0,
            "shots_off_target": 0,
            "corners": 0,
            "possession": 50
        }
        
        if sres.status_code == 200:
            sjson = sres.json()
            st = sjson.get('statistics', [])
            if len(st) > 0:
                all_period = next((p for p in st if p['period'] == 'ALL'), None)
                if all_period:
                    for group in all_period.get('groups', []):
                        for item in group.get('statisticsItems', []):
                            name = item.get('name', '')
                            # Extraer valores numéricos
                            hval = str(item.get('home', '0')).replace('%', '')
                            aval = str(item.get('away', '0')).replace('%', '')
                            try:
                                hval = int(hval)
                                aval = int(aval)
                            except:
                                hval = 0
                                aval = 0
                                
                            val_total = hval + aval
                            
                            # Mapear
                            if "Ball possession" in name:
                                stats_data['possession'] = max(hval, aval) # Tomamos la posesión del dominador
                            elif "Corner kicks" in name:
                                stats_data['corners'] = val_total
                            elif "Shots on target" in name:
                                stats_data['shots_on_target'] = val_total
                            elif "Shots off target" in name:
                                stats_data['shots_off_target'] = val_total
                            elif "Attacks" in name or "Dangerous" in name or "Big chances" in name:
                                stats_data['dangerous_attacks'] += val_total
                                
        # Calculate Live Expected Goals (xG)
        xg_live = (stats_data['dangerous_attacks'] * 0.01) + (stats_data['shots_on_target'] * 0.11)
        
        # Real goals (We can extract them from the API if needed, but for simplicity we assume 0 or we get them from the caller. 
        # Actually sofascore API has goals, let's just assume we check xG_live against a threshold for now)
        # We will pass xg_live in the return so athena_engine can decide.
        
        return {
            "minute": minute,
            "stats": stats_data,
            "xg_live": round(xg_live, 2)
        }
        
    except Exception as e:
        print(f"[SofaScraper] Error: {e}")
        return None
