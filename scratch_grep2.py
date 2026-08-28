with open('frontend/src/app/page.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'setInsights(' in line:
        for j in range(max(0, i-5), min(len(lines), i+15)):
            print(lines[j].strip())
        break
