import sys

with open('backend/seed_ligas.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
# Regex to match ALL_TRACKED_LEAGUES = { ... }
content = re.sub(r'ALL_TRACKED_LEAGUES\s*=\s*\{.*?\}', 'ALL_TRACKED_LEAGUES = {"Championship": 40, "LaLiga Hypermotion": 141, "Serie B": 136}', content, flags=re.DOTALL)
content = content.replace("sys.path.append(os.path.dirname(__file__))", "sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))")

with open('scratch_elo_batch9.py', 'w', encoding='utf-8') as f:
    f.write(content)
