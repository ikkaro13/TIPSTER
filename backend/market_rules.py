"""
market_rules.py - FUENTE UNICA DE VERDAD
Todos los umbrales de analisis se definen aqui y son compartidos por Hermes (analisis manual ATHENA)
y Delfos (scanner automatico).

SHADOW MODE: Mercados con valor=None se calculan y guardan en DB pero NO se recomiendan al usuario,
HASTA que evaluate_shadow_reactivation confirme ROI positivo sostenido.
"""

import json
import os

MIN_EDGE_PER_MARKET = {
    "Home": 0.10,
    "Draw": 0.15,
    "Away": 0.10,
    "Double Chance 1X": 0.10,
    "Double Chance X2": 0.10,
    "Double Chance 12": 0.12,
    "Draw No Bet Home": 0.10,
    "Draw No Bet Away": 0.10,
    "Over 0.5": 0.20,
    "Over 1.5": 0.15,
    "Over 2.5": 0.20,
    "BTTS Yes": None,
    "BTTS No": None,
    "Under 2.5": None,
    "Under 1.5": None,
    "Under 0.5": None,
}

DEFAULT_MIN_EDGE = 0.12
HERMES_MIN_EDGE = 0.10
HERMES_MIN_PROB = 52.0
HERMES_MIN_ODDS = 1.60

SHADOW_REVIEW_MIN_BETS = 15
SHADOW_REACTIVATION_ROI = 5.0
SHADOW_REACTIVATION_MULTIPLIER = 1.5

TUNING_FILE = os.path.join(os.path.dirname(__file__), "tuning_params.json")

def _load_lab_stats():
    """Importa get_portfolio de forma diferida para evitar import circular."""
    try:
        from portfolio_manager import get_portfolio
        import requests
        # Preferimos leer directo del endpoint lab si está disponible,
        # pero por simplicidad aquí recalculamos desde get_portfolio.
        # Se recomienda cachear esto con TTL de 1 hora en producción.
        return None # placeholder: ver TAREA 2.2 para integración real
    except Exception:
        return None

def evaluate_shadow_reactivation(market_name: str, lab_stats: dict) -> bool:
    if MIN_EDGE_PER_MARKET.get(market_name) is not None:
        return True
    
    if not lab_stats:
        return False
        
    stats = lab_stats.get(market_name)
    if not stats or stats.get("total", 0) < SHADOW_REVIEW_MIN_BETS:
        return False
        
    return stats.get("roi", -999) >= SHADOW_REACTIVATION_ROI

def get_min_edge(market_name: str, apply_tuning: bool = True, lab_stats: dict = None):
    base = MIN_EDGE_PER_MARKET.get(market_name, DEFAULT_MIN_EDGE)
    
    if base is None:
        if lab_stats and evaluate_shadow_reactivation(market_name, lab_stats):
            base = DEFAULT_MIN_EDGE * SHADOW_REACTIVATION_MULTIPLIER
        else:
            return None
            
    if apply_tuning and os.path.exists(TUNING_FILE):
        try:
            with open(TUNING_FILE, "r", encoding="utf-8") as f:
                params = json.load(f)
                penalty = params.get("markets", {}).get(market_name.upper(), {}).get("edge_penalty", 0.0)
                return base + penalty
        except Exception:
            pass
            
    return base

def is_shadow_market(market_name: str, lab_stats: dict = None) -> bool:
    if MIN_EDGE_PER_MARKET.get(market_name) is not None:
        return False
    if lab_stats and evaluate_shadow_reactivation(market_name, lab_stats):
        return False
    return True

def get_all_active_markets(lab_stats: dict = None) -> list:
    return [m for m in MIN_EDGE_PER_MARKET if not is_shadow_market(m, lab_stats)]

def get_all_shadow_markets(lab_stats: dict = None) -> list:
    return [m for m in MIN_EDGE_PER_MARKET if is_shadow_market(m, lab_stats)]

def get_shadow_market_progress(market_name: str, lab_stats: dict) -> dict:
    """Devuelve qué tan cerca está un mercado de graduarse de shadow mode."""
    if MIN_EDGE_PER_MARKET.get(market_name) is not None:
        return {"market": market_name, "status": "active"}
        
    stats = (lab_stats or {}).get(market_name, {})
    total = stats.get("total", 0)
    roi = stats.get("roi", None)
    
    return {
        "market": market_name,
        "status": "shadow",
        "bets_recorded": total,
        "bets_needed": max(0, SHADOW_REVIEW_MIN_BETS - total),
        "current_roi": roi,
        "roi_needed": SHADOW_REACTIVATION_ROI,
        "eligible": evaluate_shadow_reactivation(market_name, lab_stats or {})
    }
