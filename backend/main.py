import os
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
from portfolio_manager import get_portfolio, place_bet, settle_bet, reset_bankroll, delete_bet, update_bet_odds
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

class BetRequest(BaseModel):
    match_id: str
    pick: str
    odds: float
    stake: float
    evidence_snapshot: str = None
    bet_type: str = "PRE"

class ResetBankrollRequest(BaseModel):
    new_amount: float

class SettleRequest(BaseModel):
    result: str

class UpdateOddsRequest(BaseModel):
    odds: float

class DeleteBetRequest(BaseModel):
    bet_id: str

app = FastAPI(title="Tipster API Financial Grade", version="5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = "42cbf57204514f65c3ba5cbf2b440a0f"
GLOBAL_STATS_DB = None
ODDS_CACHE = {"timestamp": 0, "data": []}
CACHE_TTL = 3600 # 1 hora de caché

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

@app.on_event("startup")
def startup_event():
    global GLOBAL_STATS_DB
    GLOBAL_STATS_DB = get_national_elo()

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
        'probs': req.probs
    }
    
    h = Hermes()
    result = h.analyze(context)
    return {"hermes": result}

@app.post("/api/portfolio/bet")
def api_place_bet(req: BetRequest):
    return place_bet(req.match_id, req.pick, req.odds, req.stake, req.evidence_snapshot, req.bet_type)

@app.post("/api/portfolio/reset")
def api_reset_bankroll(req: ResetBankrollRequest):
    return reset_bankroll(req.new_amount)

@app.post("/api/portfolio/settle/{bet_id}")
def settle_bet_endpoint(bet_id: str, request: SettleRequest):
    return settle_bet(bet_id, request.result)

@app.delete("/api/portfolio/bets/{bet_id}")
def delete_bet_endpoint(bet_id: str):
    res = delete_bet(bet_id)
    if res.get("status") == "error":
        raise HTTPException(status_code=404, detail=res["message"])
    return res

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
    
    # Solo dispara por GPI alto o estado de candidato, no por simple acumulación lenta de xG
    athena_state['goal_alert'] = (gpi >= 75) or (athena_state['state'] == 'VALUE CANDIDATE')
    
    # --- ALERTA TELEGRAM ---
    if athena_state['goal_alert']:
        alert_id = f"{match_id}_{live_data['minute']}_{athena_state['state']}"
        
        texto_apuesta = "PRÓXIMO GOL"
        if live_data['minute'] < 40:
            texto_apuesta = "OVER 0.5 HT o PRÓXIMO GOL"
            
        msg = (
            f"🚨 <b>ALERTA ATHENA LIVE</b> 🚨\n\n"
            f"Partido ID: <code>{match_id}</code>\n"
            f"Minuto: {live_data['minute']}'\n"
            f"<b>GPI (Goal Pressure Index):</b> {gpi}\n"
            f"<b>Momentum:</b> {athena_state['momentum']}\n\n"
            f"🔥 <i>RECOMENDACIÓN: {texto_apuesta}. Presión ofensiva crítica detectada.</i>"
        )
        send_telegram_alert(msg, alert_id)
    
    return {
        "match_id": match_id,
        "live_data": live_data,
        "athena": athena_state
    }
# --------------------------------

def update_best_odd(odds_dict, key, outcome_price, bookie_name):
    """ Función auxiliar para encontrar la mejor cuota entre TODAS las casas de apuestas """
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
        
        # [OPTIMIZACIÓN DE TOKENS]
        # Cargar cuotas del día de forma masiva para evitar N+1 requests
        import odds_connector
        current_date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        if not hasattr(get_matches, "bulk_odds_cache"):
            get_matches.bulk_odds_cache = {"date": "", "timestamp": 0, "data": {}}
            
        if get_matches.bulk_odds_cache["date"] != current_date_str or (time.time() - get_matches.bulk_odds_cache["timestamp"]) > 900: # Caché de 15 min
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
            
            # En un entorno de producción, aquí leeríamos el historial de cuotas 
            # desde la DB o Caché y lo compararíamos con las cuotas actuales.
            # Como la API gratuita restringe las peticiones, usamos una simulación
            # de caída de cuotas institucional (>10% drop).
            if fixture_id == "mock_12345":
                # Simulamos que un 30% del tiempo detectamos una caída brusca
                if random.random() < 0.3:
                    smart_money = True
                    print("[ATHENA] 🚨 ALERTA INSTITUCIONAL: Dinero Inteligente Detectado en Mock Match")
            
            # Arbitrage (Surebet) Detection Logic
            arbitrage_alert = {"active": False, "roi_percent": 0.0}
            
            # Usar la caché masiva en lugar de pegarle a la API individualmente por cada partido en vivo
            odds_data = daily_odds.get(fixture_id, {})
            
            real_probs = calculate_match_probabilities(home_team, away_team, GLOBAL_STATS_DB)
            analysis = find_value_bets(real_probs, odds_data)
            
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
                "league": "Liga Pro Ecuador (Simulación ATHENA)",
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
        print(f"Excepcion de conexión: {e}")
        traceback.print_exc()
        return []

@app.get("/api/calendar")
def get_daily_calendar(date: str = None):
    try:
        mx_tz = timezone(timedelta(hours=-6))
        
        if date:
            # Si el usuario mandó fecha específica
            query_date = date
        else:
            query_date = datetime.now(mx_tz).strftime("%Y-%m-%d")
            
        data = api_football_engine.get_daily_fixtures(query_date, timezone_str="America/Mexico_City")
        
        calendar_matches = []
        for match in data:
            fixture = match.get("fixture", {})
            teams = match.get("teams", {})
            league = match.get("league", {})
            
            home_team = teams.get("home", {}).get("name", "Unknown")
            away_team = teams.get("away", {}).get("name", "Unknown")
            
            dt_str = fixture.get("date")
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00')) if dt_str else datetime.now(timezone.utc)
            dt_mx = dt.astimezone(mx_tz)
            
            calendar_matches.append({
                "id": str(fixture.get("id")),
                "league": league.get("name", "API-Football League"),
                "round": league.get("round", ""),
                "homeTeam": home_team,
                "awayTeam": away_team,
                "startTime": dt_mx.strftime("%H:%M"),
                "status": fixture.get("status", {}).get("long", ""),
                "timestamp": fixture.get("timestamp", 0)
            })
            
            
        # Ordenar por hora de juego (timestamp)
        calendar_matches.sort(key=lambda x: x["timestamp"])
        
        if len(calendar_matches) == 0:
            print("Inyectando partido simulado en el Calendario")
            calendar_matches.append({
                "id": "mock_12345",
                "league": "Liga Pro Ecuador (Simulación ATHENA)",
                "round": "Final",
                "homeTeam": "Deportivo Cuenca",
                "awayTeam": "Manta FC",
                "startTime": "20:00",
                "status": "Not Started",
                "timestamp": 9999999999
            })
            
        return calendar_matches
    except Exception as e:
        print(f"Error en calendario: {e}")
        return []

@app.get("/api/chronos/scan-day")
def scan_day_for_value_bets(date: str):
    global GLOBAL_STATS_DB
    if not GLOBAL_STATS_DB: 
        GLOBAL_STATS_DB = get_national_elo()
        
    try:
        # 1. Obtener todos los partidos del día
        fixtures = api_football_engine.get_daily_fixtures(date, timezone_str="America/Mexico_City")
        if not fixtures:
            return {"status": "success", "date": date, "value_bets": []}
            
        # 2. Extraer cuotas globales
        daily_odds = odds_connector.fetch_odds_by_date(date)
        
        value_bets = []
        
        # 3. Analizar matemáticamente
        for match in fixtures:
            fixture_id = str(match.get("fixture", {}).get("id"))
            if fixture_id not in daily_odds:
                continue
                
            teams = match.get("teams", {})
            home_team = teams.get("home", {}).get("name", "Unknown")
            away_team = teams.get("away", {}).get("name", "Unknown")
            league_name = match.get("league", {}).get("name", "Unknown")
            
            # FILTRO CRÍTICO: Si no tenemos ELO real para ninguno de los equipos, el motor genera un 
            # 54.42% genérico de Under 2.5 (probabilidad fantasma). Debemos ignorar estos partidos.
            if home_team not in GLOBAL_STATS_DB or away_team not in GLOBAL_STATS_DB:
                continue
            
            probs = calculate_match_probabilities(
                home_team, away_team, GLOBAL_STATS_DB, current_minute=0, current_home_goals=0, current_away_goals=0, historical_context=None
            )
            
            odds = daily_odds[fixture_id]
            
            # Helper to check edge
            def check_edge(prob_percent, odds_val, pick_name):
                prob = prob_percent / 100.0
                edge = (prob * odds_val) - 1
                
                # REGLA: Equilibrio matemático y realidad
                # Exigimos un mínimo de 50% de probabilidad real base para evitar buscar "milagros" matemáticos.
                if edge > 0.05 and prob_percent >= 50.0:
                    value_bets.append({
                        "fixture_id": fixture_id,
                        "league": league_name,
                        "home_team": home_team,
                        "away_team": away_team,
                        "pick": pick_name,
                        "prob": round(prob_percent, 2),
                        "odds": odds_val,
                        "edge": round(edge * 100, 2),
                        "bookie": odds.get(pick_name.lower().replace(' ', '_'), {}).get('bookie', 'Unknown')
                    })
                    
            if odds.get('home', {}).get('price', 0) > 1.0:
                check_edge(probs['home'], odds['home']['price'], "Home")
            if odds.get('draw', {}).get('price', 0) > 1.0:
                check_edge(probs['draw'], odds['draw']['price'], "Draw")
            if odds.get('away', {}).get('price', 0) > 1.0:
                check_edge(probs['away'], odds['away']['price'], "Away")
            if odds.get('over_2_5', {}).get('price', 0) > 1.0:
                check_edge(probs['over_2_5'], odds['over_2_5']['price'], "Over 2.5")
            if odds.get('under_2_5', {}).get('price', 0) > 1.0:
                check_edge(probs['under_2_5'], odds['under_2_5']['price'], "Under 2.5")
            if odds.get('btts_yes', {}).get('price', 0) > 1.0:
                check_edge(probs['btts_yes'], odds['btts_yes']['price'], "BTTS Yes")
                
        # Ordenar por edge descendente
        value_bets.sort(key=lambda x: x["edge"], reverse=True)
        
        return {"status": "success", "date": date, "value_bets": value_bets}
    except Exception as e:
        print(f"Error en scan_day: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/prematch-insight")
def get_prematch_insight(req: PrematchInsightRequest):
    global GLOBAL_STATS_DB
    if not GLOBAL_STATS_DB: 
        GLOBAL_STATS_DB = get_national_elo()
        
    # Obtener memoria histórica real si el match_id es válido
    historical_service = HistoricalContextService()
    hist_context = None
    if req.match_id and req.match_id != "-1":
        print(f"[ATHENA] Construyendo Memoria Histórica para partido: {req.match_id}")
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
        "probs": real_probs
    }
