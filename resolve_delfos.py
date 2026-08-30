import sys
import datetime
sys.path.append('backend')
from data_engine import get_db_connection
from api_football_engine import get_fixture_details

def main():
    conn = get_db_connection()
    cursor = conn.cursor()
    hoy_str = datetime.datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT id, fixture_id, pick FROM delfos_picks WHERE resultado IS NULL AND fecha < ?", (hoy_str,))
    picks_pendientes = cursor.fetchall()
    if not picks_pendientes:
        print("No hay picks pendientes de resolver.")
        return
    resolved_count = 0
    for row in picks_pendientes:
        pick_id = row['id']
        fixture_id = row['fixture_id']
        pick_name = row['pick']
        details = get_fixture_details(fixture_id)
        if not details: continue
        status = details.get('status', {}).get('short', '')
        if status not in ['FT', 'AET', 'PEN']: continue
        goals = details.get('goals', {})
        gh = goals.get('home')
        ga = goals.get('away')
        if gh is None or ga is None: continue
        total_goals = gh + ga
        es_correcto = 0
        if pick_name == 'Home' and gh > ga: es_correcto = 1
        elif pick_name == 'Draw' and gh == ga: es_correcto = 1
        elif pick_name == 'Away' and gh < ga: es_correcto = 1
        elif pick_name == 'Over 1.5' and total_goals > 1.5: es_correcto = 1
        elif pick_name == 'Over 2.5' and total_goals > 2.5: es_correcto = 1
        elif pick_name == 'Over 0.5' and total_goals > 0.5: es_correcto = 1
        elif pick_name == 'Draw No Bet Home':
            if gh > ga: es_correcto = 1
            elif gh == ga: es_correcto = -1
        elif pick_name == 'Draw No Bet Away':
            if gh < ga: es_correcto = 1
            elif gh == ga: es_correcto = -1
        elif pick_name == 'Double Chance 1X' and gh >= ga: es_correcto = 1
        elif pick_name == 'Double Chance X2' and gh <= ga: es_correcto = 1
        elif pick_name == 'Double Chance 12' and gh != ga: es_correcto = 1
        resultado_str = f\"{gh}-{ga}\"
        cursor.execute("UPDATE delfos_picks SET resultado = ?, es_correcto = ?, goles_home = ?, goles_away = ? WHERE id = ?", (resultado_str, es_correcto, gh, ga, pick_id))
        resolved_count += 1
    conn.commit()
    conn.close()
    print(f\"Resueltos {resolved_count} picks de Delfos.\")

if __name__ == '__main__':
    main()