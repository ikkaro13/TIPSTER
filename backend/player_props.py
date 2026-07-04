import random

# Diccionario de jugadores estrella por selección
# "nombre": {"prob_base_tiros": X, "prob_base_gol": Y}
PLAYER_DATABASE = {
    "Argentina": {"name": "Lionel Messi", "base_shots": 1.8, "base_goal_prob": 45},
    "France": {"name": "Kylian Mbappé", "base_shots": 2.2, "base_goal_prob": 55},
    "England": {"name": "Harry Kane", "base_shots": 1.5, "base_goal_prob": 50},
    "Brazil": {"name": "Vinícius Júnior", "base_shots": 1.4, "base_goal_prob": 35},
    "Spain": {"name": "Lamine Yamal", "base_shots": 1.2, "base_goal_prob": 25},
    "Germany": {"name": "Jamal Musiala", "base_shots": 1.3, "base_goal_prob": 30},
    "Portugal": {"name": "Cristiano Ronaldo", "base_shots": 1.9, "base_goal_prob": 42},
    "Mexico": {"name": "Santiago Giménez", "base_shots": 1.1, "base_goal_prob": 28},
    "USA": {"name": "Christian Pulisic", "base_shots": 1.2, "base_goal_prob": 26},
    "Uruguay": {"name": "Darwin Núñez", "base_shots": 1.6, "base_goal_prob": 38},
    "Colombia": {"name": "Luis Díaz", "base_shots": 1.4, "base_goal_prob": 30},
    "Netherlands": {"name": "Cody Gakpo", "base_shots": 1.3, "base_goal_prob": 32},
    "Italy": {"name": "Federico Chiesa", "base_shots": 1.2, "base_goal_prob": 25}
}

def get_player_props(team_name, team_xg):
    """
    Calcula una recomendación de apuesta de jugador basada en el xG del equipo.
    Si el equipo se espera que anote muchos goles, la probabilidad del jugador estrella sube.
    """
    if team_name not in PLAYER_DATABASE:
        return None
        
    player = PLAYER_DATABASE[team_name]
    
    # Multiplicador de rendimiento del equipo
    # Si el xG del equipo es > 1.5, el multiplicador es positivo.
    xg_multiplier = (team_xg / 1.5) 
    
    # Probabilidad de tiros a puerta
    expected_shots = player["base_shots"] * xg_multiplier
    shots_prob = min(85.0, 40.0 + (expected_shots * 15)) # Normalización a porcentaje
    
    # Probabilidad de anotar gol
    goal_prob = min(75.0, player["base_goal_prob"] * xg_multiplier)
    
    # Elegir aleatoriamente qué proponer (Tiros o Gol) para dar variedad al Dashboard
    prop_type = "shots" if random.random() > 0.4 else "goal"
    
    if prop_type == "shots":
        line = "Más de 1.5 Tiros a Puerta"
        prob = round(shots_prob, 1)
    else:
        line = "Anota en cualquier momento"
        prob = round(goal_prob, 1)
        
    fair_odds = round(100 / prob, 2)
    
    return {
        "player": player["name"],
        "pick": line,
        "prob": prob,
        "fair_odds": fair_odds
    }
