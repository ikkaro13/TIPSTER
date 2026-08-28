import requests
import urllib3
urllib3.disable_warnings()

api_key = "4e9ed7e82f648f0ea89f8cab32123953"
url = f"https://api.the-odds-api.com/v4/sports/soccer_mexico_ligamx/odds/?apiKey={api_key}&regions=us&markets=h2h"
res = requests.get(url, verify=False)
if res.status_code == 200:
    data = res.json()
    print(f"Partidos de Liga MX: {len(data)}")
    for g in data[:3]:
        print(f"{g['home_team']} vs {g['away_team']} a las {g['commence_time']}")
else:
    print(f"Error: {res.status_code} - {res.text}")
