import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_func = '''def api_place_bet(req: BetRequest):
    if not req.evidence_snapshot:
        print(f"[WARNING] Bet sin evidence_snapshot: {req.match_id} - {req.pick}")
    return place_bet(req.match_id, req.pick, req.odds, req.stake, req.evidence_snapshot, req.bet_type)'''

new_func = '''def api_place_bet(req: BetRequest):
    import json
    snap_str = req.evidence_snapshot
    if not snap_str:
        print(f"[WARNING] Bet sin evidence_snapshot: {req.match_id} - {req.pick}")
    else:
        try:
            snap = json.loads(snap_str)
            if 'hermes' not in snap or 'home' not in snap:
                snap_str = ""
                print("[WARNING] evidence_snapshot invalido, marcando sin evidencia")
        except Exception:
            snap_str = ""
            print("[WARNING] evidence_snapshot corrupto, marcando sin evidencia")
            
    res = place_bet(req.match_id, req.pick, req.odds, req.stake, snap_str, req.bet_type)
    if snap_str == "":
        res['message'] = res.get('message', '') + " (WARNING: Apuesta guardada SIN evidencia analizable)"
    return res'''

content = content.replace(old_func, new_func)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
