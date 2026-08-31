import os

with open('backend/engine/hermes.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find('h_injuries = context.get("home_injuries", 0)')
end_idx = content.find('confidence = max(0, confidence - 10)', start_idx) + len('confidence = max(0, confidence - 10)')

old_block = content[start_idx:end_idx]

new_block = '''MAX_TOTAL_PENALTY = 30 # nunca penalizar más de 30 puntos combinados
        total_penalty = 0
        h_injuries = context.get('home_injuries', 0)
        a_injuries = context.get('away_injuries', 0)
        h_reds = context.get('home_red_cards', 0)
        a_reds = context.get('away_red_cards', 0)
        
        if final_pick == home_team:
            if h_injuries >= 3:
                total_penalty += 15
            if h_reds >= 3:
                total_penalty += 10
        elif final_pick == away_team:
            if a_injuries >= 3:
                total_penalty += 15
            if a_reds >= 3:
                total_penalty += 10
                
        total_penalty = min(total_penalty, MAX_TOTAL_PENALTY)
        confidence = max(0, confidence - total_penalty)'''

if start_idx != -1:
    content = content[:start_idx] + new_block + content[end_idx:]
    with open('backend/engine/hermes.py', 'w', encoding='utf-8') as f:
        f.write(content)
else:
    print("Could not find the block to replace.")
