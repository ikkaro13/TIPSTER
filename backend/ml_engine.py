import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import random
import os

MODEL_PATH = "model.pkl"

def generate_synthetic_data(num_matches=5000):
    """
    Simula datos históricos de partidos de fútbol basados en la diferencia de ELO.
    En la vida real, aquí se cargaría un CSV con resultados históricos de la FIFA.
    """
    print(f"Generando {num_matches} partidos históricos simulados...")
    data = []
    
    for _ in range(num_matches):
        home_elo = random.uniform(1400, 2200)
        away_elo = random.uniform(1400, 2200)
        
        # El equipo local siempre tiene una ligera ventaja (+50 Elo aprox)
        elo_diff = (home_elo + 50) - away_elo
        
        # Probabilidades base basadas en ELO
        win_prob = 1 / (1 + 10 ** (-elo_diff / 400))
        
        # Agregar ruido (variables ocultas: lesiones, clima, motivación)
        noise = random.uniform(-0.15, 0.15)
        adjusted_prob = win_prob + noise
        
        # Determinar el resultado (2: Local, 1: Empate, 0: Visita)
        # Asumiendo ~25% de empates constantes en fútbol
        rand_val = random.random()
        if rand_val < (adjusted_prob - 0.125):
            outcome = 2 # Gana Local
        elif rand_val > (adjusted_prob + 0.125):
            outcome = 0 # Gana Visita
        else:
            outcome = 1 # Empate
            
        data.append({
            "home_elo": home_elo,
            "away_elo": away_elo,
            "elo_diff": elo_diff,
            "outcome": outcome
        })
        
    return pd.DataFrame(data)

def train_model():
    print("Iniciando motor de Deep Learning (Random Forest)...")
    df = generate_synthetic_data()
    
    # Features (X) y Target (y)
    X = df[["home_elo", "away_elo", "elo_diff"]]
    y = df["outcome"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Entrenar el modelo
    print("Entrenando el bosque de árboles de decisión...")
    clf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
    clf.fit(X_train, y_train)
    
    # Evaluar
    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"✅ Entrenamiento completado. Precisión del modelo (Accuracy): {acc * 100:.2f}%")
    
    # Guardar modelo
    joblib.dump(clf, MODEL_PATH)
    print(f"🧠 Modelo exportado exitosamente a {MODEL_PATH}")

if __name__ == "__main__":
    train_model()
