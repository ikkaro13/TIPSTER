import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_cache = '''_LAB_STATS_CACHE = {"data": None, "timestamp": 0}
LAB_CACHE_TTL = 3600 # 1 hora

def get_cached_lab_stats():
    import time
    now = time.time()
    if _LAB_STATS_CACHE["data"] is None or (now - _LAB_STATS_CACHE["timestamp"]) > LAB_CACHE_TTL:
        result = portfolio_lab()
        _LAB_STATS_CACHE["data"] = result.get("por_mercado", {})
        _LAB_STATS_CACHE["timestamp"] = now
    return _LAB_STATS_CACHE["data"]'''

good_cache = '''        _LAB_STATS_CACHE = {"data": None, "timestamp": 0}
        LAB_CACHE_TTL = 3600 # 1 hora

        def get_cached_lab_stats():
            import time
            now = time.time()
            if _LAB_STATS_CACHE["data"] is None or (now - _LAB_STATS_CACHE["timestamp"]) > LAB_CACHE_TTL:
                result = portfolio_lab()
                _LAB_STATS_CACHE["data"] = result.get("por_mercado", {})
                _LAB_STATS_CACHE["timestamp"] = now
            return _LAB_STATS_CACHE["data"]'''

content = content.replace(bad_cache, good_cache)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
