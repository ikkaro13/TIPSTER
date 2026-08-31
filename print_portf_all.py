lines = open('frontend/src/app/page.tsx', 'r', encoding='utf-8').readlines()
start = -1
for i, l in enumerate(lines):
    if "activeTab === 'portfolio' && portfolio" in l:
        start = i
        break
if start != -1:
    end = -1
    open_brackets = 0
    for i in range(start, len(lines)):
        print(lines[i], end='')
        open_brackets += lines[i].count('{') - lines[i].count('}')
        # simplistic tracking
        if i > start+10 and "activeTab ===" in lines[i]:
            break
