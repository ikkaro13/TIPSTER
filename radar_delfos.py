import sys
import datetime
import asyncio
sys.path.append('backend')
from main import scan_day_for_value_bets
from telegram_bot import send_telegram_alert
import odds_connector

# Forzamos borrar el cache de cuotas para que traiga datos 100% frescos (puede que las casas ya abrieran más mercados)
if hasattr(odds_connector, 'ODDS_DATE_CACHE'):
    odds_connector.ODDS_DATE_CACHE.clear()

today = datetime.datetime.now().strftime("%Y-%m-%d")
print(f"Iniciando ORÁCULO DE DELFOS para el {today}")

send_telegram_alert(f"🏛️ <b>ORÁCULO DE DELFOS INICIADO</b> 🏛️\n\nFecha: {today}\nEscaneando matriz de cuotas asiáticas (Buscando DNB, Hándicaps y Medios Tiempos)...")

try:
    results = scan_day_for_value_bets(today)
    value_bets = results.get("value_bets", [])
    
    if not value_bets:
        send_telegram_alert("📉 <b>Reporte de Delfos:</b> Los dioses no favorecen ningún mercado hoy. Cero Edges encontrados.")
    else:
        msg = f"⚡ <b>DELFOS ENCONTRÓ {len(value_bets)} OPORTUNIDADES DE VALOR</b> ⚡\n\n"
        for idx, bet in enumerate(value_bets[:15]):
            msg += f"⚔️ <b>{bet['home_team']} vs {bet['away_team']}</b>\n"
            msg += f"👉 Pick: <b>{bet['pick']}</b>\n"
            msg += f"📊 Probabilidad: {bet['prob']}%\n"
            msg += f"💰 Cuota: {bet['odds']} ({bet['bookie']})\n"
            msg += f"🔥 EDGE: +{bet['edge']}%\n"
            msg += f"🧠 Modalidad: {bet.get('type', 'Francotirador')}\n\n"
            
        if len(value_bets) > 15:
            msg += f"...y {len(value_bets) - 15} predicciones más.\n"
            
        send_telegram_alert(msg)
        print("Alertas enviadas a Telegram exitosamente.")
except Exception as e:
    send_telegram_alert(f"⚠️ Error en el Oráculo: {str(e)}")
    print(f"Error: {e}")
