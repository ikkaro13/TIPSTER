import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "tipster.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

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
