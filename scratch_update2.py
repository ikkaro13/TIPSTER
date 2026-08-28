import sys

with open('backend/analytics.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_markets = '''    markets = [
        ("Ganador Local", real_probs["home"], bookmaker_odds.get("home", {"price": 0})),
        ("Empate", real_probs["draw"], bookmaker_odds.get("draw", {"price": 0})),
        ("Ganador Visita", real_probs["away"], bookmaker_odds.get("away", {"price": 0})),
        ("Mǭs 1.5 Goles", real_probs["over_1_5"], bookmaker_odds.get("over_1_5", {"price": 0})),
        ("Menos 1.5 Goles", real_probs["under_1_5"], bookmaker_odds.get("under_1_5", {"price": 0})),
        ("Mǭs 2.5 Goles", real_probs["over_2_5"], bookmaker_odds.get("over_2_5", {"price": 0})),
        ("Menos 2.5 Goles", real_probs["under_2_5"], bookmaker_odds.get("under_2_5", {"price": 0})),
        ("Mǭs 3.5 Goles", real_probs["over_3_5"], bookmaker_odds.get("over_3_5", {"price": 0})),
        ("Menos 3.5 Goles", real_probs["under_3_5"], bookmaker_odds.get("under_3_5", {"price": 0})),
        ("Ambos Anotan (S)", real_probs["btts_yes"], bookmaker_odds.get("btts_yes", {"price": 0})),
        ("Ambos Anotan (No)", real_probs["btts_no"], bookmaker_odds.get("btts_no", {"price": 0})),
        ("Hǭndicap Local -1.5", real_probs["home_minus_1_5"], bookmaker_odds.get("home_minus_1_5", {"price": 0})),
        ("Hǭndicap Visita -1.5", real_probs["away_minus_1_5"], bookmaker_odds.get("away_minus_1_5", {"price": 0}))
    ]'''

new_markets = '''    markets = [
        ("Ganador Local", real_probs.get("home", 0), bookmaker_odds.get("home", {"price": 0})),
        ("Empate", real_probs.get("draw", 0), bookmaker_odds.get("draw", {"price": 0})),
        ("Ganador Visita", real_probs.get("away", 0), bookmaker_odds.get("away", {"price": 0})),
        
        # Nuevos: Doble Oportunidad
        ("Doble Oportunidad 1X", real_probs.get("dc_1x", 0), bookmaker_odds.get("dc_1x", {"price": 0})),
        ("Doble Oportunidad X2", real_probs.get("dc_x2", 0), bookmaker_odds.get("dc_x2", {"price": 0})),
        ("Doble Oportunidad 12", real_probs.get("dc_12", 0), bookmaker_odds.get("dc_12", {"price": 0})),
        
        # Nuevos: Empate No Accion (DNB)
        ("Empate No Acción Local", real_probs.get("dnb_home", 0), bookmaker_odds.get("dnb_home", {"price": 0})),
        ("Empate No Acción Visita", real_probs.get("dnb_away", 0), bookmaker_odds.get("dnb_away", {"price": 0})),
        
        # Goles
        ("Más 1.5 Goles", real_probs.get("over_1_5", 0), bookmaker_odds.get("over_1_5", {"price": 0})),
        ("Menos 1.5 Goles", real_probs.get("under_1_5", 0), bookmaker_odds.get("under_1_5", {"price": 0})),
        ("Más 2.5 Goles", real_probs.get("over_2_5", 0), bookmaker_odds.get("over_2_5", {"price": 0})),
        ("Menos 2.5 Goles", real_probs.get("under_2_5", 0), bookmaker_odds.get("under_2_5", {"price": 0})),
        ("Más 3.5 Goles", real_probs.get("over_3_5", 0), bookmaker_odds.get("over_3_5", {"price": 0})),
        ("Menos 3.5 Goles", real_probs.get("under_3_5", 0), bookmaker_odds.get("under_3_5", {"price": 0})),
        ("Ambos Anotan (Sí)", real_probs.get("btts_yes", 0), bookmaker_odds.get("btts_yes", {"price": 0})),
        ("Ambos Anotan (No)", real_probs.get("btts_no", 0), bookmaker_odds.get("btts_no", {"price": 0})),
        
        # Handicaps Asiaticos
        ("Hándicap Local -1.5", real_probs.get("home_minus_1_5", 0), bookmaker_odds.get("home_minus_1_5", {"price": 0})),
        ("Hándicap Visita -1.5", real_probs.get("away_minus_1_5", 0), bookmaker_odds.get("away_minus_1_5", {"price": 0})),
        ("Hándicap Local -1.0", real_probs.get("home_minus_1_0", 0), bookmaker_odds.get("home_minus_1_0", {"price": 0})),
        ("Hándicap Visita -1.0", real_probs.get("away_minus_1_0", 0), bookmaker_odds.get("away_minus_1_0", {"price": 0})),
        ("Hándicap Local +1.5", real_probs.get("home_plus_1_5", 0), bookmaker_odds.get("home_plus_1_5", {"price": 0})),
        ("Hándicap Visita +1.5", real_probs.get("away_plus_1_5", 0), bookmaker_odds.get("away_plus_1_5", {"price": 0})),
        
        # Medio Tiempo
        ("Medio Tiempo Local", real_probs.get("ht_home", 0), bookmaker_odds.get("ht_home", {"price": 0})),
        ("Medio Tiempo Empate", real_probs.get("ht_draw", 0), bookmaker_odds.get("ht_draw", {"price": 0})),
        ("Medio Tiempo Visita", real_probs.get("ht_away", 0), bookmaker_odds.get("ht_away", {"price": 0})),
        ("Medio Tiempo Más 0.5 Goles", real_probs.get("ht_over_0_5", 0), bookmaker_odds.get("ht_over_0_5", {"price": 0}))
    ]'''

content = content.replace(old_markets, new_markets)

with open('backend/analytics.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated find_value_bets in analytics.py")
