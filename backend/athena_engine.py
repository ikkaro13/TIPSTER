import math

def calculate_gpi(stats):
    """
    Calcula el Goal Pressure Index (GPI) experimental (R1.2) basado en las estadísticas en vivo.
    stats = {
        'dangerous_attacks': 0,
        'shots_on_target': 0,
        'shots_off_target': 0,
        'corners': 0,
        'possession': 50 # percentage
    }
    Devuelve un valor entre 0 y 100.
    """
    # Pesos normalizados para métricas extraíbles
    w_da = 0.35
    w_sot = 0.25
    w_s = 0.15
    w_c = 0.15
    w_p = 0.10

    # Normalización basada en promedios por minuto (ajustable)
    # Suponiendo un partido de alta presión donde un equipo llega a:
    # 80 DA, 10 SoT, 15 Tiros totales, 8 Corners, 65% Posesión
    
    da_score = min(stats.get('dangerous_attacks', 0) / 80.0, 1.0) * 100
    sot_score = min(stats.get('shots_on_target', 0) / 10.0, 1.0) * 100
    s_score = min(stats.get('shots_off_target', 0) / 15.0, 1.0) * 100
    c_score = min(stats.get('corners', 0) / 8.0, 1.0) * 100
    
    pos = stats.get('possession', 50)
    p_score = max(0, (pos - 50) / 20.0) * 100 if pos > 50 else 0
    p_score = min(p_score, 100)

    gpi = (da_score * w_da) + (sot_score * w_sot) + (s_score * w_s) + (c_score * w_c) + (p_score * w_p)
    return round(min(gpi, 100.0), 2)

def evaluate_athena_state(minute, gpi, prev_gpi=None):
    """
    Determina el estado (WATCH, VALUE CANDIDATE, WAIT) según la ventana de tiempo (R1.3, R1.4).
    """
    state = "WAIT"
    momentum = 0
    
    if prev_gpi is not None:
        momentum = gpi - prev_gpi

    # R1.7 Estados LIVE
    if minute < 8:
        state = "OBSERVATION"
    elif 8 <= minute <= 25:
        if gpi >= 60:
            if momentum > 5:
                state = "VALUE CANDIDATE" # Goal Burst Watch
            else:
                state = "WATCH"
    elif minute > 25:
        if gpi >= 75:
            state = "WATCH"
        
    return {
        "gpi": gpi,
        "momentum": round(momentum, 2),
        "state": state,
        "reading": "Alta" if gpi >= 60 else "Moderada" if gpi >= 40 else "Baja"
    }
