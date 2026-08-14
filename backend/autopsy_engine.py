import sqlite3
import json
import os
from api_football_engine import get_fixture_details
from portfolio_manager import settle_bet

DB_FILE = os.path.join(os.path.dirname(__file__), "tipster.db")
CORPUS_FILE = os.path.join(os.path.dirname(__file__), "decision_corpus.jsonl")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def parse_bet_result(pick_str, home_goals, away_goals, home_team, away_team):
    """
    Evalúa matemáticamente si el pick se ganó o perdió dado el resultado final.
    Devuelve True (WON), False (LOST) o None (PENDING/UNKNOWN)
    """
    if home_goals is None or away_goals is None:
        return None
        
    total_goals = home_goals + away_goals
    pick_lower = pick_str.lower()
    
    # Si es Parlay, verificamos las dos condiciones asumiendo "+" como separador
    if "parlay" in pick_lower:
        # Ejemplo: "👑 PARLAY (Crear Apuesta): Doble Oport. (Local o Empate) + Más de 1.5 Goles..."
        clean_pick = pick_lower.split("):")[-1] if "):" in pick_lower else pick_lower
        clean_pick = clean_pick.split("(busca")[0]
        
        parts = clean_pick.split("+")
        if len(parts) >= 2:
            part1 = parse_bet_result(parts[0], home_goals, away_goals, home_team, away_team)
            part2 = parse_bet_result(parts[1], home_goals, away_goals, home_team, away_team)
            if part1 is not None and part2 is not None:
                return part1 and part2
            else:
                return None
                
    # 1X2 y Doble Oportunidad
    if "doble oport" in pick_lower:
        if home_team.lower() in pick_lower and "empate" in pick_lower:
            return home_goals >= away_goals
        if away_team.lower() in pick_lower and "empate" in pick_lower:
            return away_goals >= home_goals
        if "cualquiera gana" in pick_lower:
            return home_goals != away_goals
    else:
        if f"gana {home_team.lower()}" in pick_lower or "home" in pick_lower:
            return home_goals > away_goals
        if f"gana {away_team.lower()}" in pick_lower or "away" in pick_lower:
            return away_goals > home_goals
        if "empate" in pick_lower or "draw" in pick_lower:
            return home_goals == away_goals
            
    # Goles Over/Under
    if "más de 0.5" in pick_lower or "over 0.5" in pick_lower: return total_goals > 0.5
    if "más de 1.5" in pick_lower or "over 1.5" in pick_lower: return total_goals > 1.5
    if "más de 2.5" in pick_lower or "over 2.5" in pick_lower: return total_goals > 2.5
    if "más de 3.5" in pick_lower or "over 3.5" in pick_lower: return total_goals > 3.5
    
    if "menos de 1.5" in pick_lower or "under 1.5" in pick_lower: return total_goals < 1.5
    if "menos de 2.5" in pick_lower or "under 2.5" in pick_lower: return total_goals < 2.5
    if "menos de 3.5" in pick_lower or "under 3.5" in pick_lower: return total_goals < 3.5
    
    # Ambos Anotan
    if "ambos anotan" in pick_lower or "btts" in pick_lower:
        if "(sí)" in pick_lower or "yes" in pick_lower:
            return home_goals > 0 and away_goals > 0
        if "(no)" in pick_lower or " no" in pick_lower:
            return home_goals == 0 or away_goals == 0
                
    return None

def run_autopsy():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bets WHERE status = 'OPEN'")
    open_bets = cursor.fetchall()
    conn.close()
    
    resolved_count = 0
    errors = []
    
    for bet in open_bets:
        bet_id = bet['id']
        match_id = bet['match_id']
        pick = bet['pick']
        evidence_str = bet['evidence_snapshot']
        
        if str(match_id) == "-1" or str(match_id) == "mock_12345":
            continue
            
        try:
            details = get_fixture_details(match_id)
            if not details:
                continue
                
            fixture = details.get('fixture', {})
            status = fixture.get('status', {})
            short_status = status.get('short', '')
            
            if short_status in ['FT', 'AET', 'PEN']:
                goals = details.get('goals', {})
                home_goals = goals.get('home')
                away_goals = goals.get('away')
                
                teams = details.get('teams', {})
                home_team = teams.get('home', {}).get('name', '')
                away_team = teams.get('away', {}).get('name', '')
                
                is_won = parse_bet_result(pick, home_goals, away_goals, home_team, away_team)
                
                if is_won is not None:
                    new_status = 'WON' if is_won else 'LOST'
                    settle_bet(bet_id, new_status)
                    resolved_count += 1
                    
                    corpus_entry = {
                        "bet_id": bet_id,
                        "match_id": match_id,
                        "pick": pick,
                        "home_team": home_team,
                        "away_team": away_team,
                        "final_score": f"{home_goals}-{away_goals}",
                        "is_won": 1 if is_won else 0,
                        "evidence": json.loads(evidence_str) if evidence_str else {}
                    }
                    
                    with open(CORPUS_FILE, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(corpus_entry) + '\n')
                else:
                    errors.append(f"Bet {bet_id}: No se pudo parsear el pick matemáticamente: {pick}")
        except Exception as e:
            errors.append(f"Error procesando apuesta {bet_id}: {str(e)}")
                
    return {"status": "success", "resolved_count": resolved_count, "errors": errors}
