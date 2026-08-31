# -*- coding: utf-8 -*-
import os

with open('backend/analytics.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure is_shadow_market is imported
if 'from market_rules import is_shadow_market' not in content:
    content = content.replace('import math\n', 'import math\nfrom market_rules import is_shadow_market\n')

# Replace the TIER 1 loop content
old_tier1 = '''        if price <= 1.0:
            continue
            
        if p_percent > best_safe_prob and p_percent >= 55.0:'''

new_tier1 = '''        if price <= 1.0:
            continue
            
        # TAREA 2.4 - IGNORAR SHADOW MARKETS
        internal_name_map = {
            "Ganador Local": "home",
            "Empate": "draw",
            "Ganador Visita": "away",
            "Más 1.5 Goles": "over_1_5",
            "Menos 1.5 Goles": "under_1_5",
            "Más 2.5 Goles": "over_2_5",
            "Menos 2.5 Goles": "under_2_5",
            "Más 3.5 Goles": "over_3_5",
            "Menos 3.5 Goles": "under_3_5",
            "Ambos Anotan (SÍ)": "btts_yes",
            "Ambos Anotan (NO)": "btts_no"
        }
        internal_key = internal_name_map.get(name)
        if internal_key:
            # We don't have lab_stats easily accessible here, but passing None reads market_rules base thresholds
            if is_shadow_market(internal_key, None):
                continue
            
        if p_percent > best_safe_prob and p_percent >= 55.0:'''

# Fallback names without accents for matching just in case
new_tier1_alt = new_tier1.replace('Más', 'Mas').replace('SÍ', 'SI')

content = content.replace(old_tier1, new_tier1)

# Do the same for TIER 2
old_tier2 = '''        if price <= 1.0:
            continue
            
        p_decimal = p_percent / 100.0'''

new_tier2 = '''        if price <= 1.0:
            continue
            
        internal_name_map = {
            "Ganador Local": "home",
            "Empate": "draw",
            "Ganador Visita": "away",
            "Más 1.5 Goles": "over_1_5",
            "Menos 1.5 Goles": "under_1_5",
            "Más 2.5 Goles": "over_2_5",
            "Menos 2.5 Goles": "under_2_5",
            "Más 3.5 Goles": "over_3_5",
            "Menos 3.5 Goles": "under_3_5",
            "Ambos Anotan (SÍ)": "btts_yes",
            "Ambos Anotan (NO)": "btts_no"
        }
        internal_key = internal_name_map.get(name)
        if internal_key and is_shadow_market(internal_key, None):
            continue
            
        p_decimal = p_percent / 100.0'''

content = content.replace(old_tier2, new_tier2)

with open('backend/analytics.py', 'w', encoding='utf-8') as f:
    f.write(content)
