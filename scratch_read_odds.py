import json

with open('odds_dump.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for bookie in data['bookmakers']:
    if bookie['name'] in ['Bet365', '1xBet', 'Pinnacle']:
        print(f"Bookie: {bookie['name']}")
        for bet in bookie['bets']:
            print(f"  Bet ID: {bet['id']} - {bet['name']}")
        break
