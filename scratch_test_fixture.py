import sys
sys.path.append('backend')
from api_football_engine import make_api_request
import json

res = make_api_request('/fixtures?date=2026-08-28')
if res and res.get('response'):
    print(f"Encontrados {len(res['response'])} partidos.")
    for fix in res['response'][:3]:
        print(f"ID: {fix['fixture']['id']} - {fix['teams']['home']['name']} vs {fix['teams']['away']['name']}")
else:
    print("Sin datos")
