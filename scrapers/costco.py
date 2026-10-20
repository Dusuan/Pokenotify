import logging
import requests
from bs4 import BeautifulSoup
from typing import Optional, List
from urllib.parse import urljoin
from config import config
from .models import ScrapedItem
from .utils import get_random_headers, parse_price
from .pricing import evaluate_product_msrp

logger = logging.getLogger("Pokenotify.Costco")

COSTCO_SEARCH_URL = "https://www.costco.com.mx/search?text=pokemon"
COSTCO_BASE_URL = "https://www.costco.com.mx"


class CostcoScraper:
    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()

    def search_pokemon_items(self) -> List[ScrapedItem]:
        """
        Escanea la búsqueda de productos Pokémon en Costco México.
        Maneja errores HTTP 403, 503 y detecta productos en stock a MSRP.
        """
        headers = get_random_headers()
        items: List[ScrapedItem] = []

        try:
            response = self.session.get(COSTCO_SEARCH_URL, headers=headers, timeout=15)

            # Manejo específico de WAF / Akamai
            if response.status_code == 403:
                logger.warning("[Costco 403 Forbidden] Petición bloqueada por WAF de Costco México.")
                return items
            elif response.status_code == 503:
                logger.warning("[Costco 503 Service Unavailable] Servicio de Costco temporalmente no disponible.")
                return items
            elif response.status_code != 200:
                logger.warning(f"[Costco HTTP {response.status_code}] Error al consultar catálogo de Costco.")
                return items

            soup = BeautifulSoup(response.text, "html.parser")

            # Buscar contenedores de productos
            product_cards = soup.select(".product-item, .product-tile, div.thumbnail, .product-list-item")
            if not product_cards:
                # Si no hay tarjetas con clases comunes, buscar enlaces de productos
                product_cards = soup.select("div[data-product-code]")

            logger.info(f"[Costco] Se encontraron {len(product_cards)} tarjetas de producto potenciales.")

            for card in product_cards:
                # Título y enlace
                title_elem = card.select_one(".description a, .product-name a, a.title, .product-info-title a")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                relative_url = title_elem.get("href", "")
                product_url = urljoin(COSTCO_BASE_URL, relative_url)

                card_text = card.get_text().lower()

                # Filtrar rigurosamente: cartas TCG, exclusiones (Legos/peluches) y SOLO idioma inglés (no español)
                if not config.is_tcg_product(title, extra_text=card_text):
                    continue
                is_out_of_stock = (
                    "agotado" in card_text
                    or "out of stock" in card_text
                    or bool(card.select_one(".out-of-stock, .product-out-of-stock, span.not-available"))
                )
                in_stock = not is_out_of_stock

                # Precio
                price_elem = card.select_one(".product-price .price, .price-value, .base-price, span.price")
                price_str = price_elem.get_text(strip=True) if price_elem else ""
                price_val = parse_price(price_str)

                # Validación de MSRP dinámico por tipo de producto (+15% colchón)
                msrp_eval = evaluate_product_msrp(
                    title=title,
                    actual_price=price_val,
                    default_max_msrp=config.max_msrp_price
                )
                is_msrp = in_stock and (msrp_eval["is_valid_deal"] if price_val is not None else True)

                item = ScrapedItem(
                    store="Costco México",
                    title=title,
                    price=price_val,
                    price_str=price_str or "Consultar en Costco",
                    url=product_url,
                    in_stock=in_stock,
                    is_msrp=is_msrp,
                    seller="Costco México Oficial",
                    notes="Socio Costco / Compra sujeta a membresía",
                    category_name=msrp_eval["category_name"],
                    msrp_usd=msrp_eval["msrp_usd"],
                    msrp_mxn=msrp_eval["msrp_mxn"],
                    max_allowed_mxn=msrp_eval["max_allowed_mxn"],
                )
                items.append(item)

                logger.info(
                    f"[Costco] '{title[:35]}...': {'EN STOCK' if in_stock else 'Agotado'} | "
                    f"Tipo: {msrp_eval['category_name']} | "
                    f"Precio: {price_str or 'N/A'} (Tope +15%: ${msrp_eval['max_allowed_mxn']:,.0f} MXN) | "
                    f"MSRP: {is_msrp}"
                )

        except requests.RequestException as e:
            logger.error(f"[Costco Request Error] Excepción al consultar catálogo: {e}")

        return items


def scan_costco() -> List[ScrapedItem]:
    """Ejecuta el escaneo de Costco México y retorna los ítems disponibles."""
    scraper = CostcoScraper()
    items = scraper.search_pokemon_items()
    return [it for it in items if it.in_stock and it.is_msrp]
