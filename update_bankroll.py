import requests
try:
    resp = requests.get('http://34.31.133.229:8000/api/portfolio', timeout=5)
    data = resp.json()
    print("LIVE BANKROLL:", data.get('bankroll'))
    
    current = data.get('bankroll', 0)
    new_bankroll = current + 2000
    
    update_resp = requests.post('http://34.31.133.229:8000/api/portfolio/reset', json={"new_amount": new_bankroll}, timeout=5)
    print("UPDATE STATUS:", update_resp.json())
except Exception as e:
    print("ERROR:", e)
