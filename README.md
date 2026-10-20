# ⚡ Pokenotify — Bot de Monitoreo TCG (Pokémon)

Bot de monitoreo automatizado en segundo plano (Worker) escrito en Python. Rastrea inventario y precios de artículos de alta demanda de Pokémon TCG en **Costco México** y **Amazon México** (detectando stock a precio de lista / MSRP) y envía alertas instantáneas por **Telegram** (100% gratuito de por vida) o WhatsApp.

---

## 🛠️ Stack Tecnológico
- **Lenguaje:** Python 3.11 (`python:3.11-slim`)
- **Scraping & Parsing:** `requests`, `beautifulsoup4`
- **Notificaciones:** Telegram Bot API (Always Free) / CallMeBot / Twilio
- **Contenedor:** Docker & Docker Compose
- **Despliegue:** Google Cloud Platform (GCP) Compute Engine (`e2-micro`, Always Free en `us-central1`)

---

## 🚀 Guía de Actualización y Despliegue Continuo (CI/CD)

### 1. ¿Cómo actualizar la lógica del bot (Scraping, nuevas funciones, etc.)?

Cada vez que modifiques el código en tu máquina local (por ejemplo, nuevos selectores HTML, soporte para otra tienda o cambios en `main.py`):

#### Paso 1 (En tu computadora local):
Guarda y sube tus cambios a GitHub:
```bash
git add .
git commit -m "feat: actualiza lógica de scraping"
git push
```

#### Paso 2 (En la terminal SSH de Google Cloud):
Conéctate a tu máquina virtual en GCP y ejecuta:
```bash
cd ~/Pokenotify
git pull
docker-compose up -d --build
```
> **¿Qué hace esto?** Docker detecta los archivos modificados, recompila la imagen, detiene el contenedor viejo y levanta el nuevo en cuestión de segundos sin perder tiempo de monitoreo.

---

### 2. ¿Cómo actualizar solo variables de configuración (.env)?

Si solo quieres:
- Agregar nuevos **ASINs** de Amazon.
- Modificar el precio máximo **MSRP**.
- Cambiar el intervalo de chequeo (**`CHECK_INTERVAL_SECONDS`**).

**No necesitas reconstruir la imagen Docker.** Solo haz esto en la terminal SSH de tu servidor:

1. Abre y edita tu archivo `.env`:
   ```bash
   nano .env
   ```
   *(Modifica lo que necesites, guarda con `Ctrl + O`, presiona `Enter`, y sal con `Ctrl + X`)*.

2. Reinicia el contenedor para aplicar los cambios de inmediato:
   ```bash
   docker-compose restart
   ```

---

### 3. ¿Cómo probar que las notificaciones funcionan?

Puedes probar que las alertas lleguen correctamente a tu teléfono en cualquier momento:

- **En tu servidor GCP con Docker:**
  ```bash
  docker-compose exec pokenotify python test_alert.py
  ```
- **En tu máquina local:**
  ```bash
  python test_alert.py
  ```
- **Prueba automática al iniciar:**
  Por defecto, cada vez que el contenedor arranca o se reinicia (`docker-compose restart`), envía un mensaje de confirmación a tu Telegram para asegurar que la conexión está activa. *(Si deseas apagar este mensaje de arranque, puedes poner `SEND_STARTUP_TEST_ALERT=false` en tu `.env`)*.

---

## 📋 Comandos de Mantenimiento Frecuentes

| Acción | Comando |
|---|---|
| **Ver logs en tiempo real** | `docker-compose logs -f` *(Salir con `Ctrl + C`)* |
| **Ver últimas 50 líneas de logs** | `docker-compose logs --tail=50 -f` |
| **Ver estado del contenedor** | `docker ps` |
| **Reiniciar el bot** | `docker-compose restart` |
| **Detener el bot** | `docker-compose down` |
| **Iniciar el bot en segundo plano** | `docker-compose up -d` |

---

## ⚙️ Esquema de Variables de Entorno (`.env`)

```env
# Canal Principal (100% Plan Continuo Gratuito Permanente)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=987654321

# Parámetros del Monitor
CHECK_INTERVAL_SECONDS=90
MAX_MSRP_PRICE_MXN=1600.0
AMAZON_ASINS=B0CQV49Z5X,B0DFZ2M1R6
```

---

## 🛡️ Políticas de Alerta
- **Sin Stock:** El bot trabaja en total silencio; no envía notificaciones spam.
- **Con Stock a MSRP:** Despacha la alerta de inmediato con título, precio, tienda y enlace de compra directo.
- **Cooldown Anti-Spam:** Solo reenvía alerta del mismo producto tras 1 hora si aún sigue disponible.
