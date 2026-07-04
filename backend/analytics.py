import math
import os
import joblib
from scraper import get_corners_data
from player_props import get_player_props

CORNERS_DB = get_corners_data()
ML_MODEL = None
MODEL_PATH = "model.pkl"

if os.path.exists(MODEL_PATH):
    try:
        ML_MODEL = joblib.load(MODEL_PATH)
        print("[TipsterAI] Modelo Random Forest cargado exitosamente.")
    except Exception as e:
        print(f"Error cargando modelo ML: {e}")

def calculate_poisson(expected_goals, actual_goals):
    if expected_goals <= 0:
        return 1.0 if actual_goals == 0 else 0.0
    return ((expected_goals ** actual_goals) * math.exp(-expected_goals)) / math.factorial(actual_goals)

def dixon_coles_adjustment(lambda_, mu, x, y, rho=-0.13):
    if x == 0 and y == 0: return max(0.0, 1.0 - (lambda_ * mu * rho))
    if x == 0 and y == 1: return max(0.0, 1.0 + (lambda_ * rho))
    if x == 1 and y == 0: return max(0.0, 1.0 + (mu * rho))
    if x == 1 and y == 1: return max(0.0, 1.0 - rho)
    return 1.0

def elo_to_expected_goals(home_elo, away_elo, home_advantage_points):
    elo_diff = home_elo - away_elo + home_advantage_points
    win_expectancy = 1 / (1 + 10 ** (-elo_diff / 400))
    total_goals_avg = 2.5
    home_xg = total_goals_avg * win_expectancy
    away_xg = total_goals_avg * (1 - win_expectancy)
    return home_xg, away_xg

def calculate_match_probabilities(home_team, away_team, elo_db, current_minute=0, current_home_goals=0, current_away_goals=0):
    home_elo = elo_db.get(home_team, 1750)
    away_elo = elo_db.get(away_team, 1750)
    
    hosts = ["Mexico", "Canada", "USA", "United States"]
    home_advantage_points = 100 if home_team in hosts else 0
    
    # xG para los 90 minutos
    home_expected_full, away_expected_full = elo_to_expected_goals(home_elo, away_elo, home_advantage_points)
    
    # --------------------------------------------
    # TIME DECAY (Decaimiento Temporal para En Vivo)
    # --------------------------------------------
    remaining_ratio = max(0.0, (90 - current_minute) / 90.0)
    home_expected = home_expected_full * remaining_ratio
    away_expected = away_expected_full * remaining_ratio
    
    prob_home_win = 0.0; prob_draw = 0.0; prob_away_win = 0.0
    prob_over_15 = 0.0; prob_under_15 = 0.0
    prob_over_25 = 0.0; prob_under_25 = 0.0
    prob_over_35 = 0.0; prob_under_35 = 0.0
    prob_btts_yes = 0.0; prob_btts_no = 0.0
    prob_home_minus_1_5 = 0.0; prob_away_minus_1_5 = 0.0
    prob_ultra_home = 0.0; prob_ultra_away = 0.0
    
    best_exact_score = f"{current_home_goals} - {current_away_goals}"
    best_exact_score_prob = 0.0

    # Iteramos sobre los goles RESTANTES
    for rem_home_goals in range(7):
        for rem_away_goals in range(7):
            base_prob = calculate_poisson(home_expected, rem_home_goals) * calculate_poisson(away_expected, rem_away_goals)
            prob = base_prob * dixon_coles_adjustment(home_expected, away_expected, rem_home_goals, rem_away_goals)
            
            # Goles FINALES reales
            home_goals = current_home_goals + rem_home_goals
            away_goals = current_away_goals + rem_away_goals
            
            # Rastreador de Marcador Exacto FINAL
            if prob > best_exact_score_prob:
                best_exact_score_prob = prob
                best_exact_score = f"{home_goals} - {away_goals}"
            
            # Básicos
            if home_goals > away_goals: prob_home_win += prob
            elif home_goals == away_goals: prob_draw += prob
            else: prob_away_win += prob
            
            total_goals = home_goals + away_goals
            if total_goals > 1.5: prob_over_15 += prob
            else: prob_under_15 += prob
            
            if total_goals > 2.5: prob_over_25 += prob
            else: prob_under_25 += prob
            
            if total_goals > 3.5: prob_over_35 += prob
            else: prob_under_35 += prob
            
            if home_goals > 0 and away_goals > 0: prob_btts_yes += prob
            else: prob_btts_no += prob
                
            if (home_goals - away_goals) > 1.5: prob_home_minus_1_5 += prob
            if (away_goals - home_goals) > 1.5: prob_away_minus_1_5 += prob
                
            # ULTRA (Same Game Parlay)
            if home_goals > away_goals and away_goals > 0 and (home_goals + away_goals) > 3.5:
                prob_ultra_home += prob
            if away_goals > home_goals and home_goals > 0 and (home_goals + away_goals) > 3.5:
                prob_ultra_away += prob

    # Ensamblaje con IA (Random Forest) si el modelo está disponible
    is_ensembled = False
    if ML_MODEL and home_team in elo_db and away_team in elo_db:
        h_elo = elo_db[home_team]
        a_elo = elo_db[away_team]
        elo_diff = (h_elo + 50) - a_elo
        
        # Predict_proba devuelve [[prob_away, prob_draw, prob_home]]
        ml_probs = ML_MODEL.predict_proba([[h_elo, a_elo, elo_diff]])[0]
        
        # Mezclamos 50% Poisson / 50% Machine Learning
        prob_away_win = (prob_away_win * 0.5) + (ml_probs[0] * 0.5)
        prob_draw = (prob_draw * 0.5) + (ml_probs[1] * 0.5)
        prob_home_win = (prob_home_win * 0.5) + (ml_probs[2] * 0.5)
        is_ensembled = True
    
    # Normalizar para asegurar que la suma es 100%
    total = prob_home_win + prob_draw + prob_away_win
    if total == 0: total = 1.0 
    
    # --------------------------------------------
    # DATOS ALTERNATIVOS: POISSON PARA CORNERS
    # --------------------------------------------
    corners_prediction = None
    if home_team in CORNERS_DB and away_team in CORNERS_DB:
        h_corners_for = CORNERS_DB[home_team]["for"]
        h_corners_against = CORNERS_DB[home_team]["against"]
        a_corners_for = CORNERS_DB[away_team]["for"]
        a_corners_against = CORNERS_DB[away_team]["against"]
        
        # Promedio cruzado (Decaimiento temporal no aplica pre-match, pero si es en vivo, reducimos)
        exp_home_corners = ((h_corners_for + a_corners_against) / 2) * remaining_ratio
        exp_away_corners = ((a_corners_for + h_corners_against) / 2) * remaining_ratio
        exp_total_corners = exp_home_corners + exp_away_corners
        
        # Poisson para Corners: Probabilidad de Menos de 9.5 (0 a 9)
        prob_under_9_5 = sum(calculate_poisson(exp_total_corners, k) for k in range(10)) * 100
        prob_over_9_5 = 100 - prob_under_9_5
        
        corners_prediction = {
            "expected_total": round(exp_total_corners, 1),
            "over_9_5_prob": round(prob_over_9_5, 1),
            "under_9_5_prob": round(prob_under_9_5, 1)
        }
    
    return {
        "home": (prob_home_win / total) * 100,
        "draw": (prob_draw / total) * 100,
        "away": (prob_away_win / total) * 100,
        "over_1_5": (prob_over_15 / total) * 100,
        "under_1_5": (prob_under_15 / total) * 100,
        "over_2_5": (prob_over_25 / total) * 100,
        "under_2_5": (prob_under_25 / total) * 100,
        "over_3_5": (prob_over_35 / total) * 100,
        "under_3_5": (prob_under_35 / total) * 100,
        "btts_yes": (prob_btts_yes / total) * 100,
        "btts_no": (prob_btts_no / total) * 100,
        "home_minus_1_5": (prob_home_minus_1_5 / total) * 100,
        "away_minus_1_5": (prob_away_minus_1_5 / total) * 100,
        "exact_score": best_exact_score,
        "exact_score_prob": (best_exact_score_prob / total) * 100,
        "ultra_home": (prob_ultra_home / total) * 100,
        "ultra_away": (prob_ultra_away / total) * 100,
        "corners": corners_prediction,
        "player_prop_home": get_player_props(home_team, home_expected),
        "player_prop_away": get_player_props(away_team, away_expected),
        "metrics": { "home_xg": round(home_expected, 2), "away_xg": round(away_expected, 2) },
        "is_ensembled": is_ensembled
    }

def find_value_bets(real_probs, bookmaker_odds):
    analysis = {
        "main_line": None,
        "medium_risk": None,
        "dreamer": None,
        "ultra": None,
        "corners_alert": None,
        "player_prop": None,
        "is_ensembled": real_probs.get("is_ensembled", False)
    }
    
    markets = [
        ("Ganador Local", real_probs["home"], bookmaker_odds.get("home", {"price": 0})),
        ("Empate", real_probs["draw"], bookmaker_odds.get("draw", {"price": 0})),
        ("Ganador Visita", real_probs["away"], bookmaker_odds.get("away", {"price": 0})),
        ("Más 1.5 Goles", real_probs["over_1_5"], bookmaker_odds.get("over_1_5", {"price": 0})),
        ("Menos 1.5 Goles", real_probs["under_1_5"], bookmaker_odds.get("under_1_5", {"price": 0})),
        ("Más 2.5 Goles", real_probs["over_2_5"], bookmaker_odds.get("over_2_5", {"price": 0})),
        ("Menos 2.5 Goles", real_probs["under_2_5"], bookmaker_odds.get("under_2_5", {"price": 0})),
        ("Más 3.5 Goles", real_probs["over_3_5"], bookmaker_odds.get("over_3_5", {"price": 0})),
        ("Menos 3.5 Goles", real_probs["under_3_5"], bookmaker_odds.get("under_3_5", {"price": 0})),
        ("Ambos Anotan (Sí)", real_probs["btts_yes"], bookmaker_odds.get("btts_yes", {"price": 0})),
        ("Ambos Anotan (No)", real_probs["btts_no"], bookmaker_odds.get("btts_no", {"price": 0})),
        ("Hándicap Local -1.5", real_probs["home_minus_1_5"], bookmaker_odds.get("home_minus_1_5", {"price": 0})),
        ("Hándicap Visita -1.5", real_probs["away_minus_1_5"], bookmaker_odds.get("away_minus_1_5", {"price": 0}))
    ]
    
    # TIER 1: MAIN LINE
    best_safe_prob = 0; best_safe_pick = None; best_safe_price = 0
    for name, p_percent, odds_info in markets:
        if p_percent > best_safe_prob and p_percent >= 55.0:
            best_safe_prob = p_percent
            best_safe_pick = name
            best_safe_price = odds_info.get("price", 0)
            
    if best_safe_pick:
        analysis["main_line"] = { "pick": best_safe_pick, "prob": round(best_safe_prob, 1), "odds": best_safe_price }

    # TIER 2: MEDIUM RISK
    best_edge = 0.0; best_val_pick = None; best_val_prob = 0.0; best_val_price = 0.0; best_val_bookie = ""
    for name, my_prob_percent, odds_info in markets:
        price = odds_info.get("price", 0)
        bookie = odds_info.get("bookie", "Desconocida")
        if price <= 1.0: continue
        
        my_prob_decimal = my_prob_percent / 100.0
        bookie_prob_decimal = 1.0 / price
        
        if my_prob_decimal > bookie_prob_decimal:
            edge_percent = (my_prob_decimal - bookie_prob_decimal) * 100
            if edge_percent > best_edge and edge_percent > 1.0:
                best_edge = edge_percent; best_val_pick = name; best_val_prob = my_prob_percent; best_val_price = price; best_val_bookie = bookie
                
    if best_val_pick:
        p = best_val_prob / 100.0; b = best_val_price
        kelly_fraction = ((p * b) - 1.0) / (b - 1.0)
        safe_kelly_percent = max(0.1, (kelly_fraction * 0.25) * 100)
        analysis["medium_risk"] = { "pick": best_val_pick, "prob": round(best_val_prob, 1), "odds": best_val_price, "edge": round(best_edge, 1), "kelly_percent": round(safe_kelly_percent, 2), "bookmaker": best_val_bookie }

    # TIER 3: DREAMER
    es_prob = real_probs["exact_score_prob"]
    cuota_justa = 100.0 / es_prob if es_prob > 0 else 0
    analysis["dreamer"] = { "pick": f"Marcador {real_probs['exact_score']}", "prob": round(es_prob, 1), "fair_odds": round(cuota_justa, 2) }
    
    # TIER 4: ULTRA
    uh = real_probs["ultra_home"]; ua = real_probs["ultra_away"]
    best_u_prob = max(uh, ua)
    best_u_pick = "Gana Local + Ambos Anotan + Más 3.5 Goles" if uh > ua else "Gana Visita + Ambos Anotan + Más 3.5 Goles"
    cuota_ultra = 100.0 / best_u_prob if best_u_prob > 0 else 0
    analysis["ultra"] = { "pick": best_u_pick, "prob": round(best_u_prob, 1), "fair_odds": round(cuota_ultra, 2) }
        
    # DATOS ALTERNATIVOS (CORNERS)
    if real_probs.get("corners"):
        c = real_probs["corners"]
        if c["over_9_5_prob"] >= c["under_9_5_prob"]:
            analysis["corners_alert"] = {"pick": "Más de 9.5 Corners", "prob": c["over_9_5_prob"], "fair_odds": round(100 / c["over_9_5_prob"], 2)}
        else:
            analysis["corners_alert"] = {"pick": "Menos de 9.5 Corners", "prob": c["under_9_5_prob"], "fair_odds": round(100 / c["under_9_5_prob"], 2)}

    # DATOS ALTERNATIVOS (PLAYER PROPS)
    pp_home = real_probs.get("player_prop_home")
    pp_away = real_probs.get("player_prop_away")
    
    best_pp = None
    if pp_home and pp_away:
        best_pp = pp_home if pp_home["prob"] > pp_away["prob"] else pp_away
    elif pp_home: best_pp = pp_home
    elif pp_away: best_pp = pp_away
    
    if best_pp:
        analysis["player_prop"] = best_pp

    return analysis
