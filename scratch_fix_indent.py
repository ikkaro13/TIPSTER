with open('backend/engine/hermes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(len(lines)):
    if 'market_map = {' in lines[i]:
        # Si tiene 16 espacios, lo pasamos a 8
        if lines[i].startswith('                market_map = {'):
            lines[i] = '        market_map = {\n'

with open('backend/engine/hermes.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
