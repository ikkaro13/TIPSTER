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
            print(f"[SofaScraper] Falla de conexión con SofaScore. HTTP {res.status_code}")
            return None
            
        events = res.json().get('events', [])
        print(f"[SofaScraper] Encontrados {len(events)} eventos en vivo en SofaScore.")
        
        import difflib
        
        best_match_id = None
        best_score = 0
        
        for e in events:
            shome = e.get('homeTeam', {}).get('name', '').lower()
            saway = e.get('awayTeam', {}).get('name', '').lower()
            
            # Ratio directo
            r_home = difflib.SequenceMatcher(None, home_name.lower(), shome).ratio()
            r_away = difflib.SequenceMatcher(None, away_name.lower(), saway).ratio()
            score_direct = (r_home + r_away) / 2
            
            # Ratio cruzado
            r_cross_home = difflib.SequenceMatcher(None, home_name.lower(), saway).ratio()
            r_cross_away = difflib.SequenceMatcher(None, away_name.lower(), shome).ratio()
            score_cross = (r_cross_home + r_cross_away) / 2
            
            total_score = max(score_direct, score_cross)
            
            if total_score > best_score and total_score >= 0.55: # Umbral de confianza del 55%
                best_score = total_score
                best_match_id = e.get('id')
                target_event = e
                
        sofascore_event_id = best_match_id
                
        if not sofascore_event_id:
            print(f"[SofaScraper] Evento no encontrado en SofaScore para: {home_name}. El mejor score fue {best_score}")
            return None
            
        print(f"[SofaScraper] Match enganchado exitosamente con SofaScore ID {sofascore_event_id}")
            
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

        # Extract Live Score
        live_home_score = target_event.get('homeScore', {}).get('current', 0)
        live_away_score = target_event.get('awayScore', {}).get('current', 0)
        live_score_str = f"{live_home_score}-{live_away_score}"
        
        # Extract True Minute from SofaScore
        status_code = target_event.get('status', {}).get('code', 0)
        if status_code == 31: # Halftime
            minute = 45
        elif status_code in [6, 7]: # 1st or 2nd half
            import time
            start_ts = target_event.get('time', {}).get('currentPeriodStartTimestamp', 0)
            if start_ts > 0:
                elapsed = int((time.time() - start_ts) / 60)
                minute = elapsed if status_code == 6 else 45 + elapsed

        return {
            "minute": minute,
            "score": live_score_str,
            "stats": stats_data,
            "xg_live": round(xg_live, 2)
        }
        
    except Exception as e:
        print(f"[SofaScraper] Error: {e}")
        return None
