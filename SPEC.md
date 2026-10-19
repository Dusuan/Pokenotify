# Especificaciones del Proyecto (SPEC.md)

Este documento es la fuente única de verdad para los requerimientos, la arquitectura y el diseño del sistema **Pokenotify**.

---

## 1. Visión General
**Pokenotify** es un bot de monitoreo en segundo plano (Worker) escrito en Python que rastrea constantemente el inventario y precios de artículos de alta demanda de Pokémon TCG (como las Elite Trainer Boxes de 30 Aniversario y colecciones especiales) en **Costco México** y **Amazon México**. Al detectar stock a precio regular (MSRP) o vendido directamente por tiendas oficiales, envía alertas instantáneas por **WhatsApp** mediante la API de **Twilio**.

---

## 2. Arquitectura del Sistema
- **Tipo de Aplicación**: Proceso demonio / Worker en segundo plano (bucle infinito con intervalos aleatorios/jitter y cooldown anti-spam).
- **Lenguaje y Entorno**: Python 3.11 (`python:3.11-slim`).
- **Contenedor**: Docker + Docker Compose.
- **Librerías Clave**:
  - `requests`: Peticiones HTTP sincrónicas configuradas con cabeceras de emulación de navegador y rotación de User-Agents.
  - `beautifulsoup4` (`bs4`): Parseo y extracción de datos del árbol DOM HTML.
  - `twilio`: Integración oficial con la API REST de Twilio WhatsApp.
  - `python-dotenv`: Carga de configuración y credenciales desde archivos `.env`.

---

## 3. Flujo Lógico del Bot (Pipeline)

```text
       ┌────────────────────────┐
       │     Inicio / Loop      │
       └───────────┬────────────┘
                   ▼
       ┌────────────────────────┐
       │   Carga Config / Env   │
       └───────────┬────────────┘
                   ▼
     ┌─────────────┴─────────────┐
     ▼                           ▼
┌──────────────┐          ┌──────────────┐
│ Scraper      │          │ Scraper      │
│ Costco México│          │ Amazon México│
└──────┬───────┘          └──────┬───────┘
       │ Extracción stock        │ Extracción stock
       │ y validación MSRP       │ y validación MSRP
       └─────────────┬───────────┘
                     ▼
           ¿Hay Stock en MSRP?
             /             \
          [Sí]             [No]
           /                 \
          ▼                   ▼
┌──────────────────┐    ┌──────────────────┐
│ Envío de Alerta  │    │ Espera / Jitter  │
│ Twilio WhatsApp  │    │ (e.g. 60-120 seg)│
└─────────┬────────┘    └────────┬─────────┘
          │                      │
          └───────────┬──────────┘
                      ▼
             Siguiente Iteración
```

1. **Inicialización**: Lectura de variables de entorno y validación de credenciales Twilio (con fallback en modo log si no están definidas).
2. **Ciclo de Inspección (Costco México)**:
   - Consulta el catálogo de Pokémon en Costco México.
   - Detecta tarjetas de producto, descarta ítems agotados (`out-of-stock`), valida títulos relevantes y evalúa precio vs umbral MSRP.
   - Maneja códigos HTTP 403 (WAF Akamai) y 503 sin interrumpir la ejecución.
3. **Ciclo de Inspección (Amazon México)**:
   - Itera sobre los ASINs configurados en `AMAZON_ASINS`.
   - Extrae disponibilidad (`#availability`), precio (`.a-price`) y vendedor (`#merchant-info`).
   - Descarta revendedores que inflen el precio sobre el MSRP.
   - Maneja bloqueos WAF (403), sobrecargas (503) y retos CAPTCHA.
4. **Despacho de Alertas y Cooldown**:
   - Si se detecta producto disponible con precio objetivo, se envía notificación detallada por WhatsApp con link directo de compra.
   - Cuenta con una caché de cooldown (1 hora por defecto) para evitar re-enviar la misma alerta repetitivamente mientras haya stock.
5. **Espera Adaptativa y Señales**:
   - Duerme durante un intervalo parametrizable con jitter aleatorio (`+ / - 10s`).
   - Atrapa `SIGINT` y `SIGTERM` para apagado controlado y limpio.

---

## 4. Esquema de Variables de Entorno (.env)

| Variable | Tipo | Requerido | Descripción | Ejemplo |
|---|---|---|---|---|
| `TWILIO_SID` | String | Sí | Account SID de la consola de Twilio | `ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX` |
| `TWILIO_AUTH` | String | Sí | Auth Token de Twilio | `your_auth_token_here` |
| `TWILIO_FROM` | String | Sí | Número remitente de Twilio (Sandbox o Producción) | `whatsapp:+14155238886` |
| `TWILIO_TO` | String | Sí | Número destinatario que recibirá las alertas | `whatsapp:+52155XXXXXXXX` |
| `CHECK_INTERVAL_SECONDS` | Entero | No | Intervalo base de espera entre rondas de scraping (default: 90) | `90` |
| `AMAZON_ASINS` | String | No | Lista de ASINs de Amazon separados por coma | `B0CQV49Z5X,B0DFZ2M1R6` |
| `MAX_MSRP_PRICE_MXN` | Float | No | Precio máximo en MXN para considerar compra razonable (default: 1600.0) | `1600.0` |

---

## 5. Estrategia de Despliegue (Investigación y Comparativa)

El bot requiere ejecutarse como un **Worker persistente 24/7** (un proceso continuo sin servidor HTTP entrante). A continuación se analiza la viabilidad en diferentes plataformas:

| Plataforma | Soporte Worker Continuo Gratuito | Requiere Puerto HTTP | Limitaciones / Consideraciones de Capa Gratuita | Recomendación |
|---|---|---|---|---|
| **Render** | ❌ No en Free Tier para Background Workers | Sí (en Web Services) | Los *Background Workers* en Render son exclusivamente de pago (\$7 USD/mes mínimo). Los *Web Services* gratuitos se suspenden tras 15 minutos sin peticiones HTTP entrantes y tienen un límite de 750 horas/mes compartidas. Correrlo gratis en Render requeriría añadir un mini-servidor HTTP (e.g. FastAPI / Flask) y un servicio de ping externo (como UptimeRobot o Cron-Job.org), lo cual añade complejidad innecesaria. | No recomendado salvo con workaround HTTP |
| **Oracle Cloud (OCI)** | ✅ Sí (Always Free) | ❌ No | Ofrece hasta 4 OCPUs y 24 GB de RAM en instancias ARM Ampere A1 (o 2 instancias AMD Micro de 1 GB) completamente gratis para siempre. Permite correr Docker y systemd sin restricciones ni suspensiones de inactividad. | **Opción Nube #1 (Recomendada si se desea hostear fuera de casa)** |
| **Fly.io** | ⚠️ Parcial / Limitado | ❌ No | Requiere tarjeta de crédito para registrarse. El esquema de free tier cambió a créditos mensuales limitados y suspende máquinas inactivas o cuando se consumen las cuotas. | Opción secundaria |
| **Despliegue Local (Linux / Hyprland / K8s)** | ✅ Excelente y 100% bajo control | ❌ No | El usuario ya cuenta con entorno Linux, Hyprland y Kubernetes local. Ejecutar el contenedor mediante `docker-compose up -d` en segundo plano o como Deployment de K8s no genera costos, no sufre suspensiones por inactividad y permite inspeccionar logs de inmediato con `docker-compose logs -f`. | **Opción Inmediata y más confiable para desarrollo y uso diario** |

**Conclusión y Hoja de Ruta de Despliegue:**
1. **Entorno Primario / Local**: Correr mediante Docker Compose (`docker-compose up -d --build`) o Kubernetes local con reinicio automático (`restart: unless-stopped`).
2. **Entorno Nube Gratuito 24/7**: Si se requiere dejar la máquina local apagada, desplegar el contenedor en una VM **Oracle Cloud Always Free (ARM Ampere / Ubuntu Linux)** mediante Docker y systemd.

---

## 6. Estado de Implementación (Hitos)

### Fase 1: Inicialización y Documentación Base
- [x] Repositorio Git inicializado.
- [x] Documentación base creada (`REFERENCES.md`, `SPEC.md`, `WORKLOG.md`, `CLAUDE.md`).
- [x] Estrategia de despliegue investigada y documentada.

### Fase 2: Implementación de Código
- [x] Dependencias y manejo de entorno (`requirements.txt`, `.env.example`, `config.py`).
- [x] Módulo de alertas Twilio WhatsApp (`alerts/twilio_client.py`).
- [x] Scraper de Amazon México con manejo de WAF (`scrapers/amazon.py`).
- [x] Scraper de Costco México con catálogo y detección de stock (`scrapers/costco.py`).
- [x] Orquestador / Loop principal con jitter, cooldown y señales (`main.py`).

### Fase 3: Contenerización
- [x] `Dockerfile` optimizado (`python:3.11-slim`, `PYTHONUNBUFFERED=1`, usuario no root).
- [x] `docker-compose.yml` para despliegue y variables de entorno.
- [x] Pruebas locales y verificación de ejecución.
