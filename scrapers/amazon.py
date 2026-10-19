import logging
import requests
from bs4 import BeautifulSoup
from typing import Optional, List
from config import config
from .models import ScrapedItem
from .utils import get_random_headers, parse_price

logger = logging.getLogger("Pokenotify.Amazon")


class AmazonScraper:
    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()

    def check_asin(self, asin: str) -> Optional[ScrapedItem]:
        """
        Inspecciona un producto en Amazon México por su código ASIN.
        Maneja errores HTTP 403, 503 y detecta páginas de CAPTCHA.
        """
        url = f"https://www.amazon.com.mx/dp/{asin}"
        headers = get_random_headers()

        try:
            response = self.session.get(url, headers=headers, timeout=15)
            
            # Manejo específico de bloqueos WAF / Bot detection
            if response.status_code == 403:
                logger.warning(f"[Amazon 403 Forbidden] Detección anti-bot en ASIN {asin}. Se omitirá en este ciclo.")
                return None
            elif response.status_code == 503:
                logger.warning(f"[Amazon 503 Service Unavailable] Posible CAPTCHA o sobrecarga en ASIN {asin}.")
                return None
            elif response.status_code != 200:
                logger.warning(f"[Amazon HTTP {response.status_code}] Respuesta no exitosa para ASIN {asin}.")
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # Detección de CAPTCHA
            page_title = soup.title.string.strip() if soup.title and soup.title.string else ""
            if "Robot Check" in page_title or "Algo salió mal" in page_title:
                logger.warning(f"[Amazon Bot Challenge] CAPTCHA detectado en ASIN {asin}.")
                return None

            # Extracción del título del producto
            title_elem = soup.select_one("#productTitle")
            title = title_elem.get_text(strip=True) if title_elem else f"Producto Amazon ({asin})"

            # Extracción de disponibilidad
            availability_elem = soup.select_one("#availability")
            availability_text = availability_elem.get_text(strip=True).lower() if availability_elem else ""
            add_to_cart_btn = soup.select_one("#add-to-cart-button")
            buy_now_btn = soup.select_one("#buy-now-button")

            is_out_of_stock = (
                "no disponible por el momento" in availability_text
                or "temporalmente agotado" in availability_text
                or "unavailable" in availability_text
            )
            has_buy_button = bool(add_to_cart_btn or buy_now_btn)
            in_stock = has_buy_button and not is_out_of_stock

            # Extracción del precio
            price_str = ""
            price_elem = (
                soup.select_one("#corePrice_feature_div .a-price .a-offscreen")
                or soup.select_one(".a-price .a-offscreen")
                or soup.select_one("#priceblock_ourprice")
                or soup.select_one("#priceblock_dealprice")
            )
            if price_elem:
                price_str = price_elem.get_text(strip=True)

            price_val = parse_price(price_str)

            # Extracción del vendedor (Merchant)
            merchant_elem = soup.select_one("#merchant-info") or soup.select_one("#tabular-buybox")
            seller = merchant_elem.get_text(strip=True) if merchant_elem else "Desconocido"
            if len(seller) > 100:
                seller = seller[:97] + "..."

            # Validación de MSRP
            is_msrp = False
            if in_stock and price_val is not None:
                is_msrp = price_val <= config.max_msrp_price

            item = ScrapedItem(
                store="Amazon México",
                title=title,
                price=price_val,
                price_str=price_str or "Consultar en enlace",
                url=url,
                in_stock=in_stock,
                is_msrp=is_msrp,
                seller=seller,
                notes=f"ASIN: {asin}"
            )

            logger.info(
                f"[Amazon] ASIN {asin}: {'EN STOCK' if in_stock else 'Agotado'} | "
                f"Precio: {price_str or 'N/A'} | MSRP válido: {is_msrp}"
            )
            return item

        except requests.RequestException as e:
            logger.error(f"[Amazon Request Error] Excepción al consultar ASIN {asin}: {e}")
            return None


def scan_amazon() -> List[ScrapedItem]:
    """Escanea la lista de ASINs configurados en Amazon México."""
    scraper = AmazonScraper()
    found_items = []
    for asin in config.amazon_asins:
        item = scraper.check_asin(asin)
        if item and item.in_stock and item.is_msrp:
            found_items.append(item)
    return found_items
