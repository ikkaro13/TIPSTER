import sqlite3
import json
import os

DB_FILE = "tipster.db"
PORTFOLIO_JSON = "portfolio_db.json"
ELO_JSON = "elo_database.json"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Tabla para Portfolio
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS portfolio (
        key TEXT PRIMARY KEY,
        value REAL
    )
    ''')
    
    # Tabla para Apuestas (Bets)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bets (
        id TEXT PRIMARY KEY,
        match_id TEXT,
        pick TEXT,
        odds REAL,
        stake REAL,
        status TEXT,
        profit REAL
    )
    ''')
    
    # Tabla para ELO
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS elo (
        team TEXT PRIMARY KEY,
        rating INTEGER
    )
    ''')
    
    conn.commit()
    return conn

def migrate_portfolio(conn):
    if not os.path.exists(PORTFOLIO_JSON):
        print(f"No se encontró {PORTFOLIO_JSON}")
        return
        
    with open(PORTFOLIO_JSON, 'r') as f:
        data = json.load(f)
        
    cursor = conn.cursor()
    
    # Insertar balance y bankroll inicial
    cursor.execute("INSERT OR REPLACE INTO portfolio (key, value) VALUES (?, ?)", ("bankroll", data.get("bankroll", 10000)))
    cursor.execute("INSERT OR REPLACE INTO portfolio (key, value) VALUES (?, ?)", ("initial_bankroll", data.get("initial_bankroll", 10000)))
    
    # Insertar apuestas
    for bet in data.get("bets", []):
        cursor.execute('''
            INSERT OR REPLACE INTO bets (id, match_id, pick, odds, stake, status, profit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            bet["id"], bet["match_id"], bet["pick"], bet["odds"], 
            bet["stake"], bet["status"], bet.get("profit", 0)
        ))
    
    print("Portfolio migrado exitosamente.")

def migrate_elo(conn):
    if not os.path.exists(ELO_JSON):
        print(f"No se encontró {ELO_JSON}")
        return
        
    with open(ELO_JSON, 'r') as f:
        data = json.load(f)
        
    cursor = conn.cursor()
    
    for team, rating in data.items():
        cursor.execute("INSERT OR REPLACE INTO elo (team, rating) VALUES (?, ?)", (team, int(rating)))
        
    print(f"Base de datos ELO ({len(data)} equipos) migrada exitosamente.")

if __name__ == "__main__":
    print("Iniciando migración a SQLite...")
    conn = init_db()
    migrate_portfolio(conn)
    migrate_elo(conn)
    conn.commit()
    conn.close()
    print("Migración completada. Base de datos lista en tipster.db")
