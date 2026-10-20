import re
import logging
import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Tuple
from config import config
from .models import ScrapedItem
from .utils import get_random_headers, parse_price
from .pricing import evaluate_product_msrp

logger = logging.getLogger("Pokenotify.Amazon")


def extract_amazon_seller_info(soup: BeautifulSoup) -> Tuple[str, str, bool]:
    """
    Extrae con precisión el vendedor y remitente en Amazon México.
    Retorna (seller_name, shipper_name, is_official_amazon).
    """
    seller_name = ""
    shipper_name = ""

    # 1. Analizar el buybox tabular (#tabular-buybox)
    tabular_box = soup.select_one("#tabular-buybox, #desktop_buybox, #buybox, #rightCol")
    if tabular_box:
        for row in tabular_box.select(".tabular-buybox-row, div.tabular-buybox-container > div, tr"):
            row_text = row.get_text().strip()
            row_lower = row_text.lower()
            if "vendido por" in row_lower or "sold by" in row_lower:
                val_elem = row.select_one("span.tabular-buybox-text-message, a#sellerProfileTriggerId, a")
                if val_elem:
                    seller_name = val_elem.get_text(strip=True)
                else:
                    parts = re.split(r"vendido por|sold by", row_text, flags=re.IGNORECASE)
                    if len(parts) > 1:
                        seller_name = parts[1].strip()
            elif any(w in row_lower for w in ["envía desde", "envia desde", "envío desde", "remitente", "ships from"]):
                val_elem = row.select_one("span.tabular-buybox-text-message, a")
                if val_elem:
                    shipper_name = val_elem.get_text(strip=True)

    # 2. Si no se encontró en filas, buscar enlace directo del perfil de vendedor
    if not seller_name:
        seller_link = soup.select_one("#sellerProfileTriggerId")
        if seller_link:
            seller_name = seller_link.get_text(strip=True)

    # 3. Analizar el bloque clásico #merchant-info
    merchant_info = soup.select_one("#merchant-info")
    if merchant_info:
        m_text = merchant_info.get_text(strip=True)
        m_lower = m_text.lower()
        if "vendido y enviado por amazon" in m_lower:
            seller_name = "Amazon México"
            shipper_name = "Amazon México"
        elif "vendido por" in m_lower:
            parts = re.split(r"vendido por", m_text, flags=re.IGNORECASE)
            if len(parts) > 1:
                sub = parts[1].split(".")[0].split("y enviado")[0].strip()
                if not seller_name:
                    seller_name = sub
        elif not seller_name:
            seller_name = m_text

    # 4. Búsqueda por expresiones regulares en el texto de la página
    page_text = soup.get_text()
    if not seller_name:
        match = re.search(r'(?:Vendido por|Sold by)\s*[:]?\s*([A-Za-z0-9áéíóúÁÉÍÓÚ\s\.\-]{2,40})', page_text, re.IGNORECASE)
        if match:
            seller_name = match.group(1).strip()

    # 5. Detección fallback de Amazon
    page_text_lower = page_text.lower()
    if not seller_name or seller_name.lower() in ("desconocido", ""):
        if "vendido y enviado por amazon" in page_text_lower or "vendido por amazon méxico" in page_text_lower:
            seller_name = "Amazon México"
        elif "vendido por amazon estados unidos" in page_text_lower or "amazon ee.uu." in page_text_lower:
            seller_name = "Amazon Estados Unidos"
        else:
            seller_name = "Desconocido"

    if len(seller_name) > 60:
        seller_name = seller_name[:57] + "..."

    seller_lower = seller_name.lower()
    shipper_lower = shipper_name.lower()

    # Detección de importación de Amazon Estados Unidos / Export
    is_amazon_us = (
        "estados unidos" in seller_lower
        or "ee.uu" in seller_lower
        or "ee. uu." in seller_lower
        or "amazon us" in seller_lower
        or "export sales" in seller_lower
        or "estados unidos" in shipper_lower
        or "ee.uu" in shipper_lower
    )

    # Debe ser estrictamente Amazon México (no terceros, no Amazon EE.UU.)
    is_amazon_mexico = not is_amazon_us and (
        "amazon méxico" in seller_lower
        or "amazon mexico" in seller_lower
        or "amazon.com.mx" in seller_lower
        or "amazon méxico" in shipper_lower
        or "amazon mexico" in shipper_lower
        or (seller_lower == "amazon" and "estados unidos" not in shipper_lower)
    )

    return seller_name, shipper_name, is_amazon_mexico


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

            # Validar idioma y relevancia (SOLO cartas en inglés, descartar español y juguetes)
            bullets_elem = soup.select_one("#feature-bullets") or soup.select_one("#detailBullets_feature_div")
            extra_details = bullets_elem.get_text(strip=True).lower() if bullets_elem else ""

            if not config.is_tcg_product(title, extra_text=extra_details):
                logger.info(
                    f"[Amazon] ASIN {asin} ('{title[:35]}...') descartado: "
                    f"No es TCG en inglés o se detectó idioma español."
                )
                return None

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

            # Extracción del vendedor (Merchant) y remitente
            seller, shipper, is_amazon_mexico = extract_amazon_seller_info(soup)

            # Filtro estricto: Solo vendedor y remitente oficial Amazon México (descarta terceros y Amazon EE.UU.)
            if config.amazon_only_official_seller and not is_amazon_mexico:
                logger.info(
                    f"[Amazon] ASIN {asin} ('{title[:30]}...') descartado: "
                    f"Vendedor '{seller}' / Remitente '{shipper}' no es específicamente 'Amazon México'."
                )
                return None

            seller_display = f"{seller} (Amazon México Oficial ✅)" if is_amazon_mexico else seller

            # Validación de MSRP dinámico por tipo de producto (+15% de colchón)
            msrp_eval = evaluate_product_msrp(
                title=title,
                actual_price=price_val,
                default_max_msrp=config.max_msrp_price
            )
            is_msrp = in_stock and msrp_eval["is_valid_deal"]

            item = ScrapedItem(
                store="Amazon México",
                title=title,
                price=price_val,
                price_str=price_str or "Consultar en enlace",
                url=url,
                in_stock=in_stock,
                is_msrp=is_msrp,
                seller=seller_display,
                notes=f"ASIN: {asin}",
                category_name=msrp_eval["category_name"],
                msrp_usd=msrp_eval["msrp_usd"],
                msrp_mxn=msrp_eval["msrp_mxn"],
                max_allowed_mxn=msrp_eval["max_allowed_mxn"],
            )

            logger.info(
                f"[Amazon] ASIN {asin}: {'EN STOCK' if in_stock else 'Agotado'} | "
                f"Tipo: {msrp_eval['category_name']} | "
                f"Precio: {price_str or 'N/A'} (Tope +15%: ${msrp_eval['max_allowed_mxn']:,.0f} MXN) | "
                f"MSRP válido: {is_msrp}"
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
