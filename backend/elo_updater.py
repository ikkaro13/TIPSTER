from data_engine import get_national_elo, save_national_elo

def calculate_elo_change(rating1, rating2, score1, score2, k=40):
    """
    Fórmula oficial del Ranking FIFA Elo con multiplicador de diferencia de goles (G).
    """
    # Expectativa de victoria
    e1 = 1 / (1 + 10 ** ((rating2 - rating1) / 400))
    e2 = 1 / (1 + 10 ** ((rating1 - rating2) / 400))
    
    # Resultado real
    s1 = 1 if score1 > score2 else (0.5 if score1 == score2 else 0)
    s2 = 1 if score2 > score1 else (0.5 if score1 == score2 else 0)
    
    # Multiplicador de Goleada
    gd = abs(score1 - score2)
    if gd <= 1: 
        g_mult = 1
    elif gd == 2: 
        g_mult = 1.5
    else: 
        g_mult = (11 + gd) / 8
        
    # Nueva clasificación
    new_r1 = rating1 + k * g_mult * (s1 - e1)
    new_r2 = rating2 + k * g_mult * (s2 - e2)
    
    return round(new_r1), round(new_r2)

def update_match_result(home_team, away_team, home_goals, away_goals):
    """
    Ejecuta el aprendizaje del sistema actualizando la base de datos.
    """
    db = get_national_elo()
    
    # Si los equipos no existen, empezamos con el promedio 1750
    r1 = db.get(home_team, 1750)
    r2 = db.get(away_team, 1750)
    
    new_r1, new_r2 = calculate_elo_change(r1, r2, home_goals, away_goals)
    
    # Guardamos en la "Memoria"
    db[home_team] = new_r1
    db[away_team] = new_r2
    save_national_elo(db)
    
    return {
        "home": {"team": home_team, "old_elo": r1, "new_elo": new_r1, "diff": new_r1 - r1},
        "away": {"team": away_team, "old_elo": r2, "new_elo": new_r2, "diff": new_r2 - r2}
    }
