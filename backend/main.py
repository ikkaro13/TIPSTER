import os
import time
import traceback
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from analytics import calculate_match_probabilities, find_value_bets
from data_engine import get_national_elo
from elo_updater import update_match_result
from portfolio_manager import get_portfolio, place_bet, settle_bet
from pydantic import BaseModel

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

class BetRequest(BaseModel):
    match_id: str
    pick: str
    odds: float
    stake: float

class SettleRequest(BaseModel):
    bet_id: str
    result: str

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

@app.post("/api/portfolio/bet")
def api_place_bet(req: BetRequest):
    return place_bet(req.match_id, req.pick, req.odds, req.stake)

@app.post("/api/portfolio/settle")
def api_settle_bet(req: SettleRequest):
    return settle_bet(req.bet_id, req.result)
# --------------------------------

def update_best_odd(odds_dict, key, outcome_price, bookie_name):
    """ Función auxiliar para encontrar la mejor cuota entre TODAS las casas de apuestas """
    if outcome_price > odds_dict[key]["price"]:
        odds_dict[key] = {"price": outcome_price, "bookie": bookie_name}

@app.get("/api/matches")
def get_matches():
    global GLOBAL_STATS_DB, ODDS_CACHE
    if not GLOBAL_STATS_DB: GLOBAL_STATS_DB = get_national_elo()
        
    try:
        current_time = time.time()
        
        # Verificar caché interno
        if current_time - ODDS_CACHE["timestamp"] < CACHE_TTL and len(ODDS_CACHE["data"]) > 0:
            print("Sirviendo desde Caché (ahorrando Request API)")
            data = ODDS_CACHE["data"]
        else:
            print("Consultando a The Odds API...")
            url = f"https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals,spreads"
            response = requests.get(url, verify=False)
            
            if response.status_code != 200:
                print(f"La API TheOddsAPI devolvió error {response.status_code}. Usando Mock Data de demostración.")
                data = [] # Forzar mock data
            else:
                data = response.json()
                ODDS_CACHE["timestamp"] = current_time
                ODDS_CACHE["data"] = data
            
        processed_matches = []
        
        if len(data) == 0:
            data = [
                {"id": "w1", "home_team": "Argentina", "away_team": "Mexico", "commence_time": "2026-06-30T18:00:00Z", 
                 "bookmakers": [
                     {"title": "Bet365", "markets": [{"key": "h2h", "outcomes": [{"name": "Argentina", "price": 1.45}, {"name": "Mexico", "price": 6.50}, {"name": "Draw", "price": 4.10}]}, {"key": "totals", "outcomes": [{"name": "Over", "point": 2.5, "price": 1.95}, {"name": "Under", "point": 2.5, "price": 1.85}]}]},
                     {"title": "Pinnacle", "markets": [{"key": "h2h", "outcomes": [{"name": "Argentina", "price": 1.50}, {"name": "Mexico", "price": 6.80}, {"name": "Draw", "price": 4.20}]}]} # Pinnacle ofrece mejor cuota para Mexico
                 ]}
            ]
        
        mx_tz = timezone(timedelta(hours=-6))
        today_date = datetime.now(mx_tz).date()

        for match in data:
            if not match.get("bookmakers"): continue
            
            # Filtro para mostrar solo los partidos "de hoy" (Fecha México)
            dt_str = match["commence_time"].replace('Z', '+00:00')
            dt = datetime.fromisoformat(dt_str)
            dt_mx = dt.astimezone(mx_tz)
            
            if dt_mx.date() != today_date:
                continue
            
            # Estructura que almacena la mejor cuota y QUIÉN la ofrece
            odds_data = {
                "home": {"price": 0, "bookie": ""}, "draw": {"price": 0, "bookie": ""}, "away": {"price": 0, "bookie": ""}, 
                "over_1_5": {"price": 0, "bookie": ""}, "under_1_5": {"price": 0, "bookie": ""},
                "over_2_5": {"price": 0, "bookie": ""}, "under_2_5": {"price": 0, "bookie": ""},
                "over_3_5": {"price": 0, "bookie": ""}, "under_3_5": {"price": 0, "bookie": ""},
                "btts_yes": {"price": 0, "bookie": ""},
                "btts_no": {"price": 0, "bookie": ""},
                "home_minus_1_5": {"price": 0, "bookie": ""}, "away_minus_1_5": {"price": 0, "bookie": ""}
            }
            
            # Line Shopping: Escaneamos TODAS las casas de apuestas
            for bookie in match["bookmakers"]:
                b_name = bookie["title"]
                
                market_h2h = next((m for m in bookie["markets"] if m["key"] == "h2h"), None)
                if market_h2h:
                    for outcome in market_h2h["outcomes"]:
                        if outcome["name"] == match["home_team"]: update_best_odd(odds_data, "home", outcome["price"], b_name)
                        elif outcome["name"] == match["away_team"]: update_best_odd(odds_data, "away", outcome["price"], b_name)
                        elif outcome["name"] == "Draw": update_best_odd(odds_data, "draw", outcome["price"], b_name)
                
                market_totals = next((m for m in bookie["markets"] if m["key"] == "totals"), None)
                if market_totals:
                    for outcome in market_totals["outcomes"]:
                        if outcome.get("point") == 1.5:
                            if outcome["name"] == "Over": update_best_odd(odds_data, "over_1_5", outcome["price"], b_name)
                            elif outcome["name"] == "Under": update_best_odd(odds_data, "under_1_5", outcome["price"], b_name)
                        elif outcome.get("point") == 2.5:
                            if outcome["name"] == "Over": update_best_odd(odds_data, "over_2_5", outcome["price"], b_name)
                            elif outcome["name"] == "Under": update_best_odd(odds_data, "under_2_5", outcome["price"], b_name)
                        elif outcome.get("point") == 3.5:
                            if outcome["name"] == "Over": update_best_odd(odds_data, "over_3_5", outcome["price"], b_name)
                            elif outcome["name"] == "Under": update_best_odd(odds_data, "under_3_5", outcome["price"], b_name)
                            
                market_btts = next((m for m in bookie["markets"] if m["key"] == "btts"), None)
                if market_btts:
                    for outcome in market_btts["outcomes"]:
                        if outcome["name"] == "Yes": update_best_odd(odds_data, "btts_yes", outcome["price"], b_name)
                        elif outcome["name"] == "No": update_best_odd(odds_data, "btts_no", outcome["price"], b_name)
                            
                market_spreads = next((m for m in bookie["markets"] if m["key"] == "spreads"), None)
                if market_spreads:
                    for outcome in market_spreads["outcomes"]:
                        if outcome.get("point") == -1.5:
                            if outcome["name"] == match["home_team"]: update_best_odd(odds_data, "home_minus_1_5", outcome["price"], b_name)
                            elif outcome["name"] == match["away_team"]: update_best_odd(odds_data, "away_minus_1_5", outcome["price"], b_name)
            
            home_team = match["home_team"]
            away_team = match["away_team"]
            
            # Smart Money Tracker Logic
            match_id = match["id"]
            smart_money = False
            current_home_price = odds_data["home"]["price"]
            
            if match_id not in ODDS_CACHE and current_home_price > 0:
                ODDS_CACHE[match_id] = current_home_price
            elif current_home_price > 0:
                opening_price = ODDS_CACHE[match_id]
                if opening_price > current_home_price:
                    drop = (opening_price - current_home_price) / opening_price
                    if drop >= 0.10: # Caída dramática de cuota (>10%)
                        smart_money = True
            
            # Arbitrage (Surebet) Detection Logic
            arbitrage_alert = {"active": False, "roi_percent": 0.0}
            try:
                p_home = odds_data["home"]["price"]
                p_draw = odds_data["draw"]["price"]
                p_away = odds_data["away"]["price"]
                
                if p_home > 0 and p_draw > 0 and p_away > 0:
                    margin = (1.0 / p_home) + (1.0 / p_draw) + (1.0 / p_away)
                    if margin < 1.0:
                        roi = ((1.0 / margin) - 1.0) * 100
                        arbitrage_alert = {
                            "active": True, 
                            "roi_percent": round(roi, 2),
                            "margin": margin,
                            "home": {"bookie": odds_data["home"]["bookie"], "price": p_home},
                            "draw": {"bookie": odds_data["draw"]["bookie"], "price": p_draw},
                            "away": {"bookie": odds_data["away"]["bookie"], "price": p_away}
                        }
            except Exception:
                pass
            
            real_probs = calculate_match_probabilities(home_team, away_team, GLOBAL_STATS_DB)
            analysis = find_value_bets(real_probs, odds_data)
            
            # dt_mx ya está calculado arriba
            
            processed_matches.append({
                "id": match["id"],
                "league": "Mundial FIFA 2026",
                "homeTeam": home_team,
                "awayTeam": away_team,
                "startTime": dt_mx.strftime("%d/%m %H:%M"),
                "status": "UPCOMING",
                "score": "-",
                "minute": "-",
                "smart_money_alert": smart_money,
                "arbitrage_alert": arbitrage_alert,
                "odds": odds_data,
                "analysis": analysis
            })
            
        return processed_matches
    except Exception as e:
        print(f"Excepcion de conexión: {e}")
        traceback.print_exc()
        return []
