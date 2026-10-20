import time
import logging
import requests
from typing import Tuple, Optional, Dict

logger = logging.getLogger("Pokenotify.Pricing")

# Catálogo oficial de MSRP en USD según tipo de producto Pokémon TCG
# Formato: (identificador, nombre_despliegue, msrp_usd, lista_palabras_clave)
TCG_MSRP_CATALOG = [
    (
        "UPC",
        "Ultra Premium Collection (UPC)",
        179.99,
        ["ultra premium collection", "ultra-premium collection", "upc", "ultra premium"],
    ),
    (
        "BOOSTER_BOX",
        "Booster Display Box (36 packs)",
        161.64,
        ["booster display", "booster box", "display box", "36 packs", "36 sobres", "caja de 36"],
    ),
    (
        "PC_ETB",
        "Elite Trainer Box — Pokemon Center",
        59.99,
        ["pokemon center elite trainer", "pokemon center etb", "pc etb"],
    ),
    (
        "ETB",
        "Elite Trainer Box (ETB)",
        49.99,
        ["elite trainer box", "etb", "caja de entrenador elite", "caja de entrenador élite"],
    ),
    (
        "PREMIUM_COLLECTION",
        "Premium Collection",
        39.99,
        ["premium collection", "coleccion premium", "colección premium", "super premium collection"],
    ),
    (
        "BUILD_BATTLE",
        "Build & Battle Box / Stadium",
        29.99,
        ["build & battle", "build and battle", "combina y combate"],
    ),
    (
        "BOOSTER_BUNDLE",
        "Booster Bundle (6 packs)",
        26.94,
        ["booster bundle", "lote de 6 sobres", "bundle 6 packs", "6 booster packs"],
    ),
    (
        "STANDARD_TIN",
        "Tin / Lata Estándar",
        24.99,
        ["tin", "lata", "collector chest", "maletin coleccionable"],
    ),
    (
        "3_PACK_BLISTER",
        "3-Pack Blister",
        13.99,
        ["3-pack blister", "3 pack blister", "blister 3", "tripack", "tri-pack", "3 booster packs"],
    ),
    (
        "MINI_TIN",
        "Mini Tin",
        9.99,
        ["mini tin", "mini lata"],
    ),
    (
        "SINGLE_BOOSTER",
        "Single Booster Pack (1 sobre)",
        4.49,
        ["single booster", "sobre individual", "booster pack", "1 booster", "1 sobre"],
    ),
]

# Caché del tipo de cambio USD a MXN
_cached_rate: Optional[float] = None
_last_rate_fetch_time: float = 0.0
RATE_CACHE_TTL = 43200  # 12 horas
DEFAULT_FALLBACK_RATE = 18.50  # Tipo de cambio de respaldo en caso de fallo de red


def get_usd_to_mxn_rate() -> float:
    """
    Obtiene el tipo de cambio oficial promedio reciente de USD a MXN.
    Se almacena en caché por 12 horas para evitar sobrecarga de red.
    """
    global _cached_rate, _last_rate_fetch_time

    now = time.time()
    if _cached_rate is not None and (now - _last_rate_fetch_time) < RATE_CACHE_TTL:
        return _cached_rate

    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=8)
        if res.status_code == 200:
            data = res.json()
            rate = data.get("rates", {}).get("MXN")
            if rate and isinstance(rate, (int, float)):
                _cached_rate = float(rate)
                _last_rate_fetch_time = now
                logger.info(f"Tipo de cambio USD a MXN actualizado: ${_cached_rate:.2f} MXN/USD")
                return _cached_rate
    except Exception as e:
        logger.warning(f"No se pudo consultar API de tipo de cambio ({e}). Usando valor de respaldo.")

    return _cached_rate or DEFAULT_FALLBACK_RATE


def evaluate_product_msrp(title: str, actual_price: Optional[float], default_max_msrp: float = 1600.0) -> Dict:
    """
    Identifica la categoría del producto TCG a partir del título, calcula el MSRP en MXN
    con el tipo de cambio actual y aplica un colchón del +15%.
    
    :return: Diccionario con detalles de categorización, precios y si califica como MSRP válido.
    """
    t = title.lower()
    matched_category = None

    for cat_id, cat_name, msrp_usd, keywords in TCG_MSRP_CATALOG:
        for kw in keywords:
            if kw in t:
                matched_category = (cat_id, cat_name, msrp_usd)
                break
        if matched_category:
            break

    usd_rate = get_usd_to_mxn_rate()

    if matched_category:
        cat_id, cat_name, msrp_usd = matched_category
        msrp_mxn = msrp_usd * usd_rate
        # Colchón del 15% sobre el precio MSRP
        max_allowed_mxn = msrp_mxn * 1.15
    else:
        # Si no encaja en una categoría exacta, usar ETB como referencia estándar
        cat_name = "Producto TCG General"
        msrp_usd = default_max_msrp / (usd_rate * 1.15)
        msrp_mxn = msrp_usd * usd_rate
        max_allowed_mxn = default_max_msrp

    is_valid_deal = False
    if actual_price is not None and actual_price > 0:
        is_valid_deal = actual_price <= max_allowed_mxn

    return {
        "category_name": cat_name,
        "msrp_usd": msrp_usd,
        "msrp_mxn": msrp_mxn,
        "usd_rate": usd_rate,
        "cushion_percent": 15,
        "max_allowed_mxn": max_allowed_mxn,
        "is_valid_deal": is_valid_deal,
    }
