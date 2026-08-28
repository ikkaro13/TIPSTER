import sys
sys.path.append('backend')
from api_football_engine import make_api_request
import json

# Try to search the correct ID for Veikkausliiga
res = make_api_request("/leagues?search=Veikkausliiga")
if res and "response" in res:
    print(json.dumps(res["response"], indent=2))
