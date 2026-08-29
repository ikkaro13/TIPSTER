with open('backend/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'def scan_day_for_value_bets' in line:
        for j in range(i+55, min(len(lines), i+150)):
            print(lines[j].rstrip())
        break
