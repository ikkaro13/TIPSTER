import sys
import datetime
import asyncio
sys.path.append('backend')
from main import scan_day_for_value_bets
from telegram_bot import send_telegram_alert

# Nombre Clave: PROYECTO ARGOS (El de los 100 ojos que todo lo ve)

today = datetime.datetime.now().strftime("%Y-%m-%d")
print(f"Iniciando PROYECTO ARGOS para el {today}")

send_telegram_alert(f"👁️ <b>PROYECTO ARGOS INICIADO</b> 👁️\n\nFecha: {today}\nEscaneando matriz de cuotas asiáticas...")

try:
    results = scan_day_for_value_bets(today)
    value_bets = results.get("value_bets", [])
    
    if not value_bets:
        send_telegram_alert("📉 <b>Reporte ARGOS:</b> No se encontraron ventajas matemáticas (Edges) para el día de hoy.")
    else:
        msg = f"🎯 <b>ARGOS DETECTÓ {len(value_bets)} OPORTUNIDADES</b> 🎯\n\n"
        for idx, bet in enumerate(value_bets[:10]):
            msg += f"⚔️ <b>{bet['home_team']} vs {bet['away_team']}</b>\n"
            msg += f"👉 Pick: <b>{bet['pick']}</b>\n"
            msg += f"📊 Probabilidad: {bet['prob']}%\n"
            msg += f"💰 Cuota: {bet['odds']} ({bet['bookie']})\n"
            msg += f"⚡ EDGE: +{bet['edge']}%\n"
            msg += f"🧠 Riesgo: {bet.get('type', 'Francotirador')}\n\n"
            
        if len(value_bets) > 10:
            msg += f"...y {len(value_bets) - 10} más.\n"
            
        send_telegram_alert(msg)
        print("Alertas enviadas a Telegram exitosamente.")
except Exception as e:
    send_telegram_alert(f"⚠️ Error en ARGOS: {str(e)}")
    print(f"Error: {e}")
