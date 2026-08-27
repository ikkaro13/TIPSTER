import sys
sys.path.append('D:\\Work\\ANTIGRAVITY\\TIPSTER\\backend')
from api_football_engine import make_api_request
import json

search_terms = ["Championship", "Segunda", "Serie B"]

for term in search_terms:
    print(f"Buscando {term}...")
    res = make_api_request(f"/leagues?search={term}")
    if res and res.get('response'):
        for l in res['response']:
            print(f" ID: {l['league']['id']} - {l['league']['name']} ({l['country']['name']})")
    else:
        print(" No encontrado o error")
