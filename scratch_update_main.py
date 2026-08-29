with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Modificar final_bets
content = re.sub(
    r"final_bets = value_bets if len\(value_bets\) > 0 else safe_bets",
    r"final_bets = value_bets + safe_bets",
    content
)

# Agregar los chequeos de nuevos mercados justo antes de "value_bets.sort"
new_checks = '''
            if odds.get('dc_1x', {}).get('price', 0) > 1.0:
                check_edge(probs.get('dc_1x', 0), odds['dc_1x']['price'], "Double Chance 1X")
            if odds.get('dc_x2', {}).get('price', 0) > 1.0:
                check_edge(probs.get('dc_x2', 0), odds['dc_x2']['price'], "Double Chance X2")
            if odds.get('dc_12', {}).get('price', 0) > 1.0:
                check_edge(probs.get('dc_12', 0), odds['dc_12']['price'], "Double Chance 12")
            if odds.get('dnb_home', {}).get('price', 0) > 1.0:
                check_edge(probs.get('dnb_home', 0), odds['dnb_home']['price'], "Draw No Bet Home")
            if odds.get('dnb_away', {}).get('price', 0) > 1.0:
                check_edge(probs.get('dnb_away', 0), odds['dnb_away']['price'], "Draw No Bet Away")

        # Ordenar por edge descendente
'''
content = content.replace('        # Ordenar por edge descendente', new_checks)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
