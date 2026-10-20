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
                f"\n🎯 *Precio Máx con Colchón (+15%):* ${self.max_allowed_mxn:,.0f} MXN"
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
            f"🔗 *Enlace de compra directa:*\n{self.url}"
        )
