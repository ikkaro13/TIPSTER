import requests
import json
url = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"
headers = {'User-Agent': 'Mozilla/5.0'}
res = requests.get(url, headers=headers)
if res.status_code == 200:
    data = res.json()
    events = data.get('events', [])
    print(f"Encontrados {len(events)} partidos en ESPN.")
    for e in events[:5]:
        print(e['name'])
else:
    print(f"Status code: {res.status_code}")
