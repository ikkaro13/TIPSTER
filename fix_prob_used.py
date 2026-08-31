# -*- coding: utf-8 -*-
import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r'        elif "1x" in pick_lower or "doble oportunidad \(1x\)" in pick_lower\.replace\(" ", ""\):\n\s*prob_used = snap\.get\("dc_1x", 0\)\n\s*elif "x2" in pick_lower or "doble oportunidad \(x2\)" in pick_lower\.replace\(" ", ""\):\n\s*prob_used = snap\.get\("dc_x2", 0\)', re.MULTILINE)

new_logic = '''        elif "(x2)" in pick_lower or "dc_x2" in pick_lower:
            prob_used = snap.get("dc_2x", 0)
            if prob_used == 0:
                import re as _re
                match = _re.search(r'pivote seguro:\\s*\\+?([\\d.]+)%', pick_lower)
                if match:
                    prob_used = float(match.group(1))
        elif "(1x)" in pick_lower or "dc_1x" in pick_lower:
            prob_used = snap.get("dc_1x", 0)
            if prob_used == 0:
                import re as _re
                match = _re.search(r'pivote seguro:\\s*\\+?([\\d.]+)%', pick_lower)
                if match:
                    prob_used = float(match.group(1))'''

match = pattern.search(content)
if match:
    content = content[:match.start()] + new_logic + content[match.end():]
else:
    print("Could not find prob_used logic")

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
