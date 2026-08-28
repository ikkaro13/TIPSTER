from datetime import datetime, timezone, timedelta
import requests

mx_tz = timezone(timedelta(hours=-6))
query_date = datetime.now(mx_tz).strftime("%Y-%m-%d")
calendar_matches = []

print(f"Buscando para query_date = {query_date}")

theodds_key = "4e9ed7e82f648f0ea89f8cab32123953"
fallback_leagues = ['soccer_mexico_ligamx', 'soccer_usa_mls', 'soccer_epl', 'soccer_spain_la_liga', 'soccer_italy_serie_a']

for lg in fallback_leagues:
    url = f"https://api.the-odds-api.com/v4/sports/{lg}/odds/?apiKey={theodds_key}&regions=us&markets=h2h"
    try:
        res = requests.get(url, verify=False, timeout=5)
        if res.status_code == 200:
            odds_data = res.json()
            for g in odds_data:
                dt = datetime.fromisoformat(g['commence_time'].replace('Z', '+00:00'))
                dt_mx = dt.astimezone(mx_tz)
                
                if dt_mx.strftime("%Y-%m-%d") != query_date:
                    continue
                    
                calendar_matches.append({
                    "league": lg,
                    "home": g.get('home_team'),
                    "time": dt_mx.strftime("%Y-%m-%d %H:%M")
                })
        else:
            print(f"Error en {lg}: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Exception en {lg}: {e}")

print(f"Encontrados en TheOddsAPI: {len(calendar_matches)}")

# Test Football-Data
fd_key = "d238787ab8b3494592c7c805b9be8b84"
url = f"https://api.football-data.org/v4/matches?dateFrom={query_date}&dateTo={query_date}"
headers = {'X-Auth-Token': fd_key}

try:
    res = requests.get(url, headers=headers, verify=False, timeout=5)
    if res.status_code == 200:
        fd_data = res.json().get('matches', [])
        for m in fd_data:
            dt_str = m.get('utcDate')
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00')) if dt_str else datetime.now(timezone.utc)
            dt_mx = dt.astimezone(mx_tz)
            calendar_matches.append({"league": "FD", "home": "X"})
    else:
        print(f"Error FD: {res.status_code}")
except Exception as e:
    print(f"Exception FD: {e}")

print(f"Encontrados totales: {len(calendar_matches)}")
