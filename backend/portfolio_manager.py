import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "tipster.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_portfolio():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT value FROM portfolio WHERE key = 'bankroll'")
    row = cursor.fetchone()
    bankroll = row['value'] if row else 10000.0
    
    cursor.execute("SELECT value FROM portfolio WHERE key = 'initial_bankroll'")
    row = cursor.fetchone()
    initial_bankroll = row['value'] if row else 10000.0
    
    cursor.execute("SELECT * FROM bets ORDER BY id DESC")
    bets = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "bankroll": bankroll,
        "initial_bankroll": initial_bankroll,
        "bets": bets
    }

def place_bet(match_id, pick, odds, stake):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT value FROM portfolio WHERE key = 'bankroll'")
    row = cursor.fetchone()
    bankroll = row['value'] if row else 10000.0
    
    if stake > bankroll:
        conn.close()
        return {"status": "error", "message": "Bankroll insuficiente"}
        
    new_bankroll = bankroll - stake
    bet_id = f"bet_{len(get_portfolio()['bets']) + 1}"
    
    cursor.execute("UPDATE portfolio SET value = ? WHERE key = 'bankroll'", (new_bankroll,))
    if cursor.rowcount == 0:
        cursor.execute("INSERT INTO portfolio (key, value) VALUES ('bankroll', ?)", (new_bankroll,))
        
    cursor.execute('''
        INSERT INTO bets (id, match_id, pick, odds, stake, status, profit)
        VALUES (?, ?, ?, ?, ?, 'OPEN', 0)
    ''', (bet_id, match_id, pick, odds, stake))
    
    conn.commit()
    conn.close()
    
    return {"status": "success", "bet_id": bet_id, "new_bankroll": new_bankroll}

def settle_bet(bet_id, result_status):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM bets WHERE id = ?", (bet_id,))
    bet = cursor.fetchone()
    
    if not bet or bet['status'] != 'OPEN':
        conn.close()
        return {"status": "error", "message": "Apuesta no encontrada o ya cerrada"}
        
    cursor.execute("SELECT value FROM portfolio WHERE key = 'bankroll'")
    row = cursor.fetchone()
    bankroll = row['value'] if row else 10000.0
    
    stake = bet['stake']
    odds = bet['odds']
    
    if result_status == 'WON':
        profit = (stake * odds) - stake
        bankroll += (stake * odds)
    elif result_status == 'LOST':
        profit = -stake
    else: # REFUND
        profit = 0
        bankroll += stake
        
    cursor.execute("UPDATE portfolio SET value = ? WHERE key = 'bankroll'", (bankroll,))
    cursor.execute("UPDATE bets SET status = ?, profit = ? WHERE id = ?", (result_status, profit, bet_id))
    
    conn.commit()
    conn.close()
    
    return {"status": "success", "new_bankroll": bankroll}
