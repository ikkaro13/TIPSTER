import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "tipster.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS elo (
            team TEXT PRIMARY KEY,
            rating INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historical_matches (
            id TEXT PRIMARY KEY,
            league_id INTEGER,
            home_team TEXT,
            away_team TEXT,
            home_elo INTEGER,
            away_elo INTEGER,
            elo_diff INTEGER,
            home_goals INTEGER,
            away_goals INTEGER,
            total_goals INTEGER,
            btts INTEGER,
            outcome INTEGER
        )
    ''')
    conn.commit()
    conn.close()

# Llamar a initialize_db al importar este módulo
initialize_db()

def get_national_elo():
    """
    Carga los Puntos Elo desde la base de datos SQLite.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT team, rating FROM elo")
        rows = cursor.fetchall()
        
        elo_db = {row['team']: row['rating'] for row in rows}
        conn.close()
        return elo_db
    except Exception as e:
        print(f"Error cargando DB Elo: {e}")
        return {}

def save_national_elo(db):
    """
    Guarda los nuevos Puntos Elo calculados permanentemente en SQLite.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for team, rating in db.items():
            cursor.execute("INSERT OR REPLACE INTO elo (team, rating) VALUES (?, ?)", (team, int(rating)))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error guardando DB Elo: {e}")

def save_historical_match(match_data):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO historical_matches 
            (id, league_id, home_team, away_team, home_elo, away_elo, elo_diff, home_goals, away_goals, total_goals, btts, outcome)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            match_data["id"],
            match_data["league_id"],
            match_data["home_team"],
            match_data["away_team"],
            match_data["home_elo"],
            match_data["away_elo"],
            match_data["elo_diff"],
            match_data["home_goals"],
            match_data["away_goals"],
            match_data["total_goals"],
            match_data["btts"],
            match_data["outcome"]
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error guardando partido historico: {e}")
