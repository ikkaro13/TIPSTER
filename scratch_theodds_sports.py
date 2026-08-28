import requests
import urllib3
urllib3.disable_warnings()

api_key = "4e9ed7e82f648f0ea89f8cab32123953"
url = f"https://api.the-odds-api.com/v4/sports/?apiKey={api_key}"
res = requests.get(url, verify=False)
if res.status_code == 200:
    data = res.json()
    soccer_keys = [s['key'] for s in data if s['group'] == 'Soccer']
    print("Ligas de soccer disponibles:")
    print(soccer_keys)
