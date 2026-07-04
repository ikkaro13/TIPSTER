import random
from analytics import calculate_match_probabilities, find_value_bets
from data_engine import get_national_elo

print("\n" + "="*50)
print("INICIANDO MOTOR DE BACKTESTING (1,000 PARTIDOS)")
print("="*50)

elo_db = get_national_elo()
equipos = list(elo_db.keys())

# Parámetros del Portafolio
bankroll_inicial = 1000.0
bankroll = bankroll_inicial
apuestas_ganadas = 0
apuestas_perdidas = 0
yield_total = 0

print(f"Capital Inicial: ${bankroll_inicial:.2f}\n")

# Simular 1000 partidos
for i in range(1000):
    if bankroll <= 0:
        print("BANCARROTA. El modelo falló.")
        break
        
    home = random.choice(equipos)
    away = random.choice(equipos)
    if home == away: continue
    
    # 1. Calcular probabilidades reales
    real_probs = calculate_match_probabilities(home, away, elo_db)
    
    # 2. Simular Cuotas de Casas de Apuestas (con un margen de error del casino del 5%)
    # Si la prob real es 60%, la cuota justa es 1.66. El casino ofrecerá 1.58.
    # Pero a veces el casino se equivoca, así que añadimos ruido.
    ruido_casino = random.uniform(-0.15, 0.15) 
    
    bookie_p_home = (real_probs["home"]/100.0) + ruido_casino
    if bookie_p_home <= 0.05: bookie_p_home = 0.05
    if bookie_p_home >= 0.95: bookie_p_home = 0.95
    bookie_odds_home = 1.0 / bookie_p_home
    
    dummy_odds = {
        "home": {"price": bookie_odds_home, "bookie": "CasinoSim"}
    }
    
    # 3. Analizar si hay una "Apuesta de Valor" (Medium Risk)
    analysis = find_value_bets(real_probs, dummy_odds)
    
    if analysis["medium_risk"]:
        edge = analysis["medium_risk"]["edge"]
        kelly = analysis["medium_risk"]["kelly_percent"] / 100.0
        
        # Apostar
        monto_apuesta = bankroll * kelly
        
        # 4. Simular el resultado del partido real
        # Usamos la probabilidad matemática real como el generador de la realidad
        resultado_real = random.random() < (real_probs["home"] / 100.0)
        
        if resultado_real: # Ganamos
            ganancia = monto_apuesta * (bookie_odds_home - 1.0)
            bankroll += ganancia
            apuestas_ganadas += 1
        else: # Perdimos
            bankroll -= monto_apuesta
            apuestas_perdidas += 1

print("="*50)
print("RESULTADOS DEL BACKTESTING")
print("="*50)
print(f"Apuestas Ganadas: {apuestas_ganadas}")
print(f"Apuestas Perdidas: {apuestas_perdidas}")
win_rate = (apuestas_ganadas / (apuestas_ganadas + apuestas_perdidas)) * 100 if (apuestas_ganadas + apuestas_perdidas) > 0 else 0
print(f"Win Rate Real: {win_rate:.1f}%")
print(f"Capital Final: ${bankroll:.2f}")
roi = ((bankroll - bankroll_inicial) / bankroll_inicial) * 100
print(f"Retorno de Inversión (ROI): {roi:.2f}%")
print("="*50 + "\n")

