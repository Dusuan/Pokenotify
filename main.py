import time
import signal
import random
import sys
import logging
from typing import Dict
from config import config, logger
from alerts import dispatch_alert
from scrapers.amazon import scan_amazon
from scrapers.costco import scan_costco
from scrapers.models import ScrapedItem
from test_alert import send_test_notification

# Control de terminación graciosa (Graceful shutdown)
running = True

# Cooldown para evitar spam de alertas (URL -> timestamp del último envío)
# Por defecto 12 horas para productos que permanecen disponibles continuamente
ALERT_COOLDOWN_SECONDS = int(config.alert_cooldown_hours * 3600)


def handle_shutdown(signum, frame):
    global running
    logger.info("Señal de detención recibida. Finalizando ciclo de monitoreo limpiamente...")
    running = False


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


def run_monitor_cycle(alert_history: Dict[str, float]):
    """Ejecuta una ronda de inspección completa en todas las plataformas."""
    logger.info("=== Iniciando ronda de monitoreo ===")

    found_opportunities: list[ScrapedItem] = []

    # 1. Monitoreo Costco México
    try:
        costco_items = scan_costco()
        found_opportunities.extend(costco_items)
    except Exception as e:
        logger.error(f"Error inesperado en ciclo de Costco: {e}")

    # 2. Monitoreo Amazon México
    try:
        amazon_items = scan_amazon()
        found_opportunities.extend(amazon_items)
    except Exception as e:
        logger.error(f"Error inesperado en ciclo de Amazon: {e}")

    # 3. Procesamiento y despacho de alertas
    now = time.time()
    for item in found_opportunities:
        last_sent = alert_history.get(item.url, 0)
        time_since_last = now - last_sent

        if time_since_last < ALERT_COOLDOWN_SECONDS:
            logger.info(
                f"[Cooldown Activo] Ya se alertó '{item.title[:30]}...' hace "
                f"{int(time_since_last // 60)} min. Se omite para evitar spam."
            )
            continue

        # Enviar alerta (Telegram, Discord, CallMeBot WhatsApp o Twilio) con botones de acción directa
        msg = item.to_whatsapp_message()
        buttons = item.get_action_buttons()
        success = dispatch_alert(msg, buttons=buttons)
        if success:
            alert_history[item.url] = now
            logger.info(f"¡Alerta despachada para {item.title[:40]}...!")
        else:
            logger.error(f"Fallo al despachar alerta para {item.title[:40]}...")

    logger.info(
        f"=== Fin de ronda. Oportunidades encontradas: {len(found_opportunities)} ==="
    )


def main():
    logger.info("Iniciando Pokenotify - Bot de Monitoreo TCG (Costco & Amazon México)")
    logger.info(
        f"Intervalo base: {config.check_interval}s | Cooldown de alertas: {config.alert_cooldown_hours:.1f}h | "
        f"Precio MSRP Máx: ${config.max_msrp_price} MXN"
    )
    logger.info(f"ASINs de Amazon monitoreados: {', '.join(config.amazon_asins)}")

    # Modo de prueba directa si se pasa el flag --test-alert
    if "--test-alert" in sys.argv:
        logger.info("Modo de prueba manual activado (--test-alert).")
        send_test_notification()
        return

    # Envío de prueba al arrancar el contenedor si está habilitado
    if config.send_startup_test_alert:
        send_test_notification()

    alert_history: Dict[str, float] = {}

    while running:
        run_monitor_cycle(alert_history)

        if not running:
            break

        # Jitter aleatorio (+/- 10s) para mitigar huellas de tráfico automatizado
        jitter = random.uniform(-10.0, 15.0)
        sleep_duration = max(15.0, config.check_interval + jitter)
        logger.info(f"Próxima inspección en {sleep_duration:.1f} segundos...\n")

        # Espera fraccionada para responder inmediatamente a señales SIGINT/SIGTERM
        elapsed = 0.0
        while elapsed < sleep_duration and running:
            time.sleep(1.0)
            elapsed += 1.0

    logger.info("Pokenotify se ha detenido correctamente.")


if __name__ == "__main__":
    main()
