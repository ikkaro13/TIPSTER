# -*- coding: utf-8 -*-
import os

with open('backend/engine/hermes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure is_shadow_market is imported
if 'from market_rules import is_shadow_market' not in content:
    content = content.replace('from engine.rules import RuleEngine', 'from engine.rules import RuleEngine\nfrom market_rules import is_shadow_market')

# New evaluate_safe function
new_evaluate_safe = '''    def evaluate_safe(self, current_pick, confidence, context):
        odds = context.get('odds', {})
        probs = context.get('probs', {})
        home_team = context.get('home_team', 'Local')
        away_team = context.get('away_team', 'Visita')
        
        market_map = {
            f"{home_team} (Gana Local)": "home",
            "Empate": "draw",
            f"{away_team} (Gana Visita)": "away",
            "Más de 1.5 Goles": "over_1_5",
            "Menos de 3.5 Goles": "under_3_5",
            "Ambos Anotan - SÍ": "btts_yes",
            "Ambos Anotan - NO": "btts_no",
            "Menos de 2.5 Goles": "under_2_5",
            "Doble Oportunidad 1X": "dc_1x",
            "Doble Oportunidad X2": "dc_2x",
            "DNB Local": "dnb_home",
            "DNB Visita": "dnb_away",
        }
        
        lab_stats = context.get('lab_stats', None)
        valid_safe_markets = {}
        shadow_candidates = {}
        
        for market_desc, key in market_map.items():
            if key in odds and key in probs:
                try:
                    o = float(odds[key])
                    p = float(probs[key])
                except (ValueError, TypeError):
                    continue
                    
                implied_edge = (p / 100.0) * o - 1
                if implied_edge <= -0.05:
                    continue
                    
                if is_shadow_market(market_desc, lab_stats):
                    shadow_candidates[market_desc] = p
                    continue
                    
                valid_safe_markets[market_desc] = p
                
        if not valid_safe_markets:
            if shadow_candidates:
                best_shadow_desc = max(shadow_candidates, key=shadow_candidates.get)
                return f"NO BET ({best_shadow_desc} en Monitoreo, sin recomendación activa)", 0
            return "NO HAY SAFE PICK (Ningún mercado seguro >= 1.60)", 0
            
        best_safe_desc = max(valid_safe_markets, key=valid_safe_markets.get)
        best_safe_prob = valid_safe_markets[best_safe_desc]
        
        return f"{best_safe_desc} (Cuota >= 1.60)", int(best_safe_prob)
'''

# Find the start of evaluate_safe and the start of the next method
idx_start = content.find('def evaluate_safe(self, current_pick, confidence, context):')
if idx_start != -1:
    idx_end = content.find('def aggregate(self, h_xg, a_xg, probs, odds, context):', idx_start)
    if idx_end != -1:
        # Replaces evaluate_safe
        content = content[:idx_start] + new_evaluate_safe + '\n    ' + content[idx_end:]
        with open('backend/engine/hermes.py', 'w', encoding='utf-8') as f:
            f.write(content)
