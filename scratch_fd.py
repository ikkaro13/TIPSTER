import requests

url = "https://api.football-data.org/v4/matches"
headers = {
    'X-Auth-Token': 'd238787ab8b3494592c7c805b9be8b84'
}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    data = response.json()
    matches = data.get('matches', [])
    print(f"Football-data.org matches for today: {len(matches)}")
    for m in matches[:3]:
        home = m.get('homeTeam', {}).get('name', '')
        away = m.get('awayTeam', {}).get('name', '')
        comp = m.get('competition', {}).get('name', '')
        print(f"[{comp}] {home} vs {away}")
else:
    print(f"Error {response.status_code}: {response.text}")
