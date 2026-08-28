with open('backend/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if line.startswith('def get_daily_calendar(date: str = None):'):
        start_idx = i
        break

if start_idx != -1:
    for i in range(start_idx, len(lines)):
        if 'return {"status": "error", "message": str(e), "data": []}' in lines[i]:
            end_idx = i
            break

if start_idx != -1 and end_idx != -1:
    print(f"Encontrado desde la línea {start_idx} hasta {end_idx}")
else:
    print("NO ENCONTRADO")
