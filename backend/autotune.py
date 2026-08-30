import sqlite3
import os
import json

DB_FILE = os.path.join(os.path.dirname(__file__), "tipster.db")
TUNING_FILE = os.path.join(os.path.dirname(__file__), "tuning_params.json")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def run_auto_tuning():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM bets WHERE status IN ('WON', 'LOST')")
    bets = cursor.fetchall()
    conn.close()
    
    # Agrupar por mercado
    market_stats = {}
    
    for bet in bets:
        pick_str = bet['pick']
        # Extract market from "Team A vs Team B: Market"
        if ":" in pick_str:
            market = pick_str.split(":", 1)[1].strip()
        else:
            market = pick_str.strip()
            
        # Normalize market name a bit just in case
        market = market.upper()
        
        if market not in market_stats:
            market_stats[market] = {"total_staked": 0.0, "total_profit": 0.0, "count": 0, "won": 0}
            
        market_stats[market]["total_staked"] += bet['stake']
        market_stats[market]["total_profit"] += bet['profit']
        market_stats[market]["count"] += 1
        
        if bet['status'] == 'WON':
            market_stats[market]["won"] += 1
            
    # AGREGAR LÓGICA DE DELFOS PICKS
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM delfos_picks WHERE es_correcto IS NOT NULL AND es_correcto != -1")
    delfos_picks = cursor.fetchall()
    conn.close()

    for pick in delfos_picks:
        market = pick['pick'].upper()
        if market not in market_stats:
            market_stats[market] = {"total_staked": 0.0, "total_profit": 0.0, "count": 0, "won": 0}
            
        market_stats[market]["count"] += 1
        market_stats[market]["total_staked"] += 1.0 # 1u plana
        
        if pick['es_correcto'] == 1:
            market_stats[market]["won"] += 1
            market_stats[market]["total_profit"] += (pick['cuota'] - 1)
        elif pick['es_correcto'] == 0:
            market_stats[market]["total_profit"] -= 1.0

    modifiers = {
        "markets": {},
        "global_edge_modifier": 0.0
    }
    
    report = []
    
    for market, stats in market_stats.items():
        staked = stats["total_staked"]
        profit = stats["total_profit"]
        roi = (profit / staked) * 100 if staked > 0 else 0
        count = stats["count"]
        
        edge_penalty = 0.0
        
        if count >= 10:
            if roi < -20:
                edge_penalty = +0.02 
            elif roi < 0:
                edge_penalty = +0.01 
            elif roi > 20:
                edge_penalty = -0.01 
                
        if edge_penalty != 0:
            modifiers["markets"][market] = {"edge_penalty": edge_penalty, "roi": round(roi, 2), "sample": count}
            
        report.append({
            "market": market,
            "roi": round(roi, 2),
            "sample_size": count,
            "edge_penalty": edge_penalty
        })
        
    with open(TUNING_FILE, 'w', encoding='utf-8') as f:
        json.dump(modifiers, f, indent=4)
        
    return {
        "status": "success",
        "message": "Auto-tuning completado",
        "report": report
    }
