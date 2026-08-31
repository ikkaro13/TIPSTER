import re

with open('backend/engine/hermes.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_logic = '''        total_penalty = min(total_penalty, MAX_TOTAL_PENALTY)
        confidence = max(0, confidence - total_penalty)
        elif final_pick == away_team and a_reds >= 3:
            confidence = max(0, confidence - 10)'''

good_logic = '''        total_penalty = min(total_penalty, MAX_TOTAL_PENALTY)
        confidence = max(0, confidence - total_penalty)'''

content = content.replace(bad_logic, good_logic)

with open('backend/engine/hermes.py', 'w', encoding='utf-8') as f:
    f.write(content)
