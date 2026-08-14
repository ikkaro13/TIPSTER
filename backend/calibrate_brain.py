import json
import os
import numpy as np

CORPUS_FILE = os.path.join(os.path.dirname(__file__), "decision_corpus.jsonl")

def calibrate():
    if not os.path.exists(CORPUS_FILE):
        print("Aún no hay Decision Corpus disponible. Corre una Autopsia primero.")
        return
        
    corpus = []
    with open(CORPUS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                corpus.append(json.loads(line))
                
    if not corpus:
        print("El Corpus está vacío.")
        return
        
    total_bets = len(corpus)
    won_bets = sum(1 for c in corpus if c['is_won'] == 1)
    win_rate = (won_bets / total_bets) * 100
    
    print("========================================")
    print("🧠 ATHENA: CALIBRACIÓN DE CEREBRO 🧠")
    print("========================================")
    print(f"Decisiones Tomadas: {total_bets}")
    print(f"Aciertos: {won_bets}")
    print(f"Win Rate Histórico: {win_rate:.2f}%\n")
    
    # Análisis de Confianza
    # Comparamos la confianza predicha (probabilidad) vs resultado real (Brier Score simplificado)
    brier_sum = 0.0
    valid_probs = 0
    
    for c in corpus:
        pick = c['pick'].lower()
        evidence = c.get('evidence', {})
        prob_predicha = 0.0
        
        if "home" in pick or "local" in pick: prob_predicha = evidence.get("home", 0) / 100.0
        elif "away" in pick or "visita" in pick: prob_predicha = evidence.get("away", 0) / 100.0
        elif "draw" in pick or "empate" in pick: prob_predicha = evidence.get("draw", 0) / 100.0
        elif "más de 2.5" in pick or "over 2.5" in pick: prob_predicha = evidence.get("over_2_5", 0) / 100.0
        elif "menos de 2.5" in pick or "under 2.5" in pick: prob_predicha = evidence.get("under_2_5", 0) / 100.0
        elif "ambos anotan (sí)" in pick: prob_predicha = evidence.get("btts_yes", 0) / 100.0
        elif "ambos anotan (no)" in pick: prob_predicha = evidence.get("btts_no", 0) / 100.0
        
        if prob_predicha > 0:
            resultado = c['is_won']
            brier_sum += (prob_predicha - resultado) ** 2
            valid_probs += 1
            
    if valid_probs > 0:
        brier_score = brier_sum / valid_probs
        print(f"Brier Score (Precisión de Probabilidad): {brier_score:.4f} (Ideal: 0.0)")
    
    print("\n[INFO] En el futuro, este script inyectará este Corpus en scikit-learn para re-entrenar model.pkl")
    print("========================================\n")

if __name__ == "__main__":
    calibrate()
