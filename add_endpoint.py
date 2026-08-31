import os
import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_endpoint = '''
@app.get("/api/portfolio/audit-log")
def get_audit_log(limit: int = 50):
    from portfolio_manager import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bankroll_audit_log ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"audit_log": rows}
'''

if '/api/portfolio/audit-log' not in content:
    content = content.replace('@app.post("/api/portfolio/reset")', new_endpoint + '\n@app.post("/api/portfolio/reset")')
    
with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
