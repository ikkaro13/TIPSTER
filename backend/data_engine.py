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
            outcome INTEGER,
            home_momentum INTEGER DEFAULT 0,
            away_momentum INTEGER DEFAULT 0
        )
    ''')
    
    # Parche de migración para bases de datos existentes
    try:
        cursor.execute("ALTER TABLE historical_matches ADD COLUMN home_momentum INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE historical_matches ADD COLUMN away_momentum INTEGER DEFAULT 0")
    except:
        pass # Las columnas ya existen
        
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
            (id, league_id, home_team, away_team, home_elo, away_elo, elo_diff, home_goals, away_goals, total_goals, btts, outcome, home_momentum, away_momentum)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            match_data["outcome"],
            match_data.get("home_momentum", 0),
            match_data.get("away_momentum", 0)
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error guardando partido historico: {e}")

def get_team_momentum(team_name):
    """
    Calcula el momentum (0 a 15) basado en los últimos 5 partidos del equipo,
    tanto de local como visitante, extraídos de la base de datos histórica.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Buscamos los últimos 5 partidos donde el equipo participó (local o visita)
        cursor.execute('''
            SELECT home_team, away_team, outcome 
            FROM historical_matches 
            WHERE home_team = ? OR away_team = ?
            ORDER BY id DESC LIMIT 5
        ''', (team_name, team_name))
        
        matches = cursor.fetchall()
        conn.close()
        
        points = 0
        for match in matches:
            if match['home_team'] == team_name:
                if match['outcome'] == 2: points += 3
                elif match['outcome'] == 1: points += 1
            else:
                if match['outcome'] == 0: points += 3
                elif match['outcome'] == 1: points += 1
                
        return points
    except Exception as e:
        print(f"Error obteniendo momentum de {team_name}: {e}")
        return 0
