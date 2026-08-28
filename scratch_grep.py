with open('backend/main.py', 'r', encoding='utf-8') as f:
    for line in f:
        if 'prob' in line.lower() or 'dnb' in line.lower():
            print(line.strip())
