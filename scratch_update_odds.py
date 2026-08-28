import sys

with open('backend/odds_connector.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add constants
old_constants = '''BET_ID_ASIAN_HANDICAP = 3'''
new_constants = '''BET_ID_ASIAN_HANDICAP = 4
BET_ID_DRAW_NO_BET = 2
BET_ID_DOUBLE_CHANCE = 12
BET_ID_FIRST_HALF_WINNER = 13
BET_ID_FIRST_HALF_GOALS = 6'''

content = content.replace(old_constants, new_constants)

old_parse = '''        elif bet_id == BET_ID_BTTS:
            for v in values:
                val_str = str(v.get('value')).lower()
                price = float(v.get('odd', 0))
                if val_str == "yes":
                    odds['btts_yes'] = {"price": price, "bookie": bookie_name}
                elif val_str == "no":
                    odds['btts_no'] = {"price": price, "bookie": bookie_name}'''

new_parse = '''        elif bet_id == BET_ID_BTTS:
            for v in values:
                val_str = str(v.get('value')).lower()
                price = float(v.get('odd', 0))
                if val_str == "yes":
                    odds['btts_yes'] = {"price": price, "bookie": bookie_name}
                elif val_str == "no":
                    odds['btts_no'] = {"price": price, "bookie": bookie_name}
                    
        elif bet_id == BET_ID_DRAW_NO_BET:
            for v in values:
                val_str = str(v.get('value')).lower()
                price = float(v.get('odd', 0))
                if val_str == "home": odds['dnb_home'] = {"price": price, "bookie": bookie_name}
                elif val_str == "away": odds['dnb_away'] = {"price": price, "bookie": bookie_name}
                
        elif bet_id == BET_ID_DOUBLE_CHANCE:
            for v in values:
                val_str = str(v.get('value')).lower()
                price = float(v.get('odd', 0))
                if val_str == "home/draw": odds['dc_1x'] = {"price": price, "bookie": bookie_name}
                elif val_str == "draw/away": odds['dc_x2'] = {"price": price, "bookie": bookie_name}
                elif val_str == "home/away": odds['dc_12'] = {"price": price, "bookie": bookie_name}
                
        elif bet_id == BET_ID_FIRST_HALF_WINNER:
            for v in values:
                val_str = str(v.get('value')).lower()
                price = float(v.get('odd', 0))
                if val_str == "home": odds['ht_home'] = {"price": price, "bookie": bookie_name}
                elif val_str == "draw": odds['ht_draw'] = {"price": price, "bookie": bookie_name}
                elif val_str == "away": odds['ht_away'] = {"price": price, "bookie": bookie_name}
                
        elif bet_id == BET_ID_FIRST_HALF_GOALS:
            for v in values:
                val_str = str(v.get('value')).lower()
                price = float(v.get('odd', 0))
                if val_str == "over 0.5": odds['ht_over_0_5'] = {"price": price, "bookie": bookie_name}
                
        elif bet_id == BET_ID_ASIAN_HANDICAP:
            for v in values:
                val_str = str(v.get('value')).lower()
                price = float(v.get('odd', 0))
                if val_str == "home -1.5": odds['home_minus_1_5'] = {"price": price, "bookie": bookie_name}
                elif val_str == "away -1.5": odds['away_minus_1_5'] = {"price": price, "bookie": bookie_name}
                elif val_str == "home -1.0" or val_str == "home -1": odds['home_minus_1_0'] = {"price": price, "bookie": bookie_name}
                elif val_str == "away -1.0" or val_str == "away -1": odds['away_minus_1_0'] = {"price": price, "bookie": bookie_name}
                elif val_str == "home +1.5": odds['home_plus_1_5'] = {"price": price, "bookie": bookie_name}
                elif val_str == "away +1.5": odds['away_plus_1_5'] = {"price": price, "bookie": bookie_name}'''

content = content.replace(old_parse, new_parse)

with open('backend/odds_connector.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated odds_connector.py successfully")
