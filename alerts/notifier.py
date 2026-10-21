import urllib.parse
import logging
import requests
from typing import Optional
from config import config
from .twilio_client import send_whatsapp as send_twilio_whatsapp

logger = logging.getLogger("Pokenotify.Alerts")


def send_telegram_alert(message_text: str, buttons: Optional[list] = None) -> bool:
    """Envía alerta vía Telegram Bot API con soporte para Inline Keyboard (100% Plan Continuo Gratuito)."""
    if not config.telegram_bot_token or not config.telegram_chat_id:
        return False

    url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": config.telegram_chat_id,
        "text": message_text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }

    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}

    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            logger.info("Alerta despachada exitosamente por Telegram.")
            return True
        else:
            logger.error(f"Error Telegram API (HTTP {res.status_code}): {res.text}")
            return False
    except Exception as e:
        logger.error(f"Excepción al conectar con Telegram: {e}")
        return False


def send_discord_alert(message_text: str) -> bool:
    """Envía alerta vía Discord Webhook (100% Plan Continuo Gratuito)."""
    if not config.discord_webhook_url:
        return False

    payload = {"content": message_text}
    try:
        res = requests.post(config.discord_webhook_url, json=payload, timeout=10)
        if res.status_code in (200, 204):
            logger.info("Alerta despachada exitosamente por Discord Webhook.")
            return True
        else:
            logger.error(f"Error Discord Webhook (HTTP {res.status_code}): {res.text}")
            return False
    except Exception as e:
        logger.error(f"Excepción al conectar con Discord: {e}")
        return False


def send_callmebot_whatsapp(message_text: str) -> bool:
    """Envía alerta a WhatsApp vía CallMeBot API (100% Gratuito para uso personal)."""
    if not config.callmebot_phone or not config.callmebot_apikey:
        return False

    encoded_text = urllib.parse.quote(message_text)
    url = (
        f"https://api.callmebot.com/whatsapp.php?"
        f"phone={config.callmebot_phone}&text={encoded_text}&apikey={config.callmebot_apikey}"
    )

    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            logger.info("Alerta despachada exitosamente por CallMeBot WhatsApp.")
            return True
        else:
            logger.error(f"Error CallMeBot (HTTP {res.status_code}): {res.text}")
            return False
    except Exception as e:
        logger.error(f"Excepción al conectar con CallMeBot: {e}")
        return False


def dispatch_alert(message_text: str, buttons: Optional[list] = None) -> bool:
    """
    Despacha la alerta a todos los canales gratuitos y configurados.
    Si no hay ninguno configurado, simula la alerta en logs.
    """
    sent_any = False

    # 1. Telegram Bot (Gratis de por vida) - Soporta botones interactivos Inline Keyboard
    if config.telegram_bot_token and config.telegram_chat_id:
        if send_telegram_alert(message_text, buttons=buttons):
            sent_any = True

    # 2. Discord Webhook (Gratis de por vida)
    if config.discord_webhook_url:
        if send_discord_alert(message_text):
            sent_any = True

    # 3. CallMeBot WhatsApp (Gratis para uso personal)
    if config.callmebot_phone and config.callmebot_apikey:
        if send_callmebot_whatsapp(message_text):
            sent_any = True

    # 4. Twilio WhatsApp (Si el usuario configuró credenciales)
    if config.twilio_sid and config.twilio_auth and config.twilio_to:
        if send_twilio_whatsapp(message_text):
            sent_any = True

    # Fallback si ningún canal está configurado
    if not sent_any and not config.has_any_alert_channel():
        logger.warning(
            f"[SIMULACIÓN ALERTA - SIN CANALES CONFIGURADOS]\n"
            f"Configura TELEGRAM_BOT_TOKEN o CALLMEBOT en .env para recibir alertas reales gratis.\n"
            f"Mensaje:\n{message_text}"
        )
        return True

    return sent_any
