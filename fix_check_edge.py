import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_def = '''def check_edge(prob_percent, odds_val, pick_name, match_probs, match_odds,
                       match_home, match_away, match_league, match_fixture_id):'''

good_def = '''        def check_edge(prob_percent, odds_val, pick_name, match_probs, match_odds,
                       match_home, match_away, match_league, match_fixture_id):'''

content = content.replace(bad_def, good_def)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
