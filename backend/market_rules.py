"""
market_rules.py - FUENTE UNICA DE VERDAD
Todos los umbrales de analisis se definen aqui y son compartidos
por Hermes (analisis manual ATHENA) y Delfos (scanner automatico).

SHADOW MODE: Mercados con valor=None se calculan y guardan en DB
pero NO se recomiendan al usuario.
"""
import json
import os

MIN_EDGE_PER_MARKET = {
    "Home":                0.10,
    "Draw":                0.15,
    "Away":                0.10,
    "Double Chance 1X":    0.10,
    "Double Chance X2":    0.10,
    "Double Chance 12":    0.12,
    "Draw No Bet Home":    0.10,
    "Draw No Bet Away":    0.10,
    "Over 0.5":            0.20,
    "Over 1.5":            0.15,
    "Over 2.5":            0.20,
    "BTTS Yes":            None,
    "BTTS No":             None,
    "Under 2.5":           None,
    "Under 1.5":           None,
    "Under 0.5":           None,
}

DEFAULT_MIN_EDGE = 0.12
HERMES_MIN_EDGE  = 0.10
HERMES_MIN_PROB  = 52.0
HERMES_MIN_ODDS  = 1.60

TUNING_FILE = os.path.join(os.path.dirname(__file__), "tuning_params.json")

def get_min_edge(market_name: str, apply_tuning: bool = True):
    base = MIN_EDGE_PER_MARKET.get(market_name, DEFAULT_MIN_EDGE)
    if base is None:
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

def is_shadow_market(market_name: str) -> bool:
    return MIN_EDGE_PER_MARKET.get(market_name) is None

def get_all_active_markets() -> list:
    return [m for m, v in MIN_EDGE_PER_MARKET.items() if v is not None]

def get_all_shadow_markets() -> list:
    return [m for m, v in MIN_EDGE_PER_MARKET.items() if v is None]
