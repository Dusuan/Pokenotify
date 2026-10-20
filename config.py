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
    msrp_cushion_percent: float = float(os.getenv("MSRP_CUSHION_PERCENT", "25.0"))
    send_startup_test_alert: bool = os.getenv("SEND_STARTUP_TEST_ALERT", "true").strip().lower() in ("true", "1", "yes")
    amazon_asins: List[str] = None
    tcg_keywords: List[str] = None
    tcg_exclude_keywords: List[str] = None

    def __post_init__(self):
        raw_asins = os.getenv("AMAZON_ASINS", "B0CQV49Z5X,B0DFZ2M1R6")
        self.amazon_asins = [asin.strip() for asin in raw_asins.split(",") if asin.strip()]

        # Palabras que identifican cartas Pokémon TCG
        default_tcg = "tcg,carta,cartas,card,cards,elite trainer,etb,booster,sobre,sobres,caja de entrenador,coleccion,colección,lata,tin,baraja,deck,bundle,paquete de mejora,paquete coleccionable"
        raw_tcg = os.getenv("TCG_KEYWORDS", default_tcg)
        self.tcg_keywords = [k.strip().lower() for k in raw_tcg.split(",") if k.strip()]

        # Palabras de productos que NO son cartas (Legos, peluches, ropa, consolas)
        default_exclude = "lego,mega construx,construx,bloks,peluche,plush,videojuego,switch,consola,pijama,mochila,gorra,playera,ropa,figura de accion"
        raw_exclude = os.getenv("TCG_EXCLUDE_KEYWORDS", default_exclude)
        self.tcg_exclude_keywords = [k.strip().lower() for k in raw_exclude.split(",") if k.strip()]

        # Indicadores de idioma Español (ESTRICTAMENTE DESCARTADOS: solo se permiten cartas en Inglés)
        default_spanish = "español,espanol,spanish,idioma español,en español,versión en español,version en espanol,edición en español,edicion en espanol,castellano"
        raw_spanish = os.getenv("SPANISH_LANGUAGE_KEYWORDS", default_spanish)
        self.spanish_keywords = [k.strip().lower() for k in raw_spanish.split(",") if k.strip()]

    def is_tcg_product(self, title: str, extra_text: str = "") -> bool:
        """Determina si un producto es cartas Pokémon TCG y EXCLUSIVAMENTE en idioma INGLÉS."""
        combined = f"{title} {extra_text}".lower()

        # 1. REGLA ESTRICTA: Descartar si está en idioma Español
        for sp in self.spanish_keywords:
            if sp in combined:
                return False

        # 2. Descartar si contiene palabras de productos no deseados (lego, peluche, etc.)
        for exc in self.tcg_exclude_keywords:
            if exc in combined:
                return False

        # 3. Debe mencionar Pokémon
        if "pokemon" not in combined and "pokémon" not in combined:
            return False

        # 4. Debe contener al menos un término específico de cartas / TCG
        for kw in self.tcg_keywords:
            if kw in combined:
                return True

        return False

    def has_any_alert_channel(self) -> bool:
        """Determina si al menos un canal de notificación está activo."""
        return bool(
            (self.telegram_bot_token and self.telegram_chat_id)
            or self.discord_webhook_url
            or (self.callmebot_phone and self.callmebot_apikey)
            or (self.twilio_sid and self.twilio_auth and self.twilio_to)
        )


config = Config()
