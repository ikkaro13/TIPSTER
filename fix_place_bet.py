import os
import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_func = '''def api_place_bet(req: BetRequest):
    return place_bet(req.match_id, req.pick, req.odds, req.stake, req.evidence_snapshot, req.bet_type)'''

new_func = '''def api_place_bet(req: BetRequest):
    if not req.evidence_snapshot:
        print(f"[WARNING] Bet sin evidence_snapshot: {req.match_id} - {req.pick}")
    return place_bet(req.match_id, req.pick, req.odds, req.stake, req.evidence_snapshot, req.bet_type)'''

content = content.replace(old_func, new_func)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
