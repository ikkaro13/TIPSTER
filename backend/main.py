import os
from dotenv import load_dotenv
load_dotenv()
VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() == "true"
import time
import traceback
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from analytics import calculate_match_probabilities, find_value_bets
from data_engine import get_national_elo
from elo_updater import update_match_result
from portfolio_manager import get_portfolio, place_bet, settle_bet, reopen_bet, reset_bankroll, delete_bet, update_bet_odds
from pydantic import BaseModel
from services.historical_context_service import HistoricalContextService
from engine.hermes import Hermes
from autopsy_engine import run_autopsy
from telegram_bot import send_telegram_alert
import odds_connector
import random
import sys
import athena_engine
import api_football_engine
import sofascore_scraper
from autotune import run_auto_tuning
from train_model import train_models
from market_rules import get_min_edge, is_shadow_market, get_all_shadow_markets
import json

class MatchResult(BaseModel):
    homeTeam: str
    awayTeam: str
    homeGoals: int
    awayGoals: int

class LiveMatchRequest(BaseModel):
    homeTeam: str
    awayTeam: str
    minute: int
    homeGoals: int
    awayGoals: int
    currentOdds: dict

class PrematchInsightRequest(BaseModel):
    homeTeam: str
    awayTeam: str
    match_id: str = None

class RecalculateHermesRequest(BaseModel):
    homeTeam: str
    awayTeam: str
    home_xg: float
    away_xg: float
    odds: dict
    probs: dict
    home_injuries: int = 0
    away_injuries: int = 0
    home_red_cards: int = 0
    away_red_cards: int = 0

class BetRequest(BaseModel):
    match_id: str
    pick: str
    odds: float
    stake: float
    evidence_snapshot: str = None
    bet_type: str = "PRE"

class ResetBankrollRequest(BaseModel):
    new_amount: float

class AresCalculateRequest(BaseModel):
    homeTeam: str
    awayTeam: str
    minute: int
    homeGoals: int
    awayGoals: int
    market: str
    odds: float
    currentCorners: int = 0

class SettleRequest(BaseModel):
    result: str

class UpdateOddsRequest(BaseModel):
    odds: float

class DeleteBetRequest(BaseModel):
    bet_id: str

app = FastAPI(title="Tipster API Financial Grade", version="5.0")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

API_KEY = os.getenv("API_FOOTBALL_KEY")
GLOBAL_STATS_DB = None
ODDS_CACHE = {"timestamp": 0, "data": []}
CACHE_TTL = 3600 # 1 hora de cachÃ©
ARGOS_DAEMON_ACTIVE = False

@app.post("/api/update-result")
def update_result(result: MatchResult):
    updates = update_match_result(result.homeTeam, result.awayTeam, result.homeGoals, result.awayGoals)
    global GLOBAL_STATS_DB
    GLOBAL_STATS_DB = get_national_elo()
    return {"status": "success", "updates": updates}

@app.post("/api/live-analysis")
def live_analysis(req: LiveMatchRequest):
    global GLOBAL_STATS_DB
    if not GLOBAL_STATS_DB: GLOBAL_STATS_DB = get_national_elo()
    
    real_probs = calculate_match_probabilities(
        req.homeTeam, req.awayTeam, GLOBAL_STATS_DB,
        current_minute=req.minute,
        current_home_goals=req.homeGoals,
        current_away_goals=req.awayGoals
    )
    analysis = find_value_bets(real_probs, req.currentOdds)
    return {"probs": real_probs, "analysis": analysis}

def athena_live_monitor_loop():
    """
    Vigilante en segundo plano: 
    Busca partidos en vivo, escanea mÃ©tricas, y envÃ­a alertas a Telegram sin depender de la UI.
    """
    global GLOBAL_STATS_DB
    
    print("[ATHENA-DAEMON] Vigilante autÃ³nomo iniciado en segundo plano.", flush=True)
    
    while True:
        try:
            time.sleep(60)
            
            # Si ARGOS estÃ¡ apagado desde la UI, no gastamos tokens
            if not ARGOS_DAEMON_ACTIVE:
                continue
                
            live_matches = api_football_engine.get_live_fixtures()
            if not live_matches:
                continue
                
            for match in live_matches:
                match_id = str(match.get("fixture", {}).get("id", ""))
                if not match_id: continue
                
                status_short = match.get("fixture", {}).get("status", {}).get("short", "")
                if status_short not in ["1H", "2H", "HT", "ET", "P", "LIVE"]:
                    continue
                    
                # Usar el scraper de SofaScore para sacar stats de ataque avanzados
                live_data = sofascore_scraper.get_live_stats(mock=False, match_id=match_id)
                
                # FALLBACK: Si SofaScore bloquea el servidor (403), rescatamos los minutos y goles desde API-Football
                if live_data is None:
                    fixtures = api_football_engine.get_live_fixtures()
                    target = next((f for f in fixtures if str(f.get('fixture', {}).get('id')) == str(match_id)), None)
                    if target:
                        status = target.get('fixture', {}).get('status', {})
                        minute = status.get('elapsed', 0)
                        goals = target.get('goals', {})
                        home_goals = goals.get('home', 0)
                        away_goals = goals.get('away', 0)
                        live_data = {
                            "minute": minute if minute else 0,
                            "score": f"{home_goals} - {away_goals}",
                            "stats": {
                                "dangerous_attacks": 0,
                                "shots_on_target": 0,
                                "shots_off_target": 0,
                                "corners": 0,
                                "possession": 50
                            }
                        }
                if not live_data: continue
                
                gpi = athena_engine.calculate_gpi(live_data['stats'])
                prev_gpi = gpi - 6.5 
                athena_state = athena_engine.evaluate_athena_state(
                    minute=live_data['minute'], 
                    gpi=gpi, 
                    prev_gpi=prev_gpi
                )
                
                if (gpi >= 75) or (athena_state['state'] == 'VALUE CANDIDATE'):
                    alert_id = f"{match_id}_{live_data['minute']}_{athena_state['state']}"
                    texto_apuesta = "OVER 0.5 HT o PRÃ“XIMO GOL" if live_data['minute'] < 40 else "PRÃ“XIMO GOL"
                    
                    msg = (
                        f"ðŸš¨ <b>ALERTA ATHENA LIVE</b> ðŸš¨\n\n"
                        f"Partido ID: <code>{match_id}</code>\n"
                        f"Minuto: {live_data['minute']}'\n"
                        f"<b>GPI (Goal Pressure Index):</b> {gpi}\n"
                        f"<b>Momentum:</b> {athena_state['momentum']}\n\n"
                        f"ðŸ”¥ <i>RECOMENDACIÃ“N: {texto_apuesta}. PresiÃ³n ofensiva crÃ­tica detectada.</i>"
                    )
                    send_telegram_alert(msg, alert_id)
                    
        except Exception as e:
            print(f"[ATHENA-DAEMON] Error crÃ­tico: {e}")
            time.sleep(60)


@app.on_event("startup")
def startup_event():
    global GLOBAL_STATS_DB
    GLOBAL_STATS_DB = get_national_elo()
    
    # Iniciar Daemon autÃ³nomo de ATHENA
    import threading
    daemon_thread = threading.Thread(target=athena_live_monitor_loop, daemon=True)
    daemon_thread.start()

@app.get("/")
def read_root():
    return {"message": "Financial Prediction Engine is running"}

# --- ENDPOINTS DEL PORTAFOLIO ---
@app.get("/api/portfolio")
def api_get_portfolio():
    return get_portfolio()

@app.post("/api/recalculate-hermes")
def api_recalculate_hermes(req: RecalculateHermesRequest):
    context = {
        'home_team': req.homeTeam,
        'away_team': req.awayTeam,
        'home_xg': req.home_xg,
        'away_xg': req.away_xg,
        'odds': req.odds,
        'probs': req.probs,
        'home_injuries': req.home_injuries,
        'away_injuries': req.away_injuries,
        'home_red_cards': req.home_red_cards,
        'away_red_cards': req.away_red_cards
    }
    
    h = Hermes()
    result = h.analyze(context)
    return {"hermes": result}

@app.post("/api/portfolio/bet")
def api_place_bet(req: BetRequest):
    import json
    snap_str = req.evidence_snapshot
    if not snap_str:
        print(f"[WARNING] Bet sin evidence_snapshot: {req.match_id} - {req.pick}")
    else:
        try:
            snap = json.loads(snap_str)
            if 'hermes' not in snap or 'home' not in snap:
                snap_str = ""
                print("[WARNING] evidence_snapshot invalido, marcando sin evidencia")
        except Exception:
            snap_str = ""
            print("[WARNING] evidence_snapshot corrupto, marcando sin evidencia")
            
    res = place_bet(req.match_id, req.pick, req.odds, req.stake, snap_str, req.bet_type)
    if snap_str == "":
        res['message'] = res.get('message', '') + " (WARNING: Apuesta guardada SIN evidencia analizable)"
    return res


@app.get("/api/portfolio/audit-log")
def get_audit_log(limit: int = 50):
    from portfolio_manager import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bankroll_audit_log ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"audit_log": rows}

@app.post("/api/portfolio/reset")
def api_reset_bankroll(req: ResetBankrollRequest):
    return reset_bankroll(req.new_amount)

@app.post("/api/argos/toggle")
def toggle_argos():
    global ARGOS_DAEMON_ACTIVE
    ARGOS_DAEMON_ACTIVE = not ARGOS_DAEMON_ACTIVE
    estado = "ON" if ARGOS_DAEMON_ACTIVE else "OFF"
    print(f"[ARGOS] Daemon cambiado a estado: {estado}", flush=True)
    return {"status": "success", "argos_active": ARGOS_DAEMON_ACTIVE}

@app.get("/api/argos/status")
def get_argos_status():
    return {"argos_active": ARGOS_DAEMON_ACTIVE}


@app.get("/api/delfos/diagnostic")
def delfos_diagnostic():
    from portfolio_manager import get_db_connection
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM bets')
    total = c.fetchone()[0]
    
    c.execute('SELECT status, COUNT(*) FROM bets GROUP BY status')
    status_counts = dict(c.fetchall())
    
    c.execute('SELECT COUNT(*) FROM bets WHERE evidence_snapshot IS NOT NULL AND evidence_snapshot != ""')
    has_snap = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM bets WHERE evidence_snapshot IS NULL OR evidence_snapshot = ""')
    no_snap = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM bets WHERE match_id IN ("-1", "mock_12345")')
    mock_matches = c.fetchone()[0]
    
    # Excluidos (simulamos para la UI)
    c.execute('SELECT * FROM bets WHERE match_id IN ("-1", "mock_12345") OR evidence_snapshot IS NULL OR evidence_snapshot = ""')
    excluidos = [dict(r) for r in c.fetchall()]
    conn.close()
    
    return {
        "total": total,
        "status_counts": status_counts,
        "has_snap": has_snap,
        "no_snap": no_snap,
        "mock_matches": mock_matches,
        "excluidos": excluidos
    }

@app.post("/api/autotune/run")
def trigger_auto_tuning():
    try:
                # 1. Ajustar hiperparametros
        res = run_auto_tuning()
        
        # 2. Entrenar los 3 modelos de Machine Learning (Random Forest)
        ml_res = train_models()
        if ml_res:
            res['ml_report'] = ml_res
            
        return res
    except Exception as e:
        print(f"Error in autotune: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/portfolio/settle/{bet_id}")
def settle_bet_endpoint(bet_id: str, request: SettleRequest):
    return settle_bet(bet_id, request.result)

@app.post("/api/portfolio/reopen/{bet_id}")
def reopen_bet_endpoint(bet_id: str):
    """Revierte una apuesta cerrada de vuelta a PENDIENTE (OPEN). Útil para corregir errores."""
    res = reopen_bet(bet_id)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res["message"])
    return res

@app.delete("/api/portfolio/bets/{bet_id}")
def delete_bet_endpoint(bet_id: str):
    res = delete_bet(bet_id)
    if res.get("status") == "error":
        raise HTTPException(status_code=404, detail=res["message"])
    return res


@app.get("/api/shadow/status")
def get_shadow_status():
    from market_rules import get_all_shadow_markets, get_shadow_market_progress
    lab_stats = get_cached_lab_stats()
    shadow_markets = get_all_shadow_markets(lab_stats)
    return {
        "shadow_markets": [get_shadow_market_progress(m, lab_stats) for m in shadow_markets]
    }

@app.get("/api/portfolio/lab")
def portfolio_lab():
    """
    🧬 LABORATORIO DE PATRONES
    Analiza apuestas cerradas con evidence_snapshot para descubrir patrones ganadores.
    """
    import json as _json
    from portfolio_manager import get_portfolio

    data = get_portfolio()
    bets = data.get("bets", [])
    
    # Solo apuestas cerradas con snapshot
    settled = [b for b in bets if b["status"] in ("WON", "LOST") and b.get("evidence_snapshot")]
    
    if not settled:
        return {"status": "sin_datos", "message": "No hay apuestas cerradas con datos de análisis aún.", "total_analizadas": 0}

    # ── Helpers ──────────────────────────────────────────────────────────────
    def parse_snap(b):
        try:
            return _json.loads(b["evidence_snapshot"])
        except Exception:
            return None

    def extract_market_from_pick(pick: str) -> str:
        """Infiere el mercado apostado desde el texto del pick."""
        p = pick.lower()
        if "over 2.5" in p or "m\u00e1s de 2.5" in p or "mas de 2.5" in p or "más de 2.5" in p: return "Over 2.5"
        if "under 2.5" in p or "menos de 2.5" in p: return "Under 2.5"
        if "over 1.5" in p or "m\u00e1s de 1.5" in p or "mas de 1.5" in p or "más de 1.5" in p: return "Over 1.5"
        if "under 1.5" in p or "menos de 1.5" in p: return "Under 1.5"
        if "over 0.5" in p or "m\u00e1s de 0.5" in p or "mas de 0.5" in p or "más de 0.5" in p: return "Over 0.5"
        if "btts" in p or "ambos anotan" in p: return "BTTS"
        if "(x2)" in p or "dc_x2" in p: return "Doble Oportunidad X2"
        if "(1x)" in p or "dc_1x" in p: return "Doble Oportunidad 1X"
        if "doble oportunidad" in p: return "Doble Oportunidad (Sin Especificar)"
        if "draw no bet" in p or "empate no acci" in p or "dnb" in p: return "DNB"
        if "empate" in p or "draw" in p: return "Empate"
        if "gana visita" in p or "away" in p: return "Gana Visita"
        if "pivote seguro" in p or "gana local" in p or "home" in p: return "Gana Local"
        return "Otro"

    def bucket_prob(prob):
        if prob < 50:   return "<50%"
        if prob < 60:   return "50-60%"
        if prob < 70:   return "60-70%"
        if prob < 80:   return "70-80%"
        return "≥80%"

    def bucket_avi(edge):
        if edge < 0:    return "Negativo"
        if edge < 10:   return "0-10%"
        if edge < 20:   return "10-20%"
        if edge < 30:   return "20-30%"
        return "≥30%"

    def bucket_xg(xg_total):
        if xg_total < 1.5:  return "<1.5 xG"
        if xg_total < 2.5:  return "1.5-2.5 xG"
        if xg_total < 3.5:  return "2.5-3.5 xG"
        return "≥3.5 xG"

    def bucket_confidence(conf):
        if conf < 40:   return "<40%"
        if conf < 60:   return "40-60%"
        if conf < 80:   return "60-80%"
        return "≥80%"

    def compute_stats(group):
        if not group: return None
        total = len(group)
        won = sum(1 for b in group if b["status"] == "WON")
        hit_rate = round(won / total * 100, 1)
        total_profit = sum(b.get("profit", 0) for b in group)
        total_stake = sum(b.get("stake", 0) for b in group)
        roi = round((total_profit / total_stake * 100) if total_stake > 0 else 0, 1)
        return {"total": total, "ganadas": won, "perdidas": total - won, "hit_rate": hit_rate, "roi": roi, "ganancia_neta": round(total_profit, 2)}

    # ── Build enriched records ────────────────────────────────────────────────
    records = []
    for b in settled:
        snap = parse_snap(b)
        if not snap: continue

        hermes = snap.get("hermes", {})
        metrics = snap.get("metrics", {})
        
        # Determinar la prob del mercado apostado
        pick_lower = b["pick"].lower()
        if "gana local" in pick_lower or "pivote seguro" in pick_lower:
            prob_used = snap.get("home", 0)
        elif "empate" in pick_lower:
            prob_used = snap.get("draw", 0)
        elif "gana visita" in pick_lower:
            prob_used = snap.get("away", 0)
        elif "(x2)" in pick_lower or "dc_x2" in pick_lower:
            prob_used = snap.get("dc_2x", 0)
            if prob_used == 0:
                import re as _re
                match = _re.search(r'pivote seguro:\s*\+?([\d.]+)%', pick_lower)
                if match:
                    prob_used = float(match.group(1))
        elif "(1x)" in pick_lower or "dc_1x" in pick_lower:
            prob_used = snap.get("dc_1x", 0)
            if prob_used == 0:
                import re as _re
                match = _re.search(r'pivote seguro:\s*\+?([\d.]+)%', pick_lower)
                if match:
                    prob_used = float(match.group(1))
        elif "over 1.5" in pick_lower or "más de 1.5" in pick_lower:
            prob_used = snap.get("over_1_5", 0)
        elif "over 2.5" in pick_lower or "más de 2.5" in pick_lower:
            prob_used = snap.get("over_2_5", 0)
        elif "btts" in pick_lower or "ambos anotan" in pick_lower:
            prob_used = snap.get("btts_yes", 0)
        else:
            prob_used = snap.get("home", 0)

        # AVI (Edge) calculado con la cuota real que el usuario usó
        odds = b.get("odds", 1.0)
        avi = round(((prob_used / 100.0) * odds - 1) * 100, 2)

        xg_total = snap.get("home_xg", metrics.get("home_xg", 0)) + snap.get("away_xg", metrics.get("away_xg", 0))
        hermes_confidence = hermes.get("confidence", 0)

        records.append({
            "bet": b,
            "snap": snap,
            "prob": prob_used,
            "avi": avi,
            "xg_total": xg_total,
            "hermes_confidence": hermes_confidence,
            "market": extract_market_from_pick(b["pick"]),
            "prob_bucket": bucket_prob(prob_used),
            "avi_bucket": bucket_avi(avi),
            "xg_bucket": bucket_xg(xg_total),
            "conf_bucket": bucket_confidence(hermes_confidence),
        })

    if not records:
        return {"status": "sin_datos", "message": "Los snapshots no pudieron procesarse.", "total_analizadas": 0}

    # ── Analysis by dimensions ────────────────────────────────────────────────
    from collections import defaultdict

    def group_by(records, key_fn):
        groups = defaultdict(list)
        for r in records:
            groups[key_fn(r)].append(r["bet"])
        return {k: compute_stats(v) for k, v in groups.items()}

    prob_analysis = group_by(records, lambda r: r["prob_bucket"])
    avi_analysis  = group_by(records, lambda r: r["avi_bucket"])
    market_analysis = group_by(records, lambda r: r["market"])
    xg_analysis   = group_by(records, lambda r: r["xg_bucket"])
    conf_analysis = group_by(records, lambda r: r["conf_bucket"])

    # ── Golden Pattern: find the combo with best ROI (min 5 bets) ────────────
    combo_groups = defaultdict(list)
    for r in records:
        key = f"Prob {r['prob_bucket']} + AVI {r['avi_bucket']}"
        combo_groups[key].append(r["bet"])
    
    patron_dorado = None
    best_roi = -999
    for combo_key, combo_bets in combo_groups.items():
        if len(combo_bets) >= 3:  # mínimo 3 apuestas para ser relevante
            stats = compute_stats(combo_bets)
            if stats and stats["roi"] > best_roi:
                best_roi = stats["roi"]
                patron_dorado = {"descripcion": combo_key, **stats}

    # ── Best and worst markets ────────────────────────────────────────────────
    mercados_ordenados = sorted(
        [(m, s) for m, s in market_analysis.items() if s and s["total"] >= 2],
        key=lambda x: x[1]["roi"], reverse=True
    )

    return {
        "status": "ok",
        "total_analizadas": len(records),
        "resumen": compute_stats([r["bet"] for r in records]),
        "por_probabilidad": prob_analysis,
        "por_avi": avi_analysis,
        "por_mercado": market_analysis,
        "por_xg_total": xg_analysis,
        "por_confianza_hermes": conf_analysis,
        "mejor_mercado": mercados_ordenados[0][0] if mercados_ordenados else None,
        "peor_mercado": mercados_ordenados[-1][0] if mercados_ordenados else None,
        "patron_dorado": patron_dorado,
    }


@app.put("/api/portfolio/bets/{bet_id}/odds")
def update_bet_odds_endpoint(bet_id: str, request: UpdateOddsRequest):
    res = update_bet_odds(bet_id, request.odds)
    if res.get("status") == "error":
        raise HTTPException(status_code=404, detail=res["message"])
    return res

@app.post("/api/portfolio/autopsy")
def execute_autopsy():
    res = run_autopsy()
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=str(res.get("errors")))
    return res

@app.post("/api/portfolio/delete")
def api_delete_bet(req: DeleteBetRequest):
    return delete_bet(req.bet_id)

@app.get("/api/athena-live/{match_id}")
def get_athena_live_data(match_id: str):
    # Usando el Scraper para alta frecuencia
    is_mock = (match_id == "mock_12345")
    
    live_data = sofascore_scraper.get_live_stats(mock=is_mock, match_id=match_id)
    
    # FALLBACK: Si SofaScore bloquea el servidor (403), rescatamos los minutos y goles desde API-Football
    if live_data is None:
        fixtures = api_football_engine.get_live_fixtures()
        target = next((f for f in fixtures if str(f.get('fixture', {}).get('id')) == str(match_id)), None)
        if target:
            status = target.get('fixture', {}).get('status', {})
            minute = status.get('elapsed', 0)
            goals = target.get('goals', {})
            home_goals = goals.get('home', 0)
            away_goals = goals.get('away', 0)
            live_data = {
                "minute": minute if minute else 0,
                "score": f"{home_goals} - {away_goals}",
                "stats": {
                    "dangerous_attacks": 0,
                    "shots_on_target": 0,
                    "shots_off_target": 0,
                    "corners": 0,
                    "possession": 50
                }
            }
            
    if not live_data:
        return {
            "match_id": match_id,
            "live_data": None,
            "athena": {
                "state": "NO DATA",
                "gpi": 0,
                "reading": "Sin cobertura en SofaScore",
                "momentum": 0
            }
        }
        
    gpi = athena_engine.calculate_gpi(live_data['stats'])
    prev_gpi = gpi - 6.5 
    athena_state = athena_engine.evaluate_athena_state(
        minute=live_data['minute'], 
        gpi=gpi, 
        prev_gpi=prev_gpi
    )
    
    # Evaluar Inminencia de Gol
    xg_live = live_data.get('xg_live', 0)
    
    # Solo dispara por GPI alto o estado de candidato, no por simple acumulaciÃ³n lenta de xG
    athena_state['goal_alert'] = (gpi >= 75) or (athena_state['state'] == 'VALUE CANDIDATE')
    
    # [Aviso] Las alertas de Telegram ahora son gestionadas por el daemon autÃ³nomo en segundo plano.
    
    return {
        "match_id": match_id,
        "live_data": live_data,
        "athena": athena_state
    }
# --------------------------------

def update_best_odd(odds_dict, key, outcome_price, bookie_name):
    """ FunciÃ³n auxiliar para encontrar la mejor cuota entre TODAS las casas de apuestas """
    if outcome_price > odds_dict[key]["price"]:
        odds_dict[key] = {"price": outcome_price, "bookie": bookie_name}

@app.get("/api/matches")
def get_matches():
    global GLOBAL_STATS_DB
    if not GLOBAL_STATS_DB: GLOBAL_STATS_DB = get_national_elo()
        
    try:
        data = api_football_engine.get_live_fixtures()
        processed_matches = []
        
        mx_tz = timezone(timedelta(hours=-6))
        
        # [OPTIMIZACIÃ“N DE TOKENS]
        # Cargar cuotas del dÃ­a de forma masiva para evitar N+1 requests
        import odds_connector
        current_date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        if not hasattr(get_matches, "bulk_odds_cache"):
            get_matches.bulk_odds_cache = {"date": "", "timestamp": 0, "data": {}}
            
        if get_matches.bulk_odds_cache["date"] != current_date_str or (time.time() - get_matches.bulk_odds_cache["timestamp"]) > 900: # CachÃ© de 15 min
            print("[ARGOS] Obteniendo bulk odds para ahorrar tokens...")
            bulk_data = odds_connector.fetch_odds_by_date(current_date_str)
            if bulk_data:
                get_matches.bulk_odds_cache = {"date": current_date_str, "timestamp": time.time(), "data": bulk_data}
                
        daily_odds = get_matches.bulk_odds_cache.get("data", {})
        
        for match in data:
            fixture = match.get("fixture", {})
            teams = match.get("teams", {})
            status = fixture.get("status", {})
            
            home_team = teams.get("home", {}).get("name", "Unknown Home")
            away_team = teams.get("away", {}).get("name", "Unknown Away")
            
            fixture_id = str(fixture.get("id"))
            
            dt_str = fixture.get("date")
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00')) if dt_str else datetime.now(timezone.utc)
            dt_mx = dt.astimezone(mx_tz)
            
            # Smart Money Tracker Logic (Time Decay Odds Analysis)
            smart_money = False
            
            # En un entorno de producciÃ³n, aquÃ­ leerÃ­amos el historial de cuotas 
            # desde la DB o CachÃ© y lo compararÃ­amos con las cuotas actuales.
            # Como la API gratuita restringe las peticiones, usamos una simulaciÃ³n
            # de caÃ­da de cuotas institucional (>10% drop).
            if fixture_id == "mock_12345":
                # Simulamos que un 30% del tiempo detectamos una caÃ­da brusca
                if random.random() < 0.3:
                    smart_money = True
                    print("[ATHENA] ðŸš¨ ALERTA INSTITUCIONAL: Dinero Inteligente Detectado en Mock Match")
            
            # Arbitrage (Surebet) Detection Logic
            arbitrage_alert = {"active": False, "roi_percent": 0.0}
            
            # Usar la cachÃ© masiva en lugar de pegarle a la API individualmente por cada partido en vivo
            odds_data = daily_odds.get(fixture_id, {})
            # Load tuning params if exists
            tuning_params = None
            tuning_file = os.path.join(os.path.dirname(__file__), "tuning_params.json")
            if os.path.exists(tuning_file):
                try:
                    with open(tuning_file, 'r', encoding='utf-8') as f:
                        tuning_params = json.load(f)
                except:
                    pass
            
            real_probs = calculate_match_probabilities(home_team, away_team, GLOBAL_STATS_DB)
            analysis = find_value_bets(real_probs, odds_data, tuning_params)
            
            minute = status.get("elapsed", "-")
            if minute is None: minute = "-"
            
            goals = match.get('goals', {})
            goals_home = goals.get('home')
            goals_away = goals.get('away')
            if goals_home is None: goals_home = 0
            if goals_away is None: goals_away = 0
            score_str = f"{goals_home} - {goals_away}"
            
            processed_matches.append({
                "id": fixture_id,
                "league": match.get("league", {}).get("name", "API-Football League"),
                "homeTeam": home_team,
                "awayTeam": away_team,
                "startTime": dt_mx.strftime("%d/%m %H:%M"),
                "status": "LIVE" if status.get("short") in ["1H", "2H", "HT", "ET", "P"] else "UPCOMING",
                "score": score_str,
                "minute": minute,
                "smart_money_alert": smart_money,
                "arbitrage_alert": arbitrage_alert,
                "odds": odds_data,
                "analysis": analysis
            })
            
        if len(processed_matches) == 0:
            print("Inyectando partido simulado de ATHENA LIVE (Cuenca vs Manta)")
            processed_matches.append({
                "id": "mock_12345",
                "league": "Liga Pro Ecuador (SimulaciÃ³n ATHENA)",
                "homeTeam": "Deportivo Cuenca",
                "awayTeam": "Manta FC",
                "startTime": "AHORA",
                "status": "LIVE",
                "score": "0 - 0",
                "minute": "13",
                "smart_money_alert": random.random() < 0.5 if 'random' in sys.modules else True,
                "arbitrage_alert": {"active": False, "roi_percent": 0.0},
                "odds": {
                    "home": {"price": 2.50, "bookie": "API-Football"}, "draw": {"price": 3.10, "bookie": "API-Football"}, "away": {"price": 2.90, "bookie": "API-Football"},
                    "over_1_5": {"price": 1.40, "bookie": "API-Football"}, "under_1_5": {"price": 2.80, "bookie": "API-Football"},
                    "over_2_5": {"price": 2.10, "bookie": "API-Football"}, "under_2_5": {"price": 1.70, "bookie": "API-Football"},
                    "over_3_5": {"price": 3.50, "bookie": "API-Football"}, "under_3_5": {"price": 1.25, "bookie": "API-Football"},
                    "btts_yes": {"price": 1.80, "bookie": "API-Football"}, "btts_no": {"price": 1.95, "bookie": "API-Football"},
                    "home_minus_1_5": {"price": 5.00, "bookie": "API-Football"}, "away_minus_1_5": {"price": 6.00, "bookie": "API-Football"}
                },
                "analysis": {
                    "main_line": {"pick": "Over 1.5 Goles", "prob": 75, "odds": 1.40},
                    "medium_risk": {"pick": "Over 2.5 Goles", "prob": 55, "odds": 2.10, "edge": 5, "kelly_percent": 2.5, "bookmaker": "API-Football"},
                    "dreamer": None,
                    "ultra": None
                }
            })
            
        return processed_matches
    except Exception as e:
        print(f"Excepcion de conexiÃ³n: {e}")
        traceback.print_exc()
        return []

@app.get("/api/calendar")
def get_daily_calendar(date: str = None):
    try:
        mx_tz = timezone(timedelta(hours=-6))
        
        if date:
            query_date = date
        else:
            query_date = datetime.now(mx_tz).strftime("%Y-%m-%d")
            
        data = api_football_engine.get_daily_fixtures(query_date, timezone_str="America/Mexico_City")
        
        calendar_matches = []
        if data:
            for match in data:
                fixture = match.get("fixture", {})
                teams = match.get("teams", {})
                league = match.get("league", {})
                
                dt_str = fixture.get("date")
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00')) if dt_str else datetime.now(timezone.utc)
                dt_mx = dt.astimezone(mx_tz)
                
                calendar_matches.append({
                    "id": str(fixture.get("id")),
                    "league": league.get("name", "API-Football League"),
                    "country": league.get("country", "Unknown"),
                    "round": league.get("round", ""),
                    "homeTeam": teams.get("home", {}).get("name", "Unknown"),
                    "awayTeam": teams.get("away", {}).get("name", "Unknown"),
                    "startTime": dt_mx.strftime("%H:%M"),
                    "status": fixture.get("status", {}).get("long", ""),
                    "timestamp": fixture.get("timestamp", 0)
                })
        
        debug_msg = ""
        fallback_used = False
        if len(calendar_matches) == 0:
            fallback_used = True

        # 2. RESPALDO: THE-ODDS-API
        if len(calendar_matches) == 0:
            import requests
            theodds_key = os.getenv("THE_ODDS_API_KEY")
            fallback_leagues = ['soccer_mexico_ligamx', 'soccer_usa_mls', 'soccer_epl', 'soccer_spain_la_liga', 'soccer_italy_serie_a']
            
            for lg in fallback_leagues:
                url = f"https://api.the-odds-api.com/v4/sports/{lg}/odds/?apiKey={theodds_key}&regions=us&markets=h2h"
                try:
                    res = requests.get(url, verify=VERIFY_SSL, timeout=7)
                    if res.status_code == 200:
                        odds_data = res.json()
                        for g in odds_data:
                            dt = datetime.fromisoformat(g['commence_time'].replace('Z', '+00:00'))
                            dt_mx = dt.astimezone(mx_tz)
                            if dt_mx.strftime("%Y-%m-%d") != query_date:
                                continue
                            calendar_matches.append({
                                "id": g.get("id", "fallback_id"),
                                "league": lg.replace("soccer_", "").replace("_", " ").title(),
                                "country": "TheOddsAPI",
                                "round": "Regular",
                                "homeTeam": g.get('home_team', ''),
                                "awayTeam": g.get('away_team', ''),
                                "startTime": dt_mx.strftime("%H:%M"),
                                "status": "Not Started",
                                "timestamp": int(dt.timestamp())
                            })
                    else:
                        debug_msg += f"OddsAPI HTTP {res.status_code}. "
                except Exception as e:
                    debug_msg += f"OddsAPI Err. "
        
        # 3. RESPALDO: FOOTBALL-DATA
        if fallback_used:
            fd_key = os.getenv("FOOTBALL_DATA_KEY")
            url = f"https://api.football-data.org/v4/matches?dateFrom={query_date}&dateTo={query_date}"
            try:
                res = requests.get(url, headers={'X-Auth-Token': fd_key}, verify=VERIFY_SSL, timeout=7)
                if res.status_code == 200:
                    fd_data = res.json().get('matches', [])
                    for m in fd_data:
                        dt_str = m.get('utcDate')
                        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00')) if dt_str else datetime.now(timezone.utc)
                        dt_mx = dt.astimezone(mx_tz)
                        calendar_matches.append({
                            "id": str(m.get("id", "fd_id")),
                            "league": m.get('competition', {}).get('name', 'Football-Data League'),
                            "country": m.get('area', {}).get('name', 'Football-Data'),
                            "round": "Regular",
                            "homeTeam": m.get('homeTeam', {}).get('name', ''),
                            "awayTeam": m.get('awayTeam', {}).get('name', ''),
                            "startTime": dt_mx.strftime("%H:%M"),
                            "status": m.get('status', 'Not Started'),
                            "timestamp": int(dt.timestamp())
                        })
                else:
                    debug_msg += f"FD HTTP {res.status_code}. "
            except Exception as e:
                debug_msg += f"FD Err. "

        calendar_matches.sort(key=lambda x: (x.get("country", ""), x["timestamp"]))
        
        if len(calendar_matches) == 0:
            calendar_matches.append({
                "id": "mock_12345",
                "league": "DEBUG: " + (debug_msg if debug_msg else "Sin errores aparentes pero 0 partidos en las 3 APIs"),
                "round": "Final",
                "homeTeam": "Google Cloud",
                "awayTeam": "Bloqueó las APIs?",
                "startTime": "20:00",
                "status": "Not Started",
                "timestamp": 9999999999
            })
            
        return calendar_matches
    except Exception as e:
        print(f"Error en calendario: {e}")
        return []

@app.post("/api/ares/calculate")
def calculate_ares(req: AresCalculateRequest):
    global GLOBAL_STATS_DB
    if not GLOBAL_STATS_DB: 
        GLOBAL_STATS_DB = get_national_elo()
        
    # Cargar BÃ³veda HÃ­brida
    stats_db = {}
    stats_file = os.path.join(os.path.dirname(__file__), "team_stats_db.json")
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats_db = json.load(f)
        except:
            pass
            
    # Buscar IDs por nombre
    h_stats = None
    a_stats = None
    for tid, tdata in stats_db.items():
        if tdata.get("name") == req.homeTeam:
            h_stats = tdata
        if tdata.get("name") == req.awayTeam:
            a_stats = tdata
            
    h_ctx = None
    if h_stats and a_stats:
        h_ctx = {
            "home": h_stats,
            "away": a_stats
        }
        
    probs = calculate_match_probabilities(
        req.homeTeam, 
        req.awayTeam, 
        GLOBAL_STATS_DB, 
        current_minute=req.minute, 
        current_home_goals=req.homeGoals, 
        current_away_goals=req.awayGoals,
        historical_context=h_ctx,
        current_corners=req.currentCorners
    )
    
    market_map = {
        "home": probs.get("home", 0),
        "draw": probs.get("draw", 0),
        "away": probs.get("away", 0),
        "over_0_5": probs.get("over_0_5", 0),
        "under_0_5": probs.get("under_0_5", 0),
        "over_1_5": probs.get("over_1_5", 0),
        "under_1_5": probs.get("under_1_5", 0),
        "over_2_5": probs.get("over_2_5", 0),
        "under_2_5": probs.get("under_2_5", 0),
        "over_3_5": probs.get("over_3_5", 0),
        "under_3_5": probs.get("under_3_5", 0),
        "over_0_5_ht": probs.get("over_0_5_ht", 0),
        "over_1_5_ht": probs.get("over_1_5_ht", 0),
        "btts_yes": probs.get("btts_yes", 0),
        "btts_no": probs.get("btts_no", 0),
        "over_8_5_corners": probs.get("over_8_5_corners", 0),
        "over_9_5_corners": probs.get("over_9_5_corners", 0),
        "over_10_5_corners": probs.get("over_10_5_corners", 0)
    }
    
    real_prob_percent = market_map.get(req.market, 0)
    real_prob_decimal = real_prob_percent / 100.0
    
    edge = 0.0
    if req.odds > 1.0:
        edge = (real_prob_decimal * req.odds) - 1.0
        
    return {
        "status": "success",
        "market": req.market,
        "prob": round(real_prob_percent, 2),
        "odds": req.odds,
        "edge": round(edge * 100, 2),
        "is_value": edge > 0.05
    }

@app.get("/api/chronos/scan-day")
def scan_day_for_value_bets(date: str):
    global GLOBAL_STATS_DB
    if not GLOBAL_STATS_DB: 
        GLOBAL_STATS_DB = get_national_elo()

    # ── Umbrales provienen de market_rules.py (fuente única de verdad) ────────
    # Para ajustar umbrales o activar/desactivar mercados, editar market_rules.py

    try:
        # 1. Obtener todos los partidos del día
        fixtures = api_football_engine.get_daily_fixtures(date, timezone_str="America/Mexico_City")
        if not fixtures:
            return {"status": "success", "date": date, "value_bets": []}
            
        # 2. Extraer cuotas globales
        daily_odds = odds_connector.fetch_odds_by_date(date)
        
        value_bets = []
        safe_bets = []
        
        # Cargar Boveda de Estadísticas (Motor Hibrido)
        stats_db = {}
        stats_file = os.path.join(os.path.dirname(__file__), "team_stats_db.json")
        if os.path.exists(stats_file):
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats_db = json.load(f)
            except:
                pass

        # ── check_edge: definida FUERA del loop para eficiencia ────────────
        
        _LAB_STATS_CACHE = {"data": None, "timestamp": 0}
        LAB_CACHE_TTL = 3600 # 1 hora

        def get_cached_lab_stats():
            import time
            now = time.time()
            if _LAB_STATS_CACHE["data"] is None or (now - _LAB_STATS_CACHE["timestamp"]) > LAB_CACHE_TTL:
                result = portfolio_lab()
                _LAB_STATS_CACHE["data"] = result.get("por_mercado", {})
                _LAB_STATS_CACHE["timestamp"] = now
            return _LAB_STATS_CACHE["data"]


        def check_edge(prob_percent, odds_val, pick_name, match_probs, match_odds,
                       match_home, match_away, match_league, match_fixture_id):
            from data_engine import save_delfos_pick
            import json as _json
            prob = prob_percent / 100.0
            edge = (prob * odds_val) - 1

            # Umbral desde market_rules (incluye penalización de tuning)
            required_edge = get_min_edge(pick_name, apply_tuning=True)

            # Shadow Mode: calcular, guardar en DB, NO recomendar
            if required_edge is None:
                if edge > 0.05 and prob_percent >= 50.0:  # Solo guardar si hay algo de edge
                    save_delfos_pick(
                        fixture_id=match_fixture_id,
                        home_team=match_home,
                        away_team=match_away,
                        liga=match_league,
                        pick=pick_name,
                        probabilidad=round(prob_percent, 2),
                        cuota=odds_val,
                        edge=round(edge * 100, 2),
                        tipo="🔬 Shadow (Monitoreo)",
                        evidence_snapshot=_json.dumps(match_probs)
                    )
                return  # No agregar a value_bets

            if edge > required_edge and prob_percent >= 50.0:
                value_bets.append({
                    "fixture_id": match_fixture_id,
                    "league": match_league,
                    "home_team": match_home,
                    "away_team": match_away,
                    "pick": pick_name,
                    "prob": round(prob_percent, 2),
                    "odds": odds_val,
                    "edge": round(edge * 100, 2),
                    "bookmaker": match_odds.get(pick_name.lower().replace(' ', '_'), {}).get('bookie', 'API'),
                    "type": "🎯 Francotirador",
                    "exact_score": match_probs.get("exact_score", "?-?"),
                    "exact_score_prob": round(match_probs.get("exact_score_prob", 0), 1),
                    "insights": match_probs
                })

            # Ladrillo: alta probabilidad + cuota jugable + edge no demasiado negativo (> -5%)
            if prob_percent >= 60.0 and odds_val >= 1.60 and edge > -0.05:
                safe_bets.append({
                    "fixture_id": match_fixture_id,
                    "league": match_league,
                    "home_team": match_home,
                    "away_team": match_away,
                    "pick": pick_name,
                    "prob": round(prob_percent, 2),
                    "odds": odds_val,
                    "edge": round(edge * 100, 2),
                    "bookmaker": match_odds.get(pick_name.lower().replace(' ', '_'), {}).get('bookie', 'API'),
                    "type": "🧱 Ladrillo",
                    "exact_score": match_probs.get("exact_score", "?-?"),
                    "exact_score_prob": round(match_probs.get("exact_score_prob", 0), 1),
                    "insights": match_probs
                })

        # 3. Analizar matemáticamente
        for match in fixtures:
            fixture_id = str(match.get("fixture", {}).get("id"))
            if fixture_id not in daily_odds:
                continue
                
            teams = match.get("teams", {})
            home_team = teams.get("home", {}).get("name", "Unknown")
            away_team = teams.get("away", {}).get("name", "Unknown")
            home_id = str(teams.get("home", {}).get("id", ""))
            away_id = str(teams.get("away", {}).get("id", ""))
            league_name = match.get("league", {}).get("name", "Unknown")
            
            # Construir contexto
            h_ctx = None
            if home_id in stats_db and away_id in stats_db:
                h_ctx = {
                    "home": stats_db[home_id],
                    "away": stats_db[away_id]
                }
            else:
                # Si no tenemos los datos híbridos, ignoramos el partido para el Radar
                continue
            
            probs = calculate_match_probabilities(
                home_team, away_team, GLOBAL_STATS_DB, current_minute=0, current_home_goals=0, current_away_goals=0, historical_context=h_ctx, league_name=league_name
            )
            
            odds = daily_odds[fixture_id]
            
            # Mapeo de nombres de mercado → clave en probs/odds
            market_key_map = {
                "Home":                ("home",      "home"),
                "Draw":                ("draw",      "draw"),
                "Away":                ("away",      "away"),
                "Double Chance 1X":    ("dc_1x",     "dc_1x"),
                "Double Chance X2":    ("dc_x2",     "dc_x2"),
                "Double Chance 12":    ("dc_12",     "dc_12"),
                "Draw No Bet Home":    ("dnb_home",  "dnb_home"),
                "Draw No Bet Away":    ("dnb_away",  "dnb_away"),
                "Over 2.5":            ("over_2_5",  "over_2_5"),
                "Over 1.5":            ("over_1_5",  "over_1_5"),
                "Over 0.5":            ("over_0_5",  "over_0_5"),
                # Shadow markets — se incluyen para monitoreo silencioso
                "BTTS Yes":            ("btts_yes",  "btts_yes"),
                "BTTS No":             ("btts_no",   "btts_no"),
                "Under 2.5":           ("under_2_5", "under_2_5"),
                "Under 1.5":           ("under_1_5", "under_1_5"),
                "Under 0.5":           ("under_0_5", "under_0_5"),
            }

            # Lista dinámica de todos los mercados (activos + shadow)
            markets_to_check = [
                (name, probs.get(pk, 0), odds.get(ok, {}))
                for name, (pk, ok) in market_key_map.items()
            ]
            
            for pick_name, prob_pct, odd_info in markets_to_check:
                price = odd_info.get('price', 0)
                if price > 1.0:
                    check_edge(prob_pct, price, pick_name, probs, odds,
                               home_team, away_team, league_name, fixture_id)

        # Ordenar por edge descendente

        value_bets.sort(key=lambda x: x["edge"], reverse=True)
        # Ordenar Plan B por probabilidad descendente
        safe_bets.sort(key=lambda x: x["prob"], reverse=True)
        
        final_bets = value_bets + safe_bets
                # --- SHADOW LEDGER (DEDUPLICACIÓN CON SHA-256) ---
        import hashlib
        shadow_file = os.path.join(os.path.dirname(__file__), "athena_shadow_ledger.json")
        shadow_data = []
        existing_hashes = set()
        if os.path.exists(shadow_file):
            with open(shadow_file, "r", encoding="utf-8") as f:
                try:
                    shadow_data = json.load(f)
                    for item in shadow_data:
                        if "record_hash" in item:
                            existing_hashes.add(item["record_hash"])
                except:
                    pass
        
        # Inyectar la fecha, hash único y los picks
        for bet in final_bets:
            # Generar hash único (Fixture ID + Pick)
            hash_str = f"{bet.get('fixture_id')}_{bet.get('pick')}"
            record_hash = hashlib.sha256(hash_str.encode('utf-8')).hexdigest()
            
            if record_hash not in existing_hashes:
                bet['logged_at'] = datetime.now(timezone.utc).isoformat()
                bet['record_hash'] = record_hash
                shadow_data.append(bet)
                existing_hashes.add(record_hash)
            
        with open(shadow_file, "w", encoding="utf-8") as f:
            json.dump(shadow_data, f, ensure_ascii=False, indent=4)
        # ---------------------
        
        return {"status": "success", "date": date, "value_bets": final_bets}
    except Exception as e:
        print(f"Error en scan_day: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/prematch-insight")
def get_prematch_insight(req: PrematchInsightRequest):
    global GLOBAL_STATS_DB
    if not GLOBAL_STATS_DB: 
        GLOBAL_STATS_DB = get_national_elo()
        
    # Cargar Boveda Hibrida
    stats_db = {}
    stats_file = os.path.join(os.path.dirname(__file__), "team_stats_db.json")
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats_db = json.load(f)
        except:
            pass
            
    # Buscar IDs por nombre
    h_stats, a_stats = None, None
    h_id, a_id = None, None
    for tid, tdata in stats_db.items():
        if tdata.get("name") == req.homeTeam:
            h_stats, h_id = tdata, tid
        if tdata.get("name") == req.awayTeam:
            a_stats, a_id = tdata, tid
            
    hist_context = None
    if h_stats and a_stats:
        print(f"[ATHENA] Memoria Hibrida activada para: {req.homeTeam} vs {req.awayTeam}")
        hist_context = {
            "home": h_stats,
            "away": a_stats
        }
        hist_context["home_red_cards"] = h_stats.get("red_cards", 0)
        hist_context["away_red_cards"] = a_stats.get("red_cards", 0)
        
        if req.match_id and req.match_id != "-1":
            injuries_data = api_football_engine.get_fixture_injuries(req.match_id)
            home_injuries = len([i for i in injuries_data if str(i.get("team", {}).get("id")) == str(h_id)]) if injuries_data else 0
            away_injuries = len([i for i in injuries_data if str(i.get("team", {}).get("id")) == str(a_id)]) if injuries_data else 0
            hist_context["home_injuries"] = home_injuries
            hist_context["away_injuries"] = away_injuries
        else:
            hist_context["home_injuries"] = 0
            hist_context["away_injuries"] = 0
    else:
        # Fallback a la API de Football (aunque es mas lenta y no tiene stats avanzadas)
        historical_service = HistoricalContextService()
        if req.match_id and req.match_id != "-1":
            print(f"[ATHENA] Construyendo Memoria Historica para partido: {req.match_id}")
            hist_context = historical_service.build_context(req.match_id)
    
    # 0 porque es pre-match (minute=0, goals=0)
    real_probs = calculate_match_probabilities(
        req.homeTeam, 
        req.awayTeam, 
        GLOBAL_STATS_DB, 
        current_minute=0, 
        current_home_goals=0, 
        current_away_goals=0,
        historical_context=hist_context
    )
    
    return {
        "homeTeam": req.homeTeam,
        "awayTeam": req.awayTeam,
        "probs": real_probs,
        "context": {
            "home_injuries": hist_context.get("home_injuries", 0) if hist_context else 0,
            "away_injuries": hist_context.get("away_injuries", 0) if hist_context else 0,
            "home_red_cards": hist_context.get("home_red_cards", 0) if hist_context else 0,
            "away_red_cards": hist_context.get("away_red_cards", 0) if hist_context else 0
        }
    }

@app.get("/api/delfos/historial")
def api_delfos_historial():
    from portfolio_manager import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM delfos_picks ORDER BY created_at DESC")
    all_picks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Process stats
    hoy_str = datetime.now().strftime("%Y-%m-%d")
    picks_hoy = [p for p in all_picks if p['fecha'] == hoy_str]
    historial = [p for p in all_picks if p['fecha'] != hoy_str and p['resultado'] is not None]
    
    correctos = sum(1 for p in historial if p['es_correcto'] == 1)
    incorrectos = sum(1 for p in historial if p['es_correcto'] == 0)
    refunds = sum(1 for p in historial if p['es_correcto'] == -1)
    total_resueltos = correctos + incorrectos
    
    hit_rate = round((correctos / total_resueltos * 100), 1) if total_resueltos > 0 else 0
    
    # ROI teórico (asumiendo 1u plana)
    profit_teorico = 0
    for p in historial:
        if p['es_correcto'] == 1:
            profit_teorico += (p['cuota'] - 1)
        elif p['es_correcto'] == 0:
            profit_teorico -= 1
            
    roi_teorico = round((profit_teorico / len(historial) * 100), 1) if historial else 0
    
    # Por mercado
    mercados = {}
    for p in historial:
        m = p['pick']
        if m not in mercados:
            mercados[m] = {"total": 0, "correctos": 0, "incorrectos": 0, "profit": 0}
        
        if p['es_correcto'] != -1:
            mercados[m]["total"] += 1
            if p['es_correcto'] == 1:
                mercados[m]["correctos"] += 1
                mercados[m]["profit"] += (p['cuota'] - 1)
            else:
                mercados[m]["incorrectos"] += 1
                mercados[m]["profit"] -= 1
                
    por_mercado = {}
    for m, data in mercados.items():
        if data["total"] > 0:
            por_mercado[m] = {
                "total": data["total"],
                "hit_rate": round(data["correctos"] / data["total"] * 100, 1),
                "roi": round(data["profit"] / data["total"] * 100, 1)
            }
            
    return {
        "resumen": {
            "total_resueltos": total_resueltos,
            "correctos": correctos,
            "incorrectos": incorrectos,
            "refunds": refunds,
            "hit_rate": hit_rate,
            "roi_teorico": roi_teorico
        },
        "por_mercado": por_mercado,
        "picks_hoy": picks_hoy,
        "historial": historial[:100] # Mostrar 100 más recientes
    }






