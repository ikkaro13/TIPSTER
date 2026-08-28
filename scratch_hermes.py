import re

with open('backend/engine/hermes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Buscamos el market_map y añadimos los nuevos
new_map = '''        market_map = {
            "Gana Local": "home",
            "Empate": "draw",
            "Gana Visita": "away",
            "Mǭs de 1.5 Goles": "over_1_5",
            "Mǭs de 2.5 Goles": "over_2_5",
            "Menos de 3.5 Goles": "under_3_5",
            "Ambos Anotan (S?)": "btts_yes",
            "Ambos Anotan (NO)": "btts_no",
            "Menos de 2.5 Goles": "under_2_5",
            "Doble Oportunidad (1X)": "dc_1x",
            "Doble Oportunidad (X2)": "dc_x2",
            "DNB (Local)": "dnb_home",
            "DNB (Visita)": "dnb_away"
        }'''

# Expresión regular para reemplazar ambos market_map en hermes.py
pattern = r'market_map = \{\s*"Gana Local": "home",.*?\}\s*'
content_new = re.sub(pattern, new_map + '\n        ', content, flags=re.DOTALL)

with open('backend/engine/hermes.py', 'w', encoding='utf-8') as f:
    f.write(content_new)

print("¡hermes.py actualizado!")
