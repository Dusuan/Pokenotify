import os
import logging
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("Pokenotify")


@dataclass
class Config:
    """Configuración centralizada cargada desde variables de entorno."""

    # 1. Telegram (100% Plan Continuo Gratuito - Recomendado)
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    # 2. Discord Webhook (100% Plan Continuo Gratuito)
    discord_webhook_url: str = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

    # 3. CallMeBot WhatsApp (100% Gratuito para uso personal)
    callmebot_phone: str = os.getenv("CALLMEBOT_PHONE", "").strip()
    callmebot_apikey: str = os.getenv("CALLMEBOT_APIKEY", "").strip()

    # 4. Twilio WhatsApp (Opcional / De pago tras prueba)
    twilio_sid: str = os.getenv("TWILIO_SID", "").strip()
    twilio_auth: str = os.getenv("TWILIO_AUTH", "").strip()
    twilio_from: str = os.getenv("TWILIO_FROM", "").strip()
    twilio_to: str = os.getenv("TWILIO_TO", "").strip()

    # Parámetros del monitor
    check_interval: int = int(os.getenv("CHECK_INTERVAL_SECONDS", "90"))
    max_msrp_price: float = float(os.getenv("MAX_MSRP_PRICE_MXN", "1600.0"))
    amazon_asins: List[str] = None

    def __post_init__(self):
        raw_asins = os.getenv("AMAZON_ASINS", "B0CQV49Z5X,B0DFZ2M1R6")
        self.amazon_asins = [asin.strip() for asin in raw_asins.split(",") if asin.strip()]

    def has_any_alert_channel(self) -> bool:
        """Determina si al menos un canal de notificación está activo."""
        return bool(
            (self.telegram_bot_token and self.telegram_chat_id)
            or self.discord_webhook_url
            or (self.callmebot_phone and self.callmebot_apikey)
            or (self.twilio_sid and self.twilio_auth and self.twilio_to)
        )


config = Config()
