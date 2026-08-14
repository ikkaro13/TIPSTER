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

def reset_bankroll(new_amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Update both bankroll and initial_bankroll
    cursor.execute("UPDATE portfolio SET value = ? WHERE key = 'bankroll'", (new_amount,))
    if cursor.rowcount == 0:
        cursor.execute("INSERT INTO portfolio (key, value) VALUES ('bankroll', ?)", (new_amount,))
        
    cursor.execute("UPDATE portfolio SET value = ? WHERE key = 'initial_bankroll'", (new_amount,))
    if cursor.rowcount == 0:
        cursor.execute("INSERT INTO portfolio (key, value) VALUES ('initial_bankroll', ?)", (new_amount,))
        
    conn.commit()
    conn.close()
    return {"status": "success", "new_bankroll": new_amount}

def place_bet(match_id, pick, odds, stake, evidence_snapshot=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT value FROM portfolio WHERE key = 'bankroll'")
        row = cursor.fetchone()
        bankroll = row['value'] if row else 10000.0
        
        if stake > bankroll:
            return {"status": "error", "message": "Bankroll insuficiente"}
            
        new_bankroll = bankroll - stake
        import uuid
        bet_id = f"bet_{uuid.uuid4().hex[:8]}"
        
        cursor.execute("UPDATE portfolio SET value = ? WHERE key = 'bankroll'", (new_bankroll,))
        if cursor.rowcount == 0:
            cursor.execute("INSERT INTO portfolio (key, value) VALUES ('bankroll', ?)", (new_bankroll,))
            
        cursor.execute('''
            INSERT INTO bets (id, match_id, pick, odds, stake, status, profit, evidence_snapshot)
            VALUES (?, ?, ?, ?, ?, 'OPEN', 0, ?)
        ''', (bet_id, match_id, pick, odds, stake, evidence_snapshot))
        
        conn.commit()
        return {"status": "success", "bet_id": bet_id, "new_bankroll": new_bankroll}
    finally:
        conn.close()

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

def delete_bet(bet_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM bets WHERE id = ?", (bet_id,))
    bet = cursor.fetchone()
    
    if not bet:
        conn.close()
        return {"status": "error", "message": "Apuesta no encontrada"}
        
    cursor.execute("SELECT value FROM portfolio WHERE key = 'bankroll'")
    row = cursor.fetchone()
    bankroll = row['value'] if row else 10000.0
    
    stake = bet['stake']
    odds = bet['odds']
    status = bet['status']
    
    # Revertir el bankroll según el estado en el que estaba la apuesta
    if status == 'OPEN':
        bankroll += stake
    elif status == 'WON':
        bankroll = bankroll - (stake * odds) + stake
    elif status == 'LOST':
        bankroll += stake
    elif status == 'REFUND':
        # bankroll remained unchanged when refunded (stake was already returned)
        # Actually, when settled as REFUND, bankroll += stake is done.
        # So to undo it, we shouldn't do anything because the stake was returned, 
        # so if we delete the bet, it's as if the bet never happened. 
        # Wait, if we never placed the bet, we would have stake in bankroll.
        # After place_bet: bankroll - stake
        # After REFUND: bankroll + stake
        # Result = bankroll. So if we delete it now, we don't need to change the bankroll!
        pass
        
    cursor.execute("UPDATE portfolio SET value = ? WHERE key = 'bankroll'", (bankroll,))
    cursor.execute("DELETE FROM bets WHERE id = ?", (bet_id,))
    
    conn.commit()
    conn.close()
    
    return {"status": "success", "new_bankroll": bankroll}

def update_bet_odds(bet_id, new_odds):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM bets WHERE id = ?", (bet_id,))
    bet = cursor.fetchone()
    
    if not bet:
        conn.close()
        return {"status": "error", "message": "Apuesta no encontrada"}
        
    old_odds = bet['odds']
    stake = bet['stake']
    status = bet['status']
    
    cursor.execute("SELECT value FROM portfolio WHERE key = 'bankroll'")
    row = cursor.fetchone()
    bankroll = row['value'] if row else 10000.0
    
    profit = bet['profit']
    
    if status == 'WON':
        # Revert the old win from bankroll
        bankroll = bankroll - (stake * old_odds)
        # Apply the new win
        bankroll = bankroll + (stake * new_odds)
        profit = (stake * new_odds) - stake
        
        cursor.execute("UPDATE portfolio SET value = ? WHERE key = 'bankroll'", (bankroll,))
        
    cursor.execute("UPDATE bets SET odds = ?, profit = ? WHERE id = ?", (new_odds, profit, bet_id))
    
    conn.commit()
    conn.close()
    
    return {"status": "success", "new_bankroll": bankroll}
