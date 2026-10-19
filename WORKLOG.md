# Registro de Trabajo (WORKLOG.md)

Este documento mantiene un registro cronológico del progreso, decisiones tomadas y pendientes del proyecto **Pokenotify**.

> **[REGLA ESTRICTA]**: Cada sesión de trabajo debe actualizar el registro del día en curso. No agregar una nueva entrada si ya existe una para el día de hoy; editar/sobrescribir la entrada del día actual para reflejar el estado final acumulado de la sesión.

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
- **Fase 4 (Estrategia de Despliegue & Guías de Setup)**:
  - Análisis comparativo exhaustivo documentado en `SPEC.md` evaluando Render (Free tier descarta background workers directos sin puerto HTTP), Oracle Cloud Always Free (opción recomendada para hosting cloud 24/7 gratuito sin límites de worker) y entorno local del usuario (Docker Compose / K8s sobre Linux).
  - Guía detallada en `REFERENCES.md` para configuración de variables `.env` con Twilio WhatsApp API (Sandbox vs Business Sender oficial).
  - Guía paso a paso en `REFERENCES.md` para despliegue en AWS Cloud (EC2 Free Tier t2/t3.micro con Docker y Docker Compose).

**Qué está en progreso:**
- Configuración de credenciales de Twilio en el archivo `.env` del usuario y provisión de instancia en AWS Cloud.

**Bloqueos:**
- Ninguno.

**Próximos pasos en orden de prioridad:**
1. Crear el archivo `.env` local o en la instancia EC2 con `TWILIO_SID`, `TWILIO_AUTH`, `TWILIO_FROM` y `TWILIO_TO`.
2. Lanzar la instancia EC2 t2/t3.micro en AWS Free Tier e instalar Docker.
3. Iniciar el servicio con `docker compose up -d --build`.

---
*(Las sesiones futuras se registrarán en orden cronológico inverso, sobreescribiendo la sección del día si ya existe).*
