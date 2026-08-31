import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "tipster.db")


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS portfolio (key TEXT PRIMARY KEY, value REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS bets (id TEXT PRIMARY KEY, match_id TEXT, pick TEXT, odds REAL, stake REAL, status TEXT, profit REAL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, evidence_snapshot TEXT, bet_type TEXT DEFAULT 'PRE')")
    
    # NUEVO SCHEMA PARA BANKROLL_AUDIT_LOG
    c.execute("""
    CREATE TABLE IF NOT EXISTS bankroll_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bet_id TEXT,
        action TEXT,
        delta REAL,
        bankroll_before REAL,
        bankroll_after REAL,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    
    c.execute("CREATE TABLE IF NOT EXISTS delfos_picks (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, league TEXT, match TEXT, market TEXT, confidence REAL, edge REAL, odds REAL, status TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, evidence_snapshot TEXT)")
    c.execute("SELECT * FROM portfolio WHERE key = 'bankroll'")
    if not c.fetchone():
        c.execute("INSERT INTO portfolio (key, value) VALUES ('bankroll', 1000.0)")
        c.execute("INSERT INTO portfolio (key, value) VALUES ('initial_bankroll', 1000.0)")
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("""
    CREATE TABLE IF NOT EXISTS bankroll_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bet_id TEXT,
        action TEXT,
        delta REAL,
        bankroll_before REAL,
        bankroll_after REAL,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)
    
    # MIGRACION AUTOMATICA
    try:
        conn.execute("ALTER TABLE bets ADD COLUMN bet_type TEXT DEFAULT 'PRE'")
    except sqlite3.OperationalError:
        pass # La columna ya existe
        
    conn.commit()
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
    
    cursor.execute("SELECT * FROM bets ORDER BY created_at DESC")
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
        
    conn.execute("""
    CREATE TABLE IF NOT EXISTS bankroll_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bet_id TEXT,
        action TEXT,
        delta REAL,
        bankroll_before REAL,
        bankroll_after REAL,
        created_at TEXT DEFAULT (datetime('now'))
    );
""")
    conn.commit()
    conn.close()
    return {"status": "success", "new_bankroll": new_amount}

def place_bet(match_id, pick, odds, stake, evidence_snapshot=None, bet_type="PRE"):
    conn = get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM portfolio WHERE key = 'bankroll'")
        row = cursor.fetchone()
        bankroll = row['value'] if row else 10000.0
        
        if stake > bankroll:
            conn.rollback()
            return {"status": "error", "message": "Bankroll insuficiente"}
            
        new_bankroll = bankroll - stake
        import uuid
        bet_id = f"bet_{uuid.uuid4().hex[:8]}"
        
        cursor.execute("UPDATE portfolio SET value = ? WHERE key = 'bankroll'", (new_bankroll,))
        if cursor.rowcount == 0:
            cursor.execute("INSERT INTO portfolio (key, value) VALUES ('bankroll', ?)", (new_bankroll,))
            
        cursor.execute('''
            INSERT INTO bets (id, match_id, pick, odds, stake, status, profit, evidence_snapshot, created_at, bet_type)
            VALUES (?, ?, ?, ?, ?, 'OPEN', 0, ?, datetime('now'), ?)
        ''', (bet_id, match_id, pick, odds, stake, evidence_snapshot, bet_type))
        
        cursor.execute('''
            INSERT INTO bankroll_audit_log (bet_id, action, delta, bankroll_before, bankroll_after)
            VALUES (?, 'PLACE_BET', ?, ?, ?)
        ''', (bet_id, -stake, bankroll, new_bankroll))
        
        conn.commit()
        return {"status": "success", "bet_id": bet_id, "new_bankroll": new_bankroll}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()

def settle_bet(bet_id, result_status):
    conn = get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM bets WHERE id = ?", (bet_id,))
        bet = cursor.fetchone()
        
        if not bet or bet['status'] != 'OPEN':
            conn.rollback()
            return {"status": "error", "message": "Apuesta no encontrada o ya cerrada"}
            
        cursor.execute("SELECT value FROM portfolio WHERE key = 'bankroll'")
        row = cursor.fetchone()
        bankroll = row['value'] if row else 10000.0
        
        stake = bet['stake']
        odds = bet['odds']
        
        if result_status == 'WON':
            profit = (stake * odds) - stake
            new_bankroll = bankroll + (stake * odds)
        elif result_status == 'LOST':
            profit = -stake
            new_bankroll = bankroll
        else: # REFUND
            profit = 0
            new_bankroll = bankroll + stake
            
        cursor.execute("UPDATE portfolio SET value = ? WHERE key = 'bankroll'", (new_bankroll,))
        cursor.execute("UPDATE bets SET status = ?, profit = ? WHERE id = ?", (result_status, profit, bet_id))
        
        cursor.execute('''
            INSERT INTO bankroll_audit_log (bet_id, action, delta, bankroll_before, bankroll_after)
            VALUES (?, 'SETTLE', ?, ?, ?)
        ''', (bet_id, new_bankroll - bankroll, bankroll, new_bankroll))
        
        conn.commit()
        return {"status": "success", "new_bankroll": new_bankroll}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()

def reopen_bet(bet_id):
    conn = get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM bets WHERE id = ?", (bet_id,))
        bet = cursor.fetchone()
        
        if not bet:
            conn.rollback()
            return {"status": "error", "message": "Apuesta no encontrada"}
        
        if bet['status'] == 'OPEN':
            conn.rollback()
            return {"status": "error", "message": "La apuesta ya esta abierta"}
            
        cursor.execute("SELECT value FROM portfolio WHERE key = 'bankroll'")
        row = cursor.fetchone()
        bankroll = row['value'] if row else 10000.0
        
        stake = bet['stake']
        odds = bet['odds']
        current_status = bet['status']
        new_bankroll = bankroll
        
        if current_status == 'WON':
            new_bankroll = bankroll - (stake * odds)
        elif current_status == 'LOST':
            new_bankroll = bankroll - stake
        elif current_status == 'REFUND':
            new_bankroll = bankroll - stake
        
        cursor.execute("UPDATE portfolio SET value = ? WHERE key = 'bankroll'", (new_bankroll,))
        cursor.execute("UPDATE bets SET status = 'OPEN', profit = 0 WHERE id = ?", (bet_id,))
        
        cursor.execute('''
            INSERT INTO bankroll_audit_log (bet_id, action, delta, bankroll_before, bankroll_after)
            VALUES (?, 'REOPEN', ?, ?, ?)
        ''', (bet_id, new_bankroll - bankroll, bankroll, new_bankroll))
        
        conn.commit()
        return {"status": "success", "message": f"Apuesta reabierta correctamente.", "new_bankroll": new_bankroll}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()

def delete_bet(bet_id):
    conn = get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM bets WHERE id = ?", (bet_id,))
        bet = cursor.fetchone()
        
        if not bet:
            conn.rollback()
            return {"status": "error", "message": "Apuesta no encontrada"}
            
        cursor.execute("SELECT value FROM portfolio WHERE key = 'bankroll'")
        row = cursor.fetchone()
        bankroll = row['value'] if row else 10000.0
        
        stake = bet['stake']
        odds = bet['odds']
        status = bet['status']
        new_bankroll = bankroll
        
        if status == 'OPEN':
            new_bankroll += stake
        elif status == 'WON':
            new_bankroll = bankroll - (stake * odds) + stake
        elif status == 'LOST':
            new_bankroll += stake
        elif status == 'REFUND':
            pass
            
        cursor.execute("UPDATE portfolio SET value = ? WHERE key = 'bankroll'", (new_bankroll,))
        cursor.execute("DELETE FROM bets WHERE id = ?", (bet_id,))
        
        try:
            cursor.execute('''
                INSERT INTO bankroll_audit_log (bet_id, action, delta, bankroll_before, bankroll_after)
                VALUES (?, 'DELETE', ?, ?, ?)
            ''', (bet_id, new_bankroll - bankroll, bankroll, new_bankroll))
        except Exception as audit_err:
            print(f"Warning: Could not write to audit log: {audit_err}")
        
        conn.commit()
        return {"status": "success", "new_bankroll": new_bankroll}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()

def update_bet_odds(bet_id, new_odds):
    conn = get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM bets WHERE id = ?", (bet_id,))
        bet = cursor.fetchone()
        
        if not bet:
            conn.rollback()
            return {"status": "error", "message": "Apuesta no encontrada"}
            
        old_odds = bet['odds']
        stake = bet['stake']
        status = bet['status']
        
        cursor.execute("SELECT value FROM portfolio WHERE key = 'bankroll'")
        row = cursor.fetchone()
        bankroll = row['value'] if row else 10000.0
        
        profit = bet['profit']
        new_bankroll = bankroll
        
        if status == 'WON':
            new_bankroll = bankroll - (stake * old_odds)
            new_bankroll = new_bankroll + (stake * new_odds)
            profit = (stake * new_odds) - stake
            
            cursor.execute("UPDATE portfolio SET value = ? WHERE key = 'bankroll'", (new_bankroll,))
            
        cursor.execute("UPDATE bets SET odds = ?, profit = ? WHERE id = ?", (new_odds, profit, bet_id))
        
        cursor.execute('''
            INSERT INTO bankroll_audit_log (bet_id, action, delta, bankroll_before, bankroll_after)
            VALUES (?, 'UPDATE_ODDS', ?, ?, ?)
        ''', (bet_id, new_bankroll - bankroll, bankroll, new_bankroll))
        
        conn.commit()
        return {"status": "success", "new_bankroll": new_bankroll}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()

