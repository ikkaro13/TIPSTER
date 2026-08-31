import requests
import os
from dotenv import load_dotenv
load_dotenv()
VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() == "true"
import logging

# Configuración del Bot (Datos proporcionados por el usuario)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Variable global para evitar hacer spam de la misma alerta repetidas veces
_sent_alerts = set()

def send_telegram_alert(message: str, alert_id: str = None):
    """
    Envía un mensaje de alerta a través del bot de Telegram de ATHENA.
    """
    global _sent_alerts
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("No se pudo enviar la alerta por Telegram. Token o Chat ID faltantes.")
        return False
        
    # Evitar spam de la misma alerta
    if alert_id:
        if alert_id in _sent_alerts:
            return True # Ya se envió anteriormente
        _sent_alerts.add(alert_id)
        
        # Limpiar caché si crece mucho
        if len(_sent_alerts) > 1000:
            _sent_alerts.clear()
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5, verify=VERIFY_SSL)
        response.raise_for_status()
        return True
    except Exception as e:
        logging.error(f"Error al enviar mensaje por Telegram: {e}")
        return False

# Prueba de conexión rápida
if __name__ == "__main__":
    success = send_telegram_alert("🤖 <b>ATHENA Online</b>: Sistema de telecomunicaciones activado exitosamente. Recibiendo señales.")
    if success:
        print("Mensaje de prueba enviado exitosamente a Telegram.")
    else:
        print("Fallo al enviar el mensaje.")

