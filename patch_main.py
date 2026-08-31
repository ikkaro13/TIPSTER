import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add Cache Logic
cache_code = '''
_LAB_STATS_CACHE = {"data": None, "timestamp": 0}
LAB_CACHE_TTL = 3600 # 1 hora

def get_cached_lab_stats():
    import time
    now = time.time()
    if _LAB_STATS_CACHE["data"] is None or (now - _LAB_STATS_CACHE["timestamp"]) > LAB_CACHE_TTL:
        result = portfolio_lab()
        _LAB_STATS_CACHE["data"] = result.get("por_mercado", {})
        _LAB_STATS_CACHE["timestamp"] = now
    return _LAB_STATS_CACHE["data"]
'''

# Put it before def check_edge
content = content.replace('def check_edge(', cache_code + '\n\ndef check_edge(')

# 2. Update check_edge
# From: required_edge = MIN_EDGE_PER_MARKET.get(pick_name, DEFAULT_MIN_EDGE)
# To: 
replacement = '''lab_stats = get_cached_lab_stats()
    from market_rules import get_min_edge
    required_edge = get_min_edge(pick_name, apply_tuning=True, lab_stats=lab_stats)
    if required_edge is None:
        return {"value": False, "edge": 0, "required": 0, "msg": "SHADOW MODE - Evaluando"}'''
content = re.sub(r'required_edge = MIN_EDGE_PER_MARKET\.get\(pick_name, DEFAULT_MIN_EDGE\)', replacement, content)

# 3. Update scan_day_for_value_bets
# From: required_edge = MIN_EDGE_PER_MARKET.get(pick_name, DEFAULT_MIN_EDGE)
# To:
replacement_scan = '''lab_stats = get_cached_lab_stats()
                from market_rules import get_min_edge
                required_edge = get_min_edge(pick_name, apply_tuning=True, lab_stats=lab_stats)
                if required_edge is None:
                    continue'''
content = re.sub(r'required_edge = MIN_EDGE_PER_MARKET\.get\(pick_name, DEFAULT_MIN_EDGE\)', replacement_scan, content)

# 4. Add /api/shadow/status
new_endpoint = '''
@app.get("/api/shadow/status")
def get_shadow_status():
    from market_rules import get_all_shadow_markets, get_shadow_market_progress
    lab_stats = get_cached_lab_stats()
    shadow_markets = get_all_shadow_markets(lab_stats)
    return {
        "shadow_markets": [get_shadow_market_progress(m, lab_stats) for m in shadow_markets]
    }
'''
content = content.replace('@app.get("/api/portfolio/lab")', new_endpoint + '\n@app.get("/api/portfolio/lab")')

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
