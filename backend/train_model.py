import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import data_engine
import joblib
import os
import random

MODEL_1X2_PATH = os.path.join(os.path.dirname(__file__), "model_1x2.pkl")
MODEL_OU_PATH = os.path.join(os.path.dirname(__file__), "model_ou.pkl")
MODEL_BTTS_PATH = os.path.join(os.path.dirname(__file__), "model_btts.pkl")
DB_FILE = os.path.join(os.path.dirname(__file__), "tipster.db")

def generate_synthetic_data(num_matches=5000):
    """Fallback si no hay suficientes datos reales aún."""
    print(f"Generando {num_matches} partidos históricos simulados como fallback...")
    data = []
    
    for _ in range(num_matches):
        home_elo = random.uniform(1400, 2200)
        away_elo = random.uniform(1400, 2200)
        elo_diff = (home_elo + 50) - away_elo
        
        win_prob = 1 / (1 + 10 ** (-elo_diff / 400))
        
        # 1x2
        rand_val = random.random()
        if rand_val < (win_prob - 0.125): outcome = 2
        elif rand_val > (win_prob + 0.125): outcome = 0
        else: outcome = 1
            
        # Over/Under 2.5 (probabilidad base ~50% afectada por Elos muy altos/bajos)
        avg_elo = (home_elo + away_elo) / 2
        over_prob = 0.5 + ((avg_elo - 1500) / 4000)
        over_2_5 = 1 if random.random() < over_prob else 0
        
        # BTTS (muy correlacionado con Over 2.5)
        btts_prob = over_prob - 0.05 if elo_diff < 100 else over_prob - 0.15
        btts = 1 if random.random() < btts_prob else 0
        
        data.append({
            "home_elo": home_elo,
            "away_elo": away_elo,
            "elo_diff": elo_diff,
            "home_momentum": random.randint(0, 15),
            "away_momentum": random.randint(0, 15),
            "outcome": outcome,
            "over_2_5": over_2_5,
            "btts": btts
        })
        
    return pd.DataFrame(data)

def get_real_data():
    if not os.path.exists(DB_FILE):
        return None
        
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT home_elo, away_elo, elo_diff, home_momentum, away_momentum, total_goals, btts, outcome FROM historical_matches", conn)
        conn.close()
        
        if len(df) < 50: # Si hay muy pocos partidos, usar synthetic
            return None
            
        # Reemplazar nulos con 0 para ligas viejas sin momentum
        df["home_momentum"] = df["home_momentum"].fillna(0)
        df["away_momentum"] = df["away_momentum"].fillna(0)
        
        df["over_2_5"] = df["total_goals"].apply(lambda x: 1 if x > 2.5 else 0)
        return df
    except Exception as e:
        print(f"No se pudo cargar datos reales: {e}")
        return None

def train_models():
    print("Iniciando Motor de Machine Learning de ATHENA...")
    
    df = get_real_data()
    if df is not None:
        print(f"✅ ¡Entrenando con {len(df)} partidos REALES de la base de datos!")
    else:
        print("⚠️ No hay suficientes datos reales. Usando simulador sintético.")
        df = generate_synthetic_data()
    
    X = df[["home_elo", "away_elo", "elo_diff", "home_momentum", "away_momentum"]]
    
    # Modelo 1: 1X2 (Ganador)
    y_1x2 = df["outcome"]
    clf_1x2 = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
    clf_1x2.fit(X, y_1x2)
    joblib.dump(clf_1x2, MODEL_1X2_PATH)
    print("✅ Modelo 1X2 (Ganador) entrenado y guardado.")
    
    # Modelo 2: Over/Under 2.5
    y_ou = df["over_2_5"]
    clf_ou = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
    clf_ou.fit(X, y_ou)
    joblib.dump(clf_ou, MODEL_OU_PATH)
    print("✅ Modelo Over/Under entrenado y guardado.")
    
    # Modelo 3: BTTS
    y_btts = df["btts"]
    clf_btts = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
    clf_btts.fit(X, y_btts)
    joblib.dump(clf_btts, MODEL_BTTS_PATH)
    print("✅ Modelo BTTS (Ambos Anotan) entrenado y guardado.")
    
    print("🚀 ¡Módulo de Inteligencia Artificial actualizado con éxito!")

if __name__ == "__main__":
    train_models()
