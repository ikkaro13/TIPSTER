import sys
sys.path.append('backend')
from api_football_engine import make_api_request
import json

res = make_api_request('/odds?fixture=1549148')
if res and res.get('response'):
    with open('odds_dump.json', 'w', encoding='utf-8') as f:
        json.dump(res['response'][0], f, indent=4)
    print("Odds dump saved.")
else:
    print("Sin cuotas")
