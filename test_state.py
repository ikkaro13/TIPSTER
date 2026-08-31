import json
import sqlite3

# Test the exact state I created
with open('backend/portfolio_db.json', 'w') as f:
    f.write('{"bankroll": 1000.0, "initial_bankroll": 1000.0, "bets": []}')
with open('backend/tuning_params.json', 'w') as f:
    f.write('{}')
with open('backend/alt_data.json', 'w') as f:
    f.write('{}')
open('backend/tipster.db', 'w').close()

from backend.portfolio_manager import get_portfolio
try:
    p = get_portfolio()
    print("PORTFOLIO OK:", p)
except Exception as e:
    print("PORTFOLIO ERROR:", e)
