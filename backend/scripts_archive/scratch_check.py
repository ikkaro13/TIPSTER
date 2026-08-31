with open('backend/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'def check_edge' in line:
        print(f'Line {i+1}: {line.rstrip()}')
    if 'def scan_day_for_value_bets' in line:
        print(f'Line {i+1}: {line.rstrip()}')
