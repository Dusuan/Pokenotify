# Instrucciones del Proyecto (CLAUDE.md)

Este documento contiene las reglas generales, convenciones, comandos personalizados y directrices de operación para el Asistente AI (Agente de Software) en el proyecto **Pokenotify**.

---

## Reglas Fundamentales de Operación del Agente

1. **Lectura Previa Obligatoria**: Antes de generar o modificar código, el agente debe leer `CLAUDE.md`, `SPEC.md`, `REFERENCES.md` y `WORKLOG.md` para entender el estado actual del proyecto y no desalinearse de los objetivos.
2. **Dependencias Estrictas**: No instalar ni importar librerías externas que no estén previamente discutidas y aprobadas en `SPEC.md` / `requirements.txt`. El stack base es `requests`, `beautifulsoup4`, `twilio` y `python-dotenv`.
3. **Regla de WORKLOG.md**: Al concluir una tarea o sesión, actualizar `WORKLOG.md`. Si ya existe una sección para el día de hoy, **editar/sobrescribir** la entrada de hoy para reflejar el estado final, nunca duplicar la fecha.
4. **Simplicidad ante Todo (KISS)**: Escribir el código mínimo necesario que resuelva el requerimiento de monitoreo. Evitar sobre-ingeniería o abstracciones complejas para casos hipotéticos.
5. **Cambios Quirúrgicos**: Modificar únicamente lo necesario. No tocar código adyacente ni formatear archivos no relacionados.
6. **Commits Atómicos y Semánticos**: Seguir la convención Conventional Commits (`feat:`, `fix:`, `docs:`, `build:`, `refactor:`, `chore:`).

---

## Comandos Personalizados

- `/load-project`: Lee `CLAUDE.md`, `SPEC.md` y `WORKLOG.md` en orden. Responde con un resumen del estado actual, tareas en curso y el próximo paso. No escribe código hasta confirmación.
- `/review-code`: Revisa el código implementado con mentalidad de Senior Engineer evaluando: 1) Bugs / Edge cases, 2) Cumplimiento de `CLAUDE.md`, 3) Simplicidad, 4) Manejo de errores HTTP (403, 503) y WAF, 5) Riesgos en producción.
- `/new-feature [descripción]`: Planifica e implementa una nueva funcionalidad paso a paso siguiendo los patrones de `REFERENCES.md`.
- `/fix-bug [descripción]`: Diagnostica y repara un problema especificando causa, archivos afectados y diff exacto sin alterar código fuera de alcance.
- `/update-worklog`: Actualiza `WORKLOG.md` reflejando el progreso del día.
- `/add-reference [tema]`: Agrega selectores, snippets o técnicas anti-WAF a `REFERENCES.md`.
- `/update-spec [cambio]`: Actualiza requerimientos o modelos en `SPEC.md`.

---

## Stack Tecnológico (Pokenotify)
- **Lenguaje**: Python 3.11
- **Scraping**: `requests`, `beautifulsoup4`
- **Mensajería**: `twilio` (WhatsApp API)
- **Configuración**: `python-dotenv`
- **Contenedor**: Docker (`python:3.11-slim`), `docker-compose`

---

## Proceso de Trabajo del Agente
1. Verificar siempre la existencia y valores en variables de entorno antes de ejecutar llamadas de red.
2. Manejar excepciones de red y códigos de estado (403 Forbidden por WAF, 429 Too Many Requests, 503 Service Unavailable) con logging claro y reintentos o backoff.
3. Asegurar que las salidas de terminal y logs no queden atascadas en buffers (`PYTHONUNBUFFERED=1`).
4. Realizar commits claros y descriptivos por cada feature completado.
