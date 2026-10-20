# Registro de Trabajo (WORKLOG.md)

Este documento mantiene un registro cronológico del progreso, decisiones tomadas y pendientes del proyecto **Pokenotify**.

> **[REGLA ESTRICTA]**: Cada sesión de trabajo debe actualizar el registro del día en curso. No agregar una nueva entrada si ya existe una para el día de hoy; editar/sobrescribir la entrada del día actual para reflejar el estado final acumulado de la sesión.

---

## Sesión: 2026-10-20 (Verificación de Alertas y Test Suite)

**Qué implementamos en esta sesión:**
- Creación del script de prueba `test_alert.py` para verificar notificaciones directamente a Telegram sin esperar ciclos de stock.
- Integración de alerta de confirmación automática en `main.py` al arrancar el contenedor (`SEND_STARTUP_TEST_ALERT=true`).
- Soporte para flag manual `--test-alert` en `main.py`.
- Ejecución y verificación exitosa de prueba de notificación con entrega real a Telegram.
- Documentación del flujo de pruebas en `README.md` y actualización del template `.env.example`.
- Implementación de filtro inteligente de TCG en `config.py` y `scrapers/costco.py` con lista blanca de términos de cartas (ETB, booster, tin, colección, sobres) y lista negra de exclusión (Legos, Mega Construx, peluches, videojuegos, ropa).
- Implementación del módulo de precios dinámicos `scrapers/pricing.py` con tabla oficial de MSRPs en USD para todas las categorías (ETB, Booster Box, UPC, Blisters, Tins, etc.), consulta y caché del tipo de cambio USD/MXN en tiempo real, y cálculo automático con colchón porcentual configurable actualizado al +25% (`MSRP_CUSHION_PERCENT=25.0`), estableciendo el tope de alerta para ETBs en ~$1,153 MXN para capturar compras ventajosas en $1,100 MXN.
- Regla estricta de idioma implementada en `config.py`, `scrapers/amazon.py` y `scrapers/costco.py`: filtro que descarta automáticamente cualquier producto o carta en idioma Español (`español`, `spanish`, `castellano`, etc.), garantizando alertas exclusivas para cartas Pokémon TCG en idioma Inglés.
- Extracción precisa de vendedor/remitente en Amazon México (`extract_amazon_seller_info`) y filtro estricto opcional `AMAZON_ONLY_OFFICIAL_SELLER=true` para garantizar alertas exclusivamente de productos vendidos/enviados por Amazon México u oficial, descartando revendedores aleatorios.

**Qué está en progreso:**
- Monitoreo continuo 24/7 en la VM de Google Cloud Platform (GCP).

**Bloqueos:**
- Ninguno.

**Próximos pasos en orden de prioridad:**
1. En la VM de GCP, ejecutar `git pull && docker-compose up -d --build` para actualizar el contenedor con el ping de confirmación al arranque.
2. Agregar nuevos ASINs de Pokémon TCG en `.env` conforme salgan preventas de nuevos sets.

---

## Sesión: 2026-10-19 (Fases 1, 2, 3 y 4: Implementación Completa y Despliegue)

**Qué implementamos en esta sesión:**
- **Fase 1 (Context Management & Docs)**:
  - Repositorio Git inicializado con estructura de branches y `.gitignore`.
  - Creación de los cuatro documentos de contexto: `CLAUDE.md`, `SPEC.md`, `WORKLOG.md` y `REFERENCES.md`.
  - Commit inicial realizado (`docs: inicializa estructura de contexto y especificaciones`).
- **Fase 2 (Features Implementados)**:
  - *Feature 1*: Configuración y dependencias (`requirements.txt`, `.env.example`, `config.py`) con validación y tipado de variables (`feat: setup dependencias y env`).
  - *Feature 2*: Módulo de mensajería `alerts/twilio_client.py` con lazy loading de Twilio SDK y fallback en modo log (`feat: integra cliente de twilio para alertas whatsapp`).
  - *Feature 3*: Scrapers de Amazon y Costco (`scrapers/amazon.py`, `scrapers/costco.py`, `scrapers/utils.py`, `scrapers/models.py`) con mitigación de WAF, rotación de cabeceras, detección de CAPTCHA/403/503 y filtro de precios MSRP (`feat: implementa scrapers de amazon y costco`).
  - *Feature 4*: Orquestador principal `main.py` con bucle continuo, jitter aleatorio (+/- 10s), mitigación de spam mediante cooldown de 1h y manejo de señales `SIGINT`/`SIGTERM` (`feat: orquestacion del loop principal y tiempos de espera`).
- **Fase 3 (Contenerización)**:
  - Creación de `Dockerfile` basado en `python:3.11-slim`, activando `PYTHONUNBUFFERED=1` y configurando usuario no privilegiado (`appuser`).
  - Creación de `docker-compose.yml` para levantar el worker con inyección de variables de entorno y reinicio automático (`build: dockeriza la aplicacion de monitoreo`).
- **Fase 4 (Despliegue Always Free en GCP, Telegram API & README)**:
  - Soporte integrado para **Telegram Bot API** (100% permanente y continuo gratuito para mensajes push al celular).
  - Configuración y despliegue en **Google Cloud Platform (GCP)** sobre instancia `e2-micro` (Always Free permanente en `us-central1` con disco estándar de 30 GB).
  - Creación de [README.md](file:///c:/Users/XxDus/Documents/Pokenotify/README.md) documentando la arquitectura, la guía paso a paso de actualización continua (CI/CD manual) y comandos de mantenimiento de Docker.

**Qué está en progreso:**
- Ejecución continua del bot en segundo plano dentro de la VM de GCP monitoreando Costco y Amazon México.

**Bloqueos:**
- Ninguno.

**Próximos pasos en orden de prioridad:**
1. Verificar recepción de la primera alerta de prueba en Telegram.
2. Afinar selectores o agregar nuevos ASINs de Pokémon TCG en `.env` según demanda de mercado.
3. Actualizar la lógica con `git push` local y `git pull && docker-compose up -d --build` en la VM cuando se requieran ajustes de scraping.

---
*(Las sesiones futuras se registrarán en orden cronológico inverso, sobreescribiendo la sección del día si ya existe).*
