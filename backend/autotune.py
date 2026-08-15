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
            
    # Generar modificadores
    # Por defecto, el edge requerido es 0.05 (5%)
    # Si el ROI es negativo en una muestra decente (ej. > 5 apuestas), subimos la exigencia
    
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
        
        # Base required edge is 0.05
        # If ROI < -10% and count >= 3 (lowered for testing, ideally > 10), require higher edge
        edge_penalty = 0.0
        
        if count >= 3:
            if roi < -20:
                edge_penalty = +0.03 # Require 8% edge instead of 5%
            elif roi < 0:
                edge_penalty = +0.01 # Require 6% edge
            elif roi > 20:
                edge_penalty = -0.01 # Require 4% edge (Bonificación)
                
        if edge_penalty != 0:
            modifiers["markets"][market] = {"edge_penalty": edge_penalty, "roi": round(roi, 2), "sample": count}
            
        report.append({
            "market": market,
            "roi": round(roi, 2),
            "sample_size": count,
            "edge_penalty": edge_penalty
        })
        
    # Guardar en archivo
    with open(TUNING_FILE, 'w', encoding='utf-8') as f:
        json.dump(modifiers, f, indent=4)
        
    return {
        "status": "success",
        "message": "Auto-tuning completado",
        "report": report
    }
