import json

with open('odds_dump.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for bookie in data['bookmakers']:
    if bookie['name'] == 'Bet365':
        for bet in bookie['bets']:
            if bet['id'] in [2, 4, 12, 13]:
                print(f"Bet: {bet['name']}")
                for val in bet['values'][:5]:
                    print(f"  {val['value']} -> {val['odd']}")
