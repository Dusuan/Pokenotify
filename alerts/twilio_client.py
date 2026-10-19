import logging
from typing import Optional
from config import config

logger = logging.getLogger("Pokenotify.Alerts")

# Cliente Twilio inicializado perezosamente (lazy loading)
_twilio_client = None


def _get_twilio_client():
    global _twilio_client
    if _twilio_client is None:
        try:
            from twilio.rest import Client
            if config.validate_twilio():
                _twilio_client = Client(config.twilio_sid, config.twilio_auth)
        except Exception as e:
            logger.error(f"Error inicializando cliente de Twilio: {e}")
            _twilio_client = None
    return _twilio_client


def send_whatsapp(message_text: str, custom_to: Optional[str] = None) -> bool:
    """
    Envía un mensaje de alerta a través de Twilio WhatsApp API.
    
    :param message_text: Contenido del mensaje a enviar.
    :param custom_to: Número destinatario opcional. Si no se provee, usa config.twilio_to.
    :return: True si se envió correctamente o en dry-run, False en caso de error.
    """
    to_number = custom_to or config.twilio_to
    from_number = config.twilio_from

    # Si falta configuración, simular en logs para no interrumpir el flujo
    if not config.twilio_sid or not config.twilio_auth or not to_number:
        logger.warning(
            f"[SIMULACIÓN WHATSAPP] Destinatario: {to_number or 'NO CONFIGURADO'}\n"
            f"Mensaje:\n{message_text}"
        )
        return True

    client = _get_twilio_client()
    if not client:
        logger.error("Cliente de Twilio no disponible. No se pudo enviar el mensaje.")
        return False

    try:
        from_formatted = from_number if from_number.startswith("whatsapp:") else f"whatsapp:{from_number}"
        to_formatted = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"

        msg = client.messages.create(
            body=message_text,
            from_=from_formatted,
            to=to_formatted
        )
        logger.info(f"Notificación de WhatsApp enviada exitosamente. SID: {msg.sid}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar notificación por WhatsApp: {e}")
        return False
