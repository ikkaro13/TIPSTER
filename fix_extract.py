# -*- coding: utf-8 -*-
import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r'    def extract_market_from_pick\(pick: str\) -> str:.*?return "Otro"', re.DOTALL)
match = pattern.search(content)

if match:
    new_func = '''    def extract_market_from_pick(pick: str) -> str:
        """Infiere el mercado apostado desde el texto del pick."""
        p = pick.lower()
        if "over 2.5" in p or "m\\u00e1s de 2.5" in p or "mas de 2.5" in p or "m\xe1s de 2.5" in p: return "Over 2.5"
        if "under 2.5" in p or "menos de 2.5" in p: return "Under 2.5"
        if "over 1.5" in p or "m\\u00e1s de 1.5" in p or "mas de 1.5" in p or "m\xe1s de 1.5" in p: return "Over 1.5"
        if "under 1.5" in p or "menos de 1.5" in p: return "Under 1.5"
        if "over 0.5" in p or "m\\u00e1s de 0.5" in p or "mas de 0.5" in p or "m\xe1s de 0.5" in p: return "Over 0.5"
        if "btts" in p or "ambos anotan" in p: return "BTTS"
        if "(x2)" in p or "dc_x2" in p: return "Doble Oportunidad X2"
        if "(1x)" in p or "dc_1x" in p: return "Doble Oportunidad 1X"
        if "doble oportunidad" in p: return "Doble Oportunidad (Sin Especificar)"
        if "draw no bet" in p or "empate no acci" in p or "dnb" in p: return "DNB"
        if "empate" in p or "draw" in p: return "Empate"
        if "gana visita" in p or "away" in p: return "Gana Visita"
        if "pivote seguro" in p or "gana local" in p or "home" in p: return "Gana Local"
        return "Otro"'''
    
    content = content[:match.start()] + new_func + content[match.end():]
else:
    print("Could not find extract_market_from_pick")

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
