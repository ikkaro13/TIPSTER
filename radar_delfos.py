import sys
import datetime
import asyncio
import time
sys.path.append('backend')
from main import scan_day_for_value_bets
from telegram_bot import send_telegram_alert
import odds_connector

if hasattr(odds_connector, 'ODDS_DATE_CACHE'):
    odds_connector.ODDS_DATE_CACHE.clear()

now = datetime.datetime.now()
if len(sys.argv) > 1:
    target_date = sys.argv[1]
else:
    if now.hour >= 19:
        target_date = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        target_date = now.strftime("%Y-%m-%d")

print(f"Iniciando ORÁCULO DE DELFOS para el {target_date}")

send_telegram_alert(f"🔮 <b>ORÁCULO DE DELFOS INICIADO</b> 🔮\n\nFecha: {target_date}\nEscaneando matriz de cuotas asiáticas (Buscando DNB, Hándicaps y Medios Tiempos)...")
time.sleep(1)

try:
    results = scan_day_for_value_bets(target_date)
    value_bets = results.get("value_bets", [])
    
    if not value_bets:
        send_telegram_alert(f"🏜️ <b>Reporte de Delfos ({target_date}):</b> Ningún partido superó los filtros matemáticos. El algoritmo recomienda descansar y proteger el bankroll.")
    else:
        from data_engine import save_delfos_pick
        import json
        
        # Guardar picks en DB
        for bet in value_bets:
            evidence_str = json.dumps(bet.get("insights", {}))
            save_delfos_pick(
                fixture_id=bet['fixture_id'],
                home_team=bet['home_team'],
                away_team=bet['away_team'],
                liga=bet['league'],
                pick=bet['pick'],
                probabilidad=bet['prob'],
                cuota=bet['odds'],
                edge=bet['edge'],
                tipo=bet.get('type', 'Francotirador'),
                evidence_snapshot=evidence_str
            )
            
        value_bets.sort(key=lambda x: float(x.get('edge', 0)), reverse=True)
        best_pick = value_bets[0]
        
        # COMBO DELFOS (Over 1.5)
        over_15_picks = [b for b in value_bets if b['pick'] == 'Over 1.5' and b['prob'] >= 65]
        over_15_picks.sort(key=lambda x: float(x.get('prob', 0)), reverse=True)
        
        combo_msg = ""
        if len(over_15_picks) >= 2:
            p1, p2 = over_15_picks[0], over_15_picks[1]
            cuota_combo = round(p1['odds'] * p2['odds'], 2)
            prob_combo = round((p1['prob'] / 100.0) * (p2['prob'] / 100.0) * 100, 1)
            edge_combo = round(((prob_combo / 100.0) * cuota_combo - 1) * 100, 2)
            
            if edge_combo > 5.0: # Edge mnimo para mandar combo
                combo_msg = f"⚡ <b>COMBO DELFOS DEL DÍA</b> ⚡\n\n"
                combo_msg += f"1️⃣ {p1['home_team']} vs {p1['away_team']} (Over 1.5 @ {p1['odds']})\n"
                combo_msg += f"2️⃣ {p2['home_team']} vs {p2['away_team']} (Over 1.5 @ {p2['odds']})\n"
                combo_msg += f"📊 <b>Cuota combinada: {cuota_combo}</b>\n"
                combo_msg += f"🎯 Probabilidad: {prob_combo}%\n"
                combo_msg += f"📈 EDGE: +{edge_combo}%\n"
                combo_msg += f"-----------------------------------\n\n"
        
        # MENSAJE 1: Cabecera y el Mejor Pick
        msg_header = f"🏆 <b>DELFOS ENCONTRÓ {len(value_bets)} OPORTUNIDADES DE VALOR</b> 🏆\n\n"
        if combo_msg:
            msg_header += combo_msg
            
        msg_header += f"🔥 <b>EL MEJOR PICK DEL DÍA</b> 🔥\n"
        msg_header += f"⚽ <b>{best_pick['home_team']} vs {best_pick['away_team']}</b>\n"
        msg_header += f"🎯 Pick: <b>{best_pick['pick']}</b>\n"
        msg_header += f"📊 Probabilidad: {best_pick['prob']}%\n"
        msg_header += f"💰 Cuota: {best_pick['odds']} ({best_pick.get('bookmaker', 'API')})\n"
        msg_header += f"📈 EDGE: +{best_pick['edge']}%\n"
        msg_header += f"🧠 Modalidad: {best_pick.get('type', 'Francotirador')}\n"
        msg_header += f"-----------------------------------\n\n"
        send_telegram_alert(msg_header)
        time.sleep(1)
        
        # Enviar los demas en lotes de 10 para no romper el limite de Telegram
        current_msg = ""
        batch_count = 0
        
        for idx, bet in enumerate(value_bets[1:]):
            current_msg += f"⚽ <b>{bet['home_team']} vs {bet['away_team']}</b>\n"
            current_msg += f"🎯 Pick: <b>{bet['pick']}</b>\n"
            current_msg += f"📊 Probabilidad: {bet['prob']}%\n"
            current_msg += f"💰 Cuota: {bet['odds']} ({bet.get('bookmaker', 'API')})\n"
            current_msg += f"📈 EDGE: +{bet['edge']}%\n"
            current_msg += f"🧠 Modalidad: {bet.get('type', 'Francotirador')}\n\n"
            
            batch_count += 1
            if batch_count == 10:
                send_telegram_alert(current_msg)
                time.sleep(1.5) # Pausa para evitar rate limit de Telegram
                current_msg = ""
                batch_count = 0
                
        if current_msg:
            send_telegram_alert(current_msg)
            
        print("Alertas enviadas a Telegram exitosamente en partes.")
except Exception as e:
    send_telegram_alert(f"❌ Error en el Oráculo: {str(e)}")
    print(f"Error: {e}")
