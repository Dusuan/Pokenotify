import re
from dataclasses import dataclass
from typing import Optional, List, Dict
from config import config


@dataclass
class ScrapedItem:
    store: str
    title: str
    price: Optional[float]
    price_str: str
    url: str
    in_stock: bool
    is_msrp: bool
    seller: Optional[str] = None
    notes: Optional[str] = None
    category_name: Optional[str] = None
    msrp_usd: Optional[float] = None
    msrp_mxn: Optional[float] = None
    max_allowed_mxn: Optional[float] = None

    def to_whatsapp_message(self) -> str:
        """Formatea el producto encontrado en un mensaje atractivo para Telegram/WhatsApp."""
        price_display = self.price_str if self.price_str else "No especificado"
        seller_display = f"\n🏪 *Vendido por:* {self.seller}" if self.seller else ""
        category_display = f"\n🏷️ *Tipo:* {self.category_name}" if self.category_name else ""

        pricing_details = ""
        if self.msrp_usd and self.msrp_mxn and self.max_allowed_mxn:
            pricing_details = (
                f"\n💵 *MSRP Oficial:* ${self.msrp_usd:.2f} USD (~${self.msrp_mxn:,.0f} MXN)"
                f"\n🎯 *Precio Máx con Colchón (+{config.msrp_cushion_percent:.0f}%):* ${self.max_allowed_mxn:,.0f} MXN"
            )

        notes_display = f"\n📌 *Nota:* {self.notes}" if self.notes else ""

        return (
            f"🚨 *¡ALERTA DE STOCK TCG POKÉMON!* 🚨\n\n"
            f"🛒 *Tienda:* {self.store}\n"
            f"📦 *Producto:* {self.title}"
            f"{category_display}\n"
            f"💰 *Precio Encontrado:* {price_display}"
            f"{pricing_details}"
            f"{seller_display}"
            f"{notes_display}\n\n"
            f"🔗 *Enlace:* {self.url}"
        )

    def get_action_buttons(self) -> List[List[Dict[str, str]]]:
        """
        Genera botones interactivos de acción rápida (Telegram Inline Keyboard).
        Para Amazon, crea un enlace directo de adición instantánea al carrito / 1-Click.
        """
        buttons: List[List[Dict[str, str]]] = []

        if "amazon" in self.store.lower():
            match = re.search(r"(?:/dp/|/gp/product/|asin=)([A-Z0-9]{10})", self.url, re.IGNORECASE)
            if match:
                asin = match.group(1).upper()
                # URL especial de adición instantánea al carrito (inicia checkout rápido)
                direct_cart_url = f"https://www.amazon.com.mx/gp/aws/cart/add.html?ASIN.1={asin}&Quantity.1=1"
                product_url = f"https://www.amazon.com.mx/dp/{asin}?th=1&psc=1"

                buttons.append([{"text": "⚡ COMPRAR AHORA (DIRECT 1-CLICK)", "url": direct_cart_url}])
                buttons.append([{"text": "📱 Abrir en App de Amazon", "url": product_url}])
                return buttons

        # Botón por defecto para Costco o tiendas generales
        buttons.append([{"text": f"🛒 Ir a {self.store}", "url": self.url}])
        return buttons
