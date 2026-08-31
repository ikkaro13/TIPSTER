import os
import re

with open('backend/analytics.py', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r'        if h_over_rate > 0\.6 and a_over_rate > 0\.6:\n\s*home_expected_full \*= 1\.1\n\s*away_expected_full \*= 1\.1\n\s*elif h_over_rate < 0\.4 and a_over_rate < 0\.4:\n\s*home_expected_full \*= 0\.9\n\s*away_expected_full \*= 0\.9'

new_xg_adjust = '''        # 4. Tendencias de Goles (Over/Under) - AJUSTE INDIVIDUAL PROPORCIONAL
        OFFENSIVE_BASELINE = 0.5
        OFFENSIVE_MAX_BOOST = 1.15
        OFFENSIVE_MAX_PENALTY = 0.90
        
        def offensive_multiplier(over_rate):
            if over_rate > OFFENSIVE_BASELINE:
                excess = min(over_rate - OFFENSIVE_BASELINE, 0.5)
                return 1.0 + (excess / 0.5) * (OFFENSIVE_MAX_BOOST - 1.0)
            else:
                deficit = min(OFFENSIVE_BASELINE - over_rate, 0.5)
                return 1.0 - (deficit / 0.5) * (1.0 - OFFENSIVE_MAX_PENALTY)
                
        home_expected_full *= offensive_multiplier(h_over_rate)
        away_expected_full *= offensive_multiplier(a_over_rate)'''

if re.search(pattern, content):
    content = re.sub(pattern, new_xg_adjust, content)
else:
    print("WARNING: Could not find old xG adjustment code")

with open('backend/analytics.py', 'w', encoding='utf-8') as f:
    f.write(content)
