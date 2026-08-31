import math
from market_rules import is_shadow_market
import os
import joblib
from scraper import get_corners_data
from player_props import get_player_props
from engine.hermes import Hermes

# Singleton de Hermes: se instancia una sola vez al cargar el módulo
_HERMES_INSTANCE = Hermes()

CORNERS_DB = get_corners_data()
ML_MODEL_1X2 = None
ML_MODEL_OU = None
ML_MODEL_BTTS = None

MODEL_1X2_PATH = "model_1x2.pkl"
MODEL_OU_PATH = "model_ou.pkl"
MODEL_BTTS_PATH = "model_btts.pkl"

try:
    if os.path.exists(MODEL_1X2_PATH):
        ML_MODEL_1X2 = joblib.load(MODEL_1X2_PATH)
    if os.path.exists(MODEL_OU_PATH):
        ML_MODEL_OU = joblib.load(MODEL_OU_PATH)
    if os.path.exists(MODEL_BTTS_PATH):
        ML_MODEL_BTTS = joblib.load(MODEL_BTTS_PATH)
    print("[TipsterAI] Modelos Inteligentes (1X2, OU, BTTS) cargados exitosamente.")
except Exception as e:
    print(f"Error cargando modelos ML: {e}")

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

def elo_to_expected_goals(home_elo, away_elo, home_advantage_points, league_name="Unknown"):
    elo_diff = home_elo - away_elo + home_advantage_points
    win_expectancy = 1 / (1 + 10 ** (-elo_diff / 400))
    
    GOALS_BY_LEAGUE = {
        "Bundesliga": 3.1,
        "Bundesliga 1": 3.1,
        "Premier League": 2.7,
        "Serie A": 2.6,
        "Eredivisie": 3.1,
        "Ligue 1": 2.4,
        "Liga MX": 2.5,
        "La Liga": 2.6,
        "Championship": 2.5,
    }
    # Si la liga no está en el diccionario, usamos 2.6 como promedio global
    total_goals_avg = GOALS_BY_LEAGUE.get(league_name, 2.6)
    
    home_xg = total_goals_avg * win_expectancy
    away_xg = total_goals_avg * (1 - win_expectancy)
    return home_xg, away_xg

def calculate_match_probabilities(home_team, away_team, elo_db, current_minute=0, current_home_goals=0, current_away_goals=0, historical_context=None, current_corners=0, league_name="Unknown"):
    home_elo = elo_db.get(home_team, 1750)
    away_elo = elo_db.get(away_team, 1750)
    
    # Ventaja local universal: +50 ELO para cualquier equipo en casa.
    # CONCACAF (ligas más estudiadas por el sistema) mantiene +100.
    concacaf_teams = ["Mexico", "Canada", "USA", "United States"]
    home_advantage_points = 100 if home_team in concacaf_teams else 50
    
    # Fallback inicial usando Elo (Plan B base)
    home_expected_full, away_expected_full = elo_to_expected_goals(home_elo, away_elo, home_advantage_points, league_name)

    # Si tenemos contexto histórico real (Bóveda de Stats)
    if historical_context and historical_context.get("home") and historical_context.get("away"):
        home_stats = historical_context["home"]
        away_stats = historical_context["away"]
        
        h_matches = max(home_stats.get("matches_played", len(home_stats.get("form", " "))), 1)
        a_matches = max(away_stats.get("matches_played", len(away_stats.get("form", " "))), 1)
        
        # --- REGULARIZACIÓN BAYESIANA (Inspirado en v0.1) ---
        # Evita overfitting en equipos con pocos partidos (ej. recién ascendidos o inicio de temporada)
        PRIOR_MATCHES = 5.0
        GLOBAL_CS_RATE = 0.25  # Promedio global de porterías a cero
        GLOBAL_FTS_RATE = 0.25 # Promedio global de partidos sin anotar
        
        # 1. Clean Sheets Regularizado
        raw_h_cs = home_stats.get("clean_sheet_rate", home_stats.get("clean_sheets", home_stats.get("clean_sheets_total", 0)))
        raw_a_cs = away_stats.get("clean_sheet_rate", away_stats.get("clean_sheets", away_stats.get("clean_sheets_total", 0)))
        h_clean_sheet_rate = (raw_h_cs + PRIOR_MATCHES * GLOBAL_CS_RATE) / (h_matches + PRIOR_MATCHES)
        a_clean_sheet_rate = (raw_a_cs + PRIOR_MATCHES * GLOBAL_CS_RATE) / (a_matches + PRIOR_MATCHES)
        
        # 2. Failed to score Regularizado
        raw_h_fts = home_stats.get("failed_rate", home_stats.get("failed_to_score", home_stats.get("failed_to_score_total", 0)))
        raw_a_fts = away_stats.get("failed_rate", away_stats.get("failed_to_score", away_stats.get("failed_to_score_total", 0)))
        h_failed_rate = (raw_h_fts + PRIOR_MATCHES * GLOBAL_FTS_RATE) / (h_matches + PRIOR_MATCHES)
        a_failed_rate = (raw_a_fts + PRIOR_MATCHES * GLOBAL_FTS_RATE) / (a_matches + PRIOR_MATCHES)
        
        # Ajustamos los Expected Goals base de Elo
        # Si la defensa rival es un muro de 50%, corto mis goles a la mitad.
        home_expected_full = home_expected_full * (1.0 - (h_failed_rate * 0.5)) * (1.0 - (a_clean_sheet_rate * 0.5))
        away_expected_full = away_expected_full * (1.0 - (a_failed_rate * 0.5)) * (1.0 - (h_clean_sheet_rate * 0.5))
        
        # 3. Momentum (Form)
        def get_form_multiplier(form_str):
            if not form_str: return 1.0
            form_str = form_str[-5:]
            pts = form_str.count('W')*3 + form_str.count('D')*1
            max_pts = len(form_str)*3
            if max_pts == 0: return 1.0
            ratio = pts / max_pts
            return 0.85 + (ratio * 0.3) # Multiplicador entre 0.85 y 1.15
        
        home_expected_full *= get_form_multiplier(home_stats.get("form", ""))
        away_expected_full *= get_form_multiplier(away_stats.get("form", ""))
        
        # 4. Tendencias de Goles (Over/Under)
        h_over_rate = home_stats.get("over_25", 0) / h_matches
        a_over_rate = away_stats.get("over_25", 0) / a_matches
        if h_over_rate > 0.6 and a_over_rate > 0.6:
            home_expected_full *= 1.1
            away_expected_full *= 1.1
        elif h_over_rate < 0.4 and a_over_rate < 0.4:
            home_expected_full *= 0.9
            away_expected_full *= 0.9
    
    # --------------------------------------------
    # TIME DECAY (Decaimiento Temporal para En Vivo)
    # --------------------------------------------
    remaining_ratio = max(0.0, (90 - current_minute) / 90.0)
    home_expected = home_expected_full * remaining_ratio
    away_expected = away_expected_full * remaining_ratio
    
    prob_home_win = 0.0; prob_draw = 0.0; prob_away_win = 0.0
    prob_over_05 = 0.0; prob_under_05 = 0.0
    prob_over_15 = 0.0; prob_under_15 = 0.0
    prob_over_25 = 0.0; prob_under_25 = 0.0
    prob_over_35 = 0.0; prob_under_35 = 0.0
    prob_btts_yes = 0.0; prob_btts_no = 0.0
    prob_home_minus_1_5 = 0.0; prob_away_minus_1_5 = 0.0
    prob_home_minus_1_0 = 0.0; prob_away_minus_1_0 = 0.0
    prob_home_plus_1_0 = 0.0; prob_away_plus_1_0 = 0.0
    prob_home_plus_1_5 = 0.0; prob_away_plus_1_5 = 0.0
    
    prob_ht_home_win = 0.0; prob_ht_draw = 0.0; prob_ht_away_win = 0.0
    prob_ht_over_05 = 0.0; prob_ht_under_05 = 0.0
    
    prob_exact_score = {}
    
    prob_ultra_home_btts_o35 = 0.0; prob_ultra_away_btts_o35 = 0.0
    prob_ultra_draw_btts_o35 = 0.0; prob_ultra_home_to_nil_o25 = 0.0; prob_ultra_away_to_nil_o25 = 0.0
    
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
            if total_goals > 0.5: prob_over_05 += prob
            else: prob_under_05 += prob
            
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
            
            # Asian Handicap (Win by 2+, Win by 1 is push -> so we only count Win by 2+)
            # Note: For strict Kelly, a push is return of stake, but probability of WIN is what matters
            if (home_goals - away_goals) >= 2: prob_home_minus_1_0 += prob
            if (away_goals - home_goals) >= 2: prob_away_minus_1_0 += prob
            
            # Plus Handicaps (Win or Draw)
            if (home_goals - away_goals) >= -0.5: prob_home_plus_1_0 += prob # Win or Draw is green. Loss by 1 is push. So Win/Draw is the pure win prob.
            if (away_goals - home_goals) >= -0.5: prob_away_plus_1_0 += prob
            
            if (home_goals - away_goals) >= -1.5: prob_home_plus_1_5 += prob
            if (away_goals - home_goals) >= -1.5: prob_away_plus_1_5 += prob
                
            # ULTRA (Súper Parlays Dinámicos)
            if home_goals > away_goals:
                if away_goals > 0 and (home_goals + away_goals) > 3.5:
                    prob_ultra_home_btts_o35 += prob
                elif away_goals == 0 and home_goals > 2.5:
                    prob_ultra_home_to_nil_o25 += prob
            elif away_goals > home_goals:
                if home_goals > 0 and (home_goals + away_goals) > 3.5:
                    prob_ultra_away_btts_o35 += prob
                elif home_goals == 0 and away_goals > 2.5:
                    prob_ultra_away_to_nil_o25 += prob
            else:
                if home_goals > 0 and (home_goals + away_goals) > 3.5:
                    prob_ultra_draw_btts_o35 += prob

    # --------------------------------------------
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

    # Ensamblaje con IA (Random Forest) si el modelo está disponible
    is_ensembled = False
    if home_team in elo_db and away_team in elo_db:
        h_elo = elo_db[home_team]
        a_elo = elo_db[away_team]
        elo_diff = (h_elo + 50) - a_elo
        
        # Obtener Momentum desde SQLite
        try:
            import data_engine
            h_momentum = data_engine.get_team_momentum(home_team)
            a_momentum = data_engine.get_team_momentum(away_team)
        except:
            h_momentum = 0
            a_momentum = 0
            
        if ML_MODEL_1X2:
            # Predict_proba devuelve [[prob_away, prob_draw, prob_home]]
            try:
                ml_probs_1x2 = ML_MODEL_1X2.predict_proba([[h_elo, a_elo, elo_diff, h_momentum, a_momentum]])[0]
                prob_away_win = (prob_away_win * 0.5) + (ml_probs_1x2[0] * 0.5)
                prob_draw = (prob_draw * 0.5) + (ml_probs_1x2[1] * 0.5)
                prob_home_win = (prob_home_win * 0.5) + (ml_probs_1x2[2] * 0.5)
                is_ensembled = True
            except Exception as e:
                print("Error predicting 1X2:", e)
            
        if ML_MODEL_OU:
            try:
                ml_probs_ou = ML_MODEL_OU.predict_proba([[h_elo, a_elo, elo_diff, h_momentum, a_momentum]])[0]
                prob_under_25 = (prob_under_25 * 0.5) + (ml_probs_ou[0] * 0.5)
                prob_over_25 = (prob_over_25 * 0.5) + (ml_probs_ou[1] * 0.5)
            except Exception as e:
                pass
            
        if ML_MODEL_BTTS:
            try:
                ml_probs_btts = ML_MODEL_BTTS.predict_proba([[h_elo, a_elo, elo_diff, h_momentum, a_momentum]])[0]
                prob_btts_no = (prob_btts_no * 0.5) + (ml_probs_btts[0] * 0.5)
                prob_btts_yes = (prob_btts_yes * 0.5) + (ml_probs_btts[1] * 0.5)
            except Exception as e:
                pass
    
    # Normalizar para asegurar que la suma es 100%
    total = prob_home_win + prob_draw + prob_away_win
    if total == 0: total = 1.0 
    
    # Evaluar contexto con el Oráculo de Hermes (Motor de Reglas)
    ml_winner = None
    if is_ensembled and ML_MODEL_1X2:
        if ml_probs_1x2[2] > ml_probs_1x2[0] and ml_probs_1x2[2] > ml_probs_1x2[1]: ml_winner = home_team
        elif ml_probs_1x2[0] > ml_probs_1x2[2] and ml_probs_1x2[0] > ml_probs_1x2[1]: ml_winner = away_team
        else: ml_winner = "Empate"

    poisson_winner = None
    if prob_home_win > prob_away_win and prob_home_win > prob_draw: poisson_winner = home_team
    elif prob_away_win > prob_home_win and prob_away_win > prob_draw: poisson_winner = away_team
    else: poisson_winner = "Empate"

    hermes_insight = _HERMES_INSTANCE.analyze({
        'home_team': home_team,
        'away_team': away_team,
        'home_elo': elo_db.get(home_team, 1500),
        'away_elo': elo_db.get(away_team, 1500),
        'home_xg': home_expected,
        'away_xg': away_expected,
        'ml_winner': ml_winner,
        'poisson_winner': poisson_winner,
        'historical_context': historical_context
    })
    
    # --------------------------------------------
    # DATOS ALTERNATIVOS: POISSON PARA CORNERS
    # --------------------------------------------
    corners_prediction = None
    h_corners_for = CORNERS_DB.get(home_team, {}).get("for", 5.0)
    h_corners_against = CORNERS_DB.get(home_team, {}).get("against", 4.5)
    a_corners_for = CORNERS_DB.get(away_team, {}).get("for", 4.8)
    a_corners_against = CORNERS_DB.get(away_team, {}).get("against", 5.2)
    
    # Promedio cruzado
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
    
    total = prob_home_win + prob_draw + prob_away_win
    if total == 0: total = 1.0 # Prevent division by zero
    
    # Normalización correcta por familia de mercado
    total_ou25 = prob_over_25 + prob_under_25
    if total_ou25 == 0: total_ou25 = 1.0
    total_ou15 = prob_over_15 + prob_under_15
    if total_ou15 == 0: total_ou15 = 1.0
    total_ou35 = prob_over_35 + prob_under_35
    if total_ou35 == 0: total_ou35 = 1.0
    total_btts = prob_btts_yes + prob_btts_no
    if total_btts == 0: total_btts = 1.0
    
    result = {
        "home": (prob_home_win / total) * 100,
        "draw": (prob_draw / total) * 100,
        "away": (prob_away_win / total) * 100,
        "dc_1x": ((prob_home_win + prob_draw) / total) * 100,
        "dc_x2": ((prob_away_win + prob_draw) / total) * 100,
        "dc_12": ((prob_home_win + prob_away_win) / total) * 100,
        "dnb_home": (prob_home_win / (prob_home_win + prob_away_win)) * 100 if (prob_home_win + prob_away_win) > 0 else 0,
        "dnb_away": (prob_away_win / (prob_home_win + prob_away_win)) * 100 if (prob_home_win + prob_away_win) > 0 else 0,
        "over_0_5": (prob_over_05 / total) * 100,
        "under_0_5": (prob_under_05 / total) * 100,
        "over_1_5": (prob_over_15 / total_ou15) * 100,
        "under_1_5": (prob_under_15 / total_ou15) * 100,
        "over_2_5": (prob_over_25 / total_ou25) * 100,
        "under_2_5": (prob_under_25 / total_ou25) * 100,
        "over_3_5": (prob_over_35 / total_ou35) * 100,
        "under_3_5": (prob_under_35 / total_ou35) * 100,
        "btts_yes": (prob_btts_yes / total_btts) * 100,
        "btts_no": (prob_btts_no / total_btts) * 100,
        "home_minus_1_5": (prob_home_minus_1_5 / total) * 100,
        "away_minus_1_5": (prob_away_minus_1_5 / total) * 100,
        "home_minus_1_0": (prob_home_minus_1_0 / total) * 100,
        "away_minus_1_0": (prob_away_minus_1_0 / total) * 100,
        "home_plus_1_5": (prob_home_plus_1_5 / total) * 100,
        "away_plus_1_5": (prob_away_plus_1_5 / total) * 100,
        "ht_home": (prob_ht_home_win / max(1.0, prob_ht_home_win + prob_ht_draw + prob_ht_away_win)) * 100,
        "ht_draw": (prob_ht_draw / max(1.0, prob_ht_home_win + prob_ht_draw + prob_ht_away_win)) * 100,
        "ht_away": (prob_ht_away_win / max(1.0, prob_ht_home_win + prob_ht_draw + prob_ht_away_win)) * 100,
        "ht_over_0_5": (prob_ht_over_05 / max(1.0, prob_ht_over_05 + prob_ht_under_05)) * 100,
        "exact_score": best_exact_score,
        "exact_score_prob": (best_exact_score_prob / total) * 100,
        "home_xg": home_expected_full,
        "away_xg": away_expected_full
    }
    
    # --------------------------------------------
    # GOLES PRIMER TIEMPO (HT)
    # Asumimos ~45% de los goles suceden en el HT
    # --------------------------------------------
    if current_minute < 45:
        ht_remaining_ratio = max(0.0, (45 - current_minute) / 45.0)
        # xG esperado en el 1er tiempo restante
        ht_home_xg = home_expected_full * 0.45 * ht_remaining_ratio
        ht_away_xg = away_expected_full * 0.45 * ht_remaining_ratio
        
        prob_ht_over_05 = 0.0
        prob_ht_over_15 = 0.0
        
        for rem_h in range(5):
            for rem_a in range(5):
                prob = calculate_poisson(ht_home_xg, rem_h) * calculate_poisson(ht_away_xg, rem_a)
                total_ht_goals = current_home_goals + current_away_goals + rem_h + rem_a
                if total_ht_goals > 0.5: prob_ht_over_05 += prob
                if total_ht_goals > 1.5: prob_ht_over_15 += prob
                
        result["over_0_5_ht"] = prob_ht_over_05 * 100
        result["over_1_5_ht"] = prob_ht_over_15 * 100
    else:
        result["over_0_5_ht"] = 100 if (current_home_goals + current_away_goals) > 0.5 else 0
        result["over_1_5_ht"] = 100 if (current_home_goals + current_away_goals) > 1.5 else 0

    # --------------------------------------------
    # MODELO DE CORNERS EN VIVO
    # Media de corners en liga suele ser ~10. Ajustamos por poder ofensivo.
    # --------------------------------------------
    corners_base = 9.5
    # Equipos con alto xG tienden a provocar/recibir Más corners
    corner_multiplier = (home_expected_full + away_expected_full) / 2.5
    expected_corners_full = corners_base * corner_multiplier
    
    expected_corners_rem = expected_corners_full * remaining_ratio
    
    prob_over_85_corners = 0.0
    prob_over_95_corners = 0.0
    prob_over_105_corners = 0.0
    
    for rem_c in range(25):
        p_corner = calculate_poisson(expected_corners_rem, rem_c)
        total_c = current_corners + rem_c
        if total_c > 8.5: prob_over_85_corners += p_corner
        if total_c > 9.5: prob_over_95_corners += p_corner
        if total_c > 10.5: prob_over_105_corners += p_corner
        
    result["over_8_5_corners"] = prob_over_85_corners * 100
    result["over_9_5_corners"] = prob_over_95_corners * 100
    result["over_10_5_corners"] = prob_over_105_corners * 100
    
    result.update({
        "ultras": {
            "Gana Local + Ambos Anotan + Más 3.5 Goles": (prob_ultra_home_btts_o35 / total) * 100,
            "Gana Visita + Ambos Anotan + Más 3.5 Goles": (prob_ultra_away_btts_o35 / total) * 100,
            "Empate + Ambos Anotan + Más 3.5 Goles (Ej: 2-2)": (prob_ultra_draw_btts_o35 / total) * 100,
            "Gana Local sin recibir Gol + Más 2.5 Goles": (prob_ultra_home_to_nil_o25 / total) * 100,
            "Gana Visita sin recibir Gol + Más 2.5 Goles": (prob_ultra_away_to_nil_o25 / total) * 100,
        },
        "player_prop_home": get_player_props(home_team, home_expected),
        "player_prop_away": get_player_props(away_team, away_expected),
        "metrics": { "home_xg": round(home_expected, 2), "away_xg": round(away_expected, 2) },
        "is_ensembled": is_ensembled,
        "hermes": hermes_insight
    })
    
    return result

def find_value_bets(real_probs, bookmaker_odds, tuning_params=None):
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
        ("Ambos Anotan (SÍ)", real_probs["btts_yes"], bookmaker_odds.get("btts_yes", {"price": 0})),
        ("Ambos Anotan (NO)", real_probs["btts_no"], bookmaker_odds.get("btts_no", {"price": 0})),
        ("Hándicap Local -1.5", real_probs["home_minus_1_5"], bookmaker_odds.get("home_minus_1_5", {"price": 0})),
        ("Hándicap Visita -1.5", real_probs["away_minus_1_5"], bookmaker_odds.get("away_minus_1_5", {"price": 0}))
    ]
    
    # TIER 1: MAIN LINE
    best_safe_prob = 0; best_safe_pick = None; best_safe_price = 0
    best_safe_bookie = ""; best_safe_edge = 0.0; best_safe_kelly = 0.1
    for name, p_percent, odds_info in markets:
        price = odds_info.get("price", 0)
        if price <= 1.0:
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
            
        if p_percent > best_safe_prob and p_percent >= 55.0:
            best_safe_prob = p_percent
            best_safe_pick = name
            best_safe_price = price
            best_safe_bookie = odds_info.get("bookie", "Desconocida")
            
            if best_safe_price > 1.0:
                p_decimal = p_percent / 100.0
                b_decimal = 1.0 / best_safe_price
                if p_decimal > b_decimal:
                    best_safe_edge = (p_decimal - b_decimal) * 100
                    k_frac = ((p_decimal * best_safe_price) - 1.0) / (best_safe_price - 1.0)
                    best_safe_kelly = max(0.1, (k_frac * 0.25) * 100)
                else:
                    best_safe_edge = 0.0
                    best_safe_kelly = 0.1
                    
    if best_safe_pick:
        analysis["main_line"] = { 
            "pick": best_safe_pick, 
            "prob": round(best_safe_prob, 1), 
            "odds": best_safe_price,
            "edge": round(best_safe_edge, 1),
            "kelly_percent": round(best_safe_kelly, 2),
            "bookmaker": best_safe_bookie
        }

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
            
            # Apply auto-tuning edge penalty
            edge_penalty = 0.0
            if tuning_params:
                m_key = name.upper()
                # Some markets are stored differently in DB vs analytics naming, but let's try direct map
                # or just use the generic edge penalty logic from tuning_params.
                edge_penalty = tuning_params.get("markets", {}).get(m_key, {}).get("edge_penalty", 0.0) * 100
                
            required_edge = 1.0 + edge_penalty
            
            if edge_percent > best_edge and edge_percent > required_edge:
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
    ultras = real_probs.get("ultras", {})
    if ultras:
        best_u_pick = max(ultras, key=ultras.get)
        best_u_prob = ultras[best_u_pick]
        cuota_ultra = 100.0 / best_u_prob if best_u_prob > 0 else 0
        analysis["ultra"] = { "pick": best_u_pick, "prob": round(best_u_prob, 1), "fair_odds": round(cuota_ultra, 2) }
    else:
        # Fallback para caché antiguo
        uh = real_probs.get("ultra_home", 0); ua = real_probs.get("ultra_away", 0)
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




