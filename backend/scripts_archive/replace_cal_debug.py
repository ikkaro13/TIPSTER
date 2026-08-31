import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_func = '''def get_daily_calendar(date: str = None):
    try:
        mx_tz = timezone(timedelta(hours=-6))
        
        if date:
            query_date = date
        else:
            query_date = datetime.now(mx_tz).strftime("%Y-%m-%d")
            
        data = api_football_engine.get_daily_fixtures(query_date, timezone_str="America/Mexico_City")
        calendar_matches = []
        
        if data:
            for match in data:
                fixture = match.get("fixture", {})
                teams = match.get("teams", {})
                league = match.get("league", {})
                
                dt_str = fixture.get("date")
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00')) if dt_str else datetime.now(timezone.utc)
                dt_mx = dt.astimezone(mx_tz)
                
                calendar_matches.append({
                    "id": str(fixture.get("id")),
                    "league": league.get("name", "API-Football League"),
                    "country": league.get("country", "Unknown"),
                    "round": league.get("round", ""),
                    "homeTeam": teams.get("home", {}).get("name", "Unknown"),
                    "awayTeam": teams.get("away", {}).get("name", "Unknown"),
                    "startTime": dt_mx.strftime("%H:%M"),
                    "status": fixture.get("status", {}).get("long", ""),
                    "timestamp": fixture.get("timestamp", 0)
                })
        
        debug_msg = ""
        
        if len(calendar_matches) == 0:
            import requests
            theodds_key = "4e9ed7e82f648f0ea89f8cab32123953"
            fallback_leagues = ['soccer_mexico_ligamx', 'soccer_usa_mls', 'soccer_epl', 'soccer_spain_la_liga', 'soccer_italy_serie_a']
            
            for lg in fallback_leagues:
                url = f"https://api.the-odds-api.com/v4/sports/{lg}/odds/?apiKey={theodds_key}&regions=us&markets=h2h"
                try:
                    res = requests.get(url, verify=False, timeout=7)
                    if res.status_code == 200:
                        odds_data = res.json()
                        for g in odds_data:
                            dt = datetime.fromisoformat(g['commence_time'].replace('Z', '+00:00'))
                            dt_mx = dt.astimezone(mx_tz)
                            
                            if dt_mx.strftime("%Y-%m-%d") != query_date:
                                continue
                                
                            calendar_matches.append({
                                "id": g.get("id", "fallback_id"),
                                "league": lg.replace("soccer_", "").replace("_", " ").title(),
                                "country": "Backup 1",
                                "round": "Regular",
                                "homeTeam": g.get('home_team', ''),
                                "awayTeam": g.get('away_team', ''),
                                "startTime": dt_mx.strftime("%H:%M"),
                                "status": "Not Started",
                                "timestamp": int(dt.timestamp())
                            })
                    else:
                        debug_msg += f"OddsAPI HTTP {res.status_code}. "
                except Exception as e:
                    debug_msg += f"OddsAPI Err: {str(e)[:20]}. "
                    
        if len(calendar_matches) == 0:
            fd_key = "d238787ab8b3494592c7c805b9be8b84"
            url = f"https://api.football-data.org/v4/matches?dateFrom={query_date}&dateTo={query_date}"
            try:
                res = requests.get(url, headers={'X-Auth-Token': fd_key}, verify=False, timeout=7)
                if res.status_code == 200:
                    fd_data = res.json().get('matches', [])
                    for m in fd_data:
                        dt_str = m.get('utcDate')
                        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00')) if dt_str else datetime.now(timezone.utc)
                        dt_mx = dt.astimezone(mx_tz)
                        
                        calendar_matches.append({
                            "id": str(m.get("id", "fd_id")),
                            "league": m.get('competition', {}).get('name', 'Football-Data League'),
                            "country": m.get('area', {}).get('name', 'Backup 2'),
                            "round": "Regular",
                            "homeTeam": m.get('homeTeam', {}).get('name', ''),
                            "awayTeam": m.get('awayTeam', {}).get('name', ''),
                            "startTime": dt_mx.strftime("%H:%M"),
                            "status": m.get('status', 'Not Started'),
                            "timestamp": int(dt.timestamp())
                        })
                else:
                    debug_msg += f"FD HTTP {res.status_code}. "
            except Exception as e:
                debug_msg += f"FD Err: {str(e)[:20]}. "

        calendar_matches.sort(key=lambda x: (x.get("country", ""), x["timestamp"]))
        
        if len(calendar_matches) == 0:
            calendar_matches.append({
                "id": "mock_12345",
                "league": "DEBUG: " + (debug_msg if debug_msg else "Sin errores aparentes pero 0 partidos"),
                "round": "Final",
                "homeTeam": "Google Cloud",
                "awayTeam": "Bloqueó las APIs?",
                "startTime": "20:00",
                "status": "Not Started",
                "timestamp": int(datetime.now().timestamp())
            })

        return {"status": "success", "data": calendar_matches}
        
    except Exception as e:
        return {"status": "error", "message": str(e), "data": []}'''

pattern = r'def get_daily_calendar\(date: str = None\):.*?return \{"status": "error", "message": str\(e\), "data": \[\]\}'
content_new = re.sub(pattern, new_func, content, flags=re.DOTALL)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content_new)
