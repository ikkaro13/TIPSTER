# -*- coding: utf-8 -*-
import sqlite3
import json
import re

conn = sqlite3.connect('backend/tipster.db')
c = conn.cursor()

c.execute("SELECT id, pick, evidence_snapshot FROM bets WHERE LOWER(pick) LIKE '%doble oportunidad%'")
bets = c.fetchall()

migrated = 0
for bet_id, pick, snap_json in bets:
    try:
        snap = json.loads(snap_json) if snap_json else {}
    except Exception:
        snap = {}
        
    p = pick.lower()
    match = re.search(r'pivote seguro:\s*\+?([\d.]+)%', p)
    val = float(match.group(1)) if match else 99.0
    
    # We always ensure the structure exists
    if 'hermes' not in snap:
        snap['hermes'] = {'confidence': 0, 'value_pick': pick, 'safe_pick': pick}
        
    if "(x2)" in p or "dc_x2" in p:
        snap["dc_2x"] = val
    elif "(1x)" in p or "dc_1x" in p:
        snap["dc_1x"] = val
        
    c.execute("UPDATE bets SET evidence_snapshot = ? WHERE id = ?", (json.dumps(snap), bet_id))
    migrated += 1

conn.commit()
conn.close()
print(f"Migrated {migrated} bets.")
