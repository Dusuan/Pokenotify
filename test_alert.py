#!/usr/bin/env python3
"""
Script de prueba para verificar que las alertas se envíen correctamente al teléfono.
Uso:
    python test_alert.py
    docker-compose run --rm pokenotify python test_alert.py
"""

from config import config, logger
from alerts import dispatch_alert


def send_test_notification() -> bool:
    """Envía un mensaje de prueba para verificar conectividad con los canales de notificación."""
    test_msg = (
        "🧪 *¡PRUEBA DE NOTIFICACIÓN DE POKENOTIFY!* 🧪\n\n"
        "✅ Tus notificaciones están funcionando correctamente.\n"
        f"⏱️ Intervalo base: {config.check_interval}s\n"
        f"💰 MSRP Máx: ${config.max_msrp_price:,.2f} MXN\n"
        f"📦 ASINs de Amazon monitoreados: {len(config.amazon_asins)}\n\n"
        "El bot está activo y listo para alertarte en cuanto detecte stock a precio de lista."
    )
    logger.info("Enviando mensaje de prueba de notificación...")
    success = dispatch_alert(test_msg)
    if success:
        logger.info("Mensaje de prueba enviado exitosamente.")
    else:
        logger.error("No se pudo enviar el mensaje de prueba. Verifica tus credenciales en .env.")
    return success


if __name__ == "__main__":
    print("Iniciando prueba de notificación...")
    success = send_test_notification()
    if success:
        print("¡Prueba completada con éxito! Revisa tu teléfono (Telegram/WhatsApp).")
    else:
        print("Fallo en la prueba. Revisa las variables en tu archivo .env.")
