import threading
import uvicorn
from main import app

def run_server():
    uvicorn.run(app, host='127.0.0.1', port=8001)

threading.Thread(target=run_server, daemon=True).start()

import time
time.sleep(2)

import requests
try:
    res = requests.get('http://127.0.0.1:8001/api/portfolio')
    print('STATUS:', res.status_code)
    print(res.text[:200])
except Exception as e:
    print('ERROR:', e)
