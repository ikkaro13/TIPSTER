# -*- coding: utf-8 -*-
import os
import json
import sqlite3
import subprocess

files_to_dump = [
    'backend/main.py', 'backend/analytics.py', 'backend/engine/hermes.py', 'backend/engine/rules.py',
    'backend/portfolio_manager.py', 'backend/ml_engine.py', 'backend/athena_engine.py', 'backend/autopsy_engine.py',
    'backend/odds_connector.py', 'backend/api_football_engine.py', 'backend/sofascore_scraper.py', 'backend/data_engine.py',
    'backend/services/historical_context_service.py', 'backend/autotune.py', 'backend/train_model.py',
    'backend/telegram_bot.py', 'radar_delfos.py', 'radar_argos.py'
]

with open('AUDIT_PACKAGE.md', 'w', encoding='utf-8') as out:
    out.write('# PAQUETE DE AUDITORIA TIPSTER / ATHENA\n\n')
    
    out.write('## 1. CONTENIDO COMPLETO DE ARCHIVOS CLAVE\n\n')
    for f in files_to_dump:
        out.write(f'### {f}\n`python\n')
        if os.path.exists(f):
            with open(f, 'r', encoding='utf-8', errors='replace') as fd:
                out.write(fd.read())
        else:
            out.write(f'# NOT FOUND: {f}')
        out.write('\n`\n\n')
        
    out.write('## 2. ESQUEMA DE BASE DE DATOS\n\n`sql\n')
    if os.path.exists('backend/tipster.db'):
        conn = sqlite3.connect('backend/tipster.db')
        c = conn.cursor()
        for row in c.execute("SELECT sql FROM sqlite_master WHERE type='table'").fetchall():
            if row[0]: out.write(row[0] + ';\n')
        out.write('\n--- TABLE COUNTS ---\n')
        tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        for t in tables:
            out.write(f'{t}: {c.execute("SELECT COUNT(*) FROM "+t).fetchone()[0]} rows\n')
    out.write('`\n\n')
    
    out.write('## 3. CONFIGURACION Y PARAMETROS ACTUALES\n\n')
    conf_files = ['backend/tuning_params.json', 'docker-compose.yml', 'backend/requirements.txt']
    for cf in conf_files:
        out.write(f'### {cf}\n`\n')
        if os.path.exists(cf):
            with open(cf, 'r', encoding='utf-8', errors='replace') as f:
                out.write(f.read())
        else:
            out.write('NOT FOUND')
        out.write('\n`\n\n')
    
    out.write('### backend/team_stats_db.json (Primeras 5 entradas)\n`json\n')
    if os.path.exists('backend/team_stats_db.json'):
        with open('backend/team_stats_db.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
            keys = list(db.keys())
            sample = {k: db[k] for k in keys[:5]}
            out.write(f'TOTAL TEAMS: {len(keys)}\n')
            out.write(json.dumps(sample, indent=2))
    out.write('\n`\n\n')
    
    out.write('## 4. VARIABLES DE ENTORNO Y CLAVES\n')
    out.write('Variables detectadas (solo nombres): API_BASE, API_KEY, API_URL, current_key, d_key, TELEGRAM_TOKEN\n\n')
    
    out.write('## 5. HISTORIAL DE CAMBIOS RECIENTES\n`	ext\n')
    try:
        log_out = subprocess.check_output(['git', 'log', '--oneline', '-20'], text=True)
        out.write(log_out + '\n')
        diff_out = subprocess.check_output(['git', 'diff', 'HEAD~5', 'HEAD', '--stat'], text=True)
        out.write(diff_out)
    except Exception as e:
        out.write(str(e))
    out.write('\n`\n\n')
    
    out.write('## 6. METRICAS DE RENDIMIENTO\n`\nError: La base de datos de portfolio no esta inicializada o la tabla no existe aun.\n`\n\n')
    
    out.write('## 7. ESTRUCTURA DE ARCHIVOS ACTUALIZADA\n`\n')
    for root, dirs, files in os.walk('.'):
        if 'node_modules' in root or '.git' in root or '.next' in root: continue
        for name in files:
            if name.endswith('.py') or name.endswith('.tsx') or name.endswith('.json'):
                out.write(os.path.join(root, name).replace('\\\\', '/') + '\n')
    out.write('`\n\n')
print('Audit Package written to AUDIT_PACKAGE.md')