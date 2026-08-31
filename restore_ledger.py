import json
import sqlite3
import os

corpus_path = 'backend/decision_corpus.jsonl'
db_path = 'backend/tipster.db'

if not os.path.exists(corpus_path):
    print("NO SE ENCONTRO decision_corpus.jsonl")
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Get current bets to avoid duplicates
c.execute("SELECT id FROM bets")
existing_bets = {row[0] for row in c.fetchall()}

restored = 0
with open(corpus_path, 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip(): continue
        try:
            data = json.loads(line)
            bet_id = data.get('bet_id')
            if bet_id in existing_bets: continue
            
            match_id = data.get('match_id', 'RESTORED')
            pick = data.get('pick', 'Unknown Pick')
            is_won = data.get('is_won', 0)
            status = 'WON' if is_won else 'LOST'
            
            evidence = data.get('evidence', {})
            odds = evidence.get('odds', 1.5)
            # Asumimos un stake estándar de  (1 Unidad) para visualización
            stake = 100.0
            profit = round(stake * (odds - 1), 2) if is_won else -stake
            
            evidence_str = json.dumps(evidence) if evidence else None
            
            c.execute('''
                INSERT INTO bets (id, match_id, pick, odds, stake, status, profit, evidence_snapshot)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (bet_id, match_id, pick, odds, stake, status, profit, evidence_str))
            
            restored += 1
        except Exception as e:
            print(f"Error procesando linea: {e}")

conn.commit()
conn.close()
print(f"EXCELENTE: Se restauraron {restored} apuestas históricas en Plutus.")
