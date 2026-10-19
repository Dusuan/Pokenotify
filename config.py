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
    twilio_sid: str = os.getenv("TWILIO_SID", "").strip()
    twilio_auth: str = os.getenv("TWILIO_AUTH", "").strip()
    twilio_from: str = os.getenv("TWILIO_FROM", "").strip()
    twilio_to: str = os.getenv("TWILIO_TO", "").strip()
    check_interval: int = int(os.getenv("CHECK_INTERVAL_SECONDS", "90"))
    max_msrp_price: float = float(os.getenv("MAX_MSRP_PRICE_MXN", "1600.0"))
    amazon_asins: List[str] = None

    def __post_init__(self):
        raw_asins = os.getenv("AMAZON_ASINS", "B0CQV49Z5X,B0DFZ2M1R6")
        self.amazon_asins = [asin.strip() for asin in raw_asins.split(",") if asin.strip()]

    def validate_twilio(self) -> bool:
        """Verifica si las credenciales de Twilio están configuradas."""
        missing = []
        if not self.twilio_sid:
            missing.append("TWILIO_SID")
        if not self.twilio_auth:
            missing.append("TWILIO_AUTH")
        if not self.twilio_from:
            missing.append("TWILIO_FROM")
        if not self.twilio_to:
            missing.append("TWILIO_TO")

        if missing:
            logger.warning(
                f"Variables de Twilio incompletas ({', '.join(missing)}). "
                "Las alertas por WhatsApp se simularán en modo log."
            )
            return False
        return True


config = Config()
