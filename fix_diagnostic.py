import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_endpoint = '''
@app.get("/api/delfos/diagnostic")
def delfos_diagnostic():
    from portfolio_manager import get_db_connection
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM bets')
    total = c.fetchone()[0]
    
    c.execute('SELECT status, COUNT(*) FROM bets GROUP BY status')
    status_counts = dict(c.fetchall())
    
    c.execute('SELECT COUNT(*) FROM bets WHERE evidence_snapshot IS NOT NULL AND evidence_snapshot != ""')
    has_snap = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM bets WHERE evidence_snapshot IS NULL OR evidence_snapshot = ""')
    no_snap = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM bets WHERE match_id IN ("-1", "mock_12345")')
    mock_matches = c.fetchone()[0]
    
    # Excluidos (simulamos para la UI)
    c.execute('SELECT * FROM bets WHERE match_id IN ("-1", "mock_12345") OR evidence_snapshot IS NULL OR evidence_snapshot = ""')
    excluidos = [dict(r) for r in c.fetchall()]
    conn.close()
    
    return {
        "total": total,
        "status_counts": status_counts,
        "has_snap": has_snap,
        "no_snap": no_snap,
        "mock_matches": mock_matches,
        "excluidos": excluidos
    }
'''

content = content.replace('@app.post("/api/autotune/run")', new_endpoint + '\n@app.post("/api/autotune/run")')
with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
