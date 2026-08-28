with open('backend/engine/hermes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(115, min(140, len(lines))):
    print(f"{i+1}: {repr(lines[i])}")
