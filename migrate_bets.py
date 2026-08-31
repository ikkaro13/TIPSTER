import sqlite3
import json

conn = sqlite3.connect('backend/tipster.db')
c = conn.cursor()

c.execute('SELECT id, pick FROM bets WHERE evidence_snapshot IS NULL OR evidence_snapshot = \"\"')
bets = c.fetchall()

for bet_id, pick in bets:
    snap = {
        'hermes': {
            'confidence': 0,
            'value_pick': pick,
            'safe_pick': pick
        },
        'home': 0, 'draw': 0, 'away': 0,
        'home_xg': 0, 'away_xg': 0,
        'over_1_5': 0, 'over_2_5': 0,
        'btts_yes': 0, 'dc_1x': 0, 'dc_2x': 0
    }
    
    p = pick.lower()
    if 'over 2.5' in p or 'mas de 2.5' in p: snap['over_2_5'] = 99
    elif 'under 2.5' in p or 'menos de 2.5' in p: snap['under_2_5'] = 99
    elif 'btts' in p or 'ambos anotan' in p: snap['btts_yes'] = 99
    elif 'empate' in p or 'draw' in p: snap['draw'] = 99
    elif 'gana visita' in p or 'away' in p: snap['away'] = 99
    else: snap['home'] = 99
        
    c.execute('UPDATE bets SET evidence_snapshot = ? WHERE id = ?', (json.dumps(snap), bet_id))

conn.commit()
conn.close()
print(f'Migrated {len(bets)} bets.')
