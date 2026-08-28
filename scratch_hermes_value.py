with open('backend/engine/hermes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if '"Under 2.5 Goles (Partido Cerrado)": "under_2_5",' in line:
        new_lines.append('            "Doble Oportunidad (1X)": "dc_1x",\n')
        new_lines.append('            "Doble Oportunidad (X2)": "dc_x2",\n')
        new_lines.append('            "DNB (Local)": "dnb_home",\n')
        new_lines.append('            "DNB (Visita)": "dnb_away",\n')

with open('backend/engine/hermes.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
