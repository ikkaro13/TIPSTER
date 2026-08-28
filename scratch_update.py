import sys

with open('backend/analytics.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ADD VARIABLES
old_vars = '    prob_home_minus_1_5 = 0.0; prob_away_minus_1_5 = 0.0\n    prob_exact_score = {}'
new_vars = '''    prob_home_minus_1_5 = 0.0; prob_away_minus_1_5 = 0.0
    prob_home_minus_1_0 = 0.0; prob_away_minus_1_0 = 0.0
    prob_home_plus_1_0 = 0.0; prob_away_plus_1_0 = 0.0
    prob_home_plus_1_5 = 0.0; prob_away_plus_1_5 = 0.0
    
    prob_ht_home_win = 0.0; prob_ht_draw = 0.0; prob_ht_away_win = 0.0
    prob_ht_over_05 = 0.0; prob_ht_under_05 = 0.0
    
    prob_exact_score = {}'''

content = content.replace(old_vars, new_vars)

# ADD ASIAN HANDICAP LOGIC
old_ah = '''            if (home_goals - away_goals) > 1.5: prob_home_minus_1_5 += prob
            if (away_goals - home_goals) > 1.5: prob_away_minus_1_5 += prob'''
new_ah = '''            if (home_goals - away_goals) > 1.5: prob_home_minus_1_5 += prob
            if (away_goals - home_goals) > 1.5: prob_away_minus_1_5 += prob
            
            # Asian Handicap (Win by 2+, Win by 1 is push -> so we only count Win by 2+)
            # Note: For strict Kelly, a push is return of stake, but probability of WIN is what matters
            if (home_goals - away_goals) >= 2: prob_home_minus_1_0 += prob
            if (away_goals - home_goals) >= 2: prob_away_minus_1_0 += prob
            
            # Plus Handicaps (Win or Draw)
            if (home_goals - away_goals) >= -0.5: prob_home_plus_1_0 += prob # Win or Draw is green. Loss by 1 is push. So Win/Draw is the pure win prob.
            if (away_goals - home_goals) >= -0.5: prob_away_plus_1_0 += prob
            
            if (home_goals - away_goals) >= -1.5: prob_home_plus_1_5 += prob
            if (away_goals - home_goals) >= -1.5: prob_away_plus_1_5 += prob'''

content = content.replace(old_ah, new_ah)

# ADD HALF TIME LOOP BEFORE ENSEMBLE
old_ensemble = '    # Ensamblaje con IA'
new_ensemble = '''    # --------------------------------------------
    # SIMULACIÓN PARALELA: MEDIO TIEMPO
    # --------------------------------------------
    home_expected_ht = home_expected_full * 0.45
    away_expected_ht = away_expected_full * 0.45
    
    for h in range(6):
        for a in range(6):
            base_prob = calculate_poisson(home_expected_ht, h) * calculate_poisson(away_expected_ht, a)
            prob = base_prob * dixon_coles_adjustment(home_expected_ht, away_expected_ht, h, a)
            
            if h > a: prob_ht_home_win += prob
            elif h == a: prob_ht_draw += prob
            else: prob_ht_away_win += prob
            
            if (h+a) > 0.5: prob_ht_over_05 += prob
            else: prob_ht_under_05 += prob

    # Ensamblaje con IA'''

content = content.replace(old_ensemble, new_ensemble)

# ADD TO RESULT DICTIONARY
old_result = '''        "btts_no": (prob_btts_no / total) * 100,
        "home_minus_1_5": (prob_home_minus_1_5 / total) * 100,
        "away_minus_1_5": (prob_away_minus_1_5 / total) * 100,'''
new_result = '''        "btts_no": (prob_btts_no / total) * 100,
        "home_minus_1_5": (prob_home_minus_1_5 / total) * 100,
        "away_minus_1_5": (prob_away_minus_1_5 / total) * 100,
        "home_minus_1_0": (prob_home_minus_1_0 / total) * 100,
        "away_minus_1_0": (prob_away_minus_1_0 / total) * 100,
        "home_plus_1_5": (prob_home_plus_1_5 / total) * 100,
        "away_plus_1_5": (prob_away_plus_1_5 / total) * 100,
        "ht_home": (prob_ht_home_win / max(1.0, prob_ht_home_win + prob_ht_draw + prob_ht_away_win)) * 100,
        "ht_draw": (prob_ht_draw / max(1.0, prob_ht_home_win + prob_ht_draw + prob_ht_away_win)) * 100,
        "ht_away": (prob_ht_away_win / max(1.0, prob_ht_home_win + prob_ht_draw + prob_ht_away_win)) * 100,
        "ht_over_0_5": (prob_ht_over_05 / max(1.0, prob_ht_over_05 + prob_ht_under_05)) * 100,'''

content = content.replace(old_result, new_result)

with open('backend/analytics.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated analytics.py successfully")
