from dataclasses import dataclass
from typing import Optional


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

    def to_whatsapp_message(self) -> str:
        """Formatea el producto encontrado en un mensaje atractivo de WhatsApp."""
        price_display = self.price_str if self.price_str else "No especificado"
        seller_display = f"\n🏪 *Vendido por:* {self.seller}" if self.seller else ""
        notes_display = f"\n📌 *Nota:* {self.notes}" if self.notes else ""

        return (
            f"🚨 *¡ALERTA DE STOCK TCG POKÉMON!* 🚨\n\n"
            f"🛒 *Tienda:* {self.store}\n"
            f"📦 *Producto:* {self.title}\n"
            f"💰 *Precio:* {price_display}"
            f"{seller_display}"
            f"{notes_display}\n\n"
            f"🔗 *Enlace de compra:*\n{self.url}"
        )
