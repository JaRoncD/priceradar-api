# 📡 PriceRadar API

**API de Seguimiento de Precios en Tiempo Real**

Backend construido con **FastAPI** que monitorea precios de criptomonedas en tiempo real, evalúa alertas configuradas por el usuario y entrega actualizaciones a través de **WebSockets**. Los precios se obtienen automáticamente desde **CoinGecko** mediante un scheduler asíncrono en background.

---

## 🚀 Tecnologías

| Tecnología | Descripción |
|---|---|
| Python 3.x | Lenguaje principal |
| FastAPI | Framework web asíncrono |
| APScheduler | Scheduler de tareas en background |
| WebSockets | Actualizaciones en tiempo real |
| CoinGecko API | Fuente de precios de criptomonedas |

---

## 📁 Estructura del proyecto

```
priceradar-api/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py        # Autenticación de usuarios
│   │       ├── products.py    # Gestión de activos/criptomonedas
│   │       ├── alerts.py      # Creación y consulta de alertas
│   │       └── ws.py          # Endpoint WebSocket en tiempo real
│   ├── services/
│   │   ├── price_fetcher.py   # Obtiene precios desde CoinGecko
│   │   └── alert_engine.py    # Evalúa y dispara alertas
│   └── core/
│       └── config.py          # Configuración y variables de entorno
├── main.py                    # Punto de entrada de la aplicación
├── .gitignore
└── .env                       # Variables de entorno (no versionado)
```

---

## ⚙️ Instalación local

### 1. Clonar el repositorio

```bash
git clone https://github.com/JaRoncD/priceradar-api.git
cd priceradar-api
```

### 2. Crear y activar un entorno virtual

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=tu_secret_key_aqui
PRICE_FETCH_INTERVAL=60        # Intervalo en segundos para actualizar precios
DATABASE_URL=sqlite:///./priceradar.db
```

### 5. Ejecutar el servidor

```bash
uvicorn main:app --reload
```

La API estará disponible en `http://127.0.0.1:8000`.  
La documentación interactiva en `http://127.0.0.1:8000/docs`.

---

## 🔄 Scheduler en background

Al iniciar la aplicación, se arrancan automáticamente dos tareas periódicas:

| Tarea | Descripción | Frecuencia |
|---|---|---|
| `price_fetcher` | Obtiene precios actualizados desde CoinGecko | Configurable (`PRICE_FETCH_INTERVAL`) |
| `alert_engine` | Evalúa las alertas activas y notifica si se cumplen | Igual que `price_fetcher` |

Al apagar el servidor, el scheduler se detiene de forma limpia.

---

## 🔐 Autenticación

La API usa autenticación basada en tokens gestionada desde el módulo `auth`.

```http
POST /auth/...
```

Incluye el token en las cabeceras de las peticiones protegidas:

```http
Authorization: Bearer <token>
```

---

## 🌐 Endpoints principales

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/` | Health check |
| POST | `/auth/...` | Registro / Login |
| GET | `/products/` | Listado de activos monitoreados |
| POST | `/products/` | Agregar un activo |
| GET | `/alerts/` | Listar alertas del usuario |
| POST | `/alerts/` | Crear una nueva alerta de precio |
| DELETE | `/alerts/{id}` | Eliminar una alerta |
| WS | `/ws/prices` | Stream en tiempo real de precios vía WebSocket |

---

## 📡 WebSocket

Conéctate al endpoint de WebSocket para recibir actualizaciones de precios en tiempo real sin hacer polling:

```javascript
const socket = new WebSocket("ws://localhost:8000/ws/prices");

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Precio actualizado:", data);
};
```

---

## 📊 Fuente de datos

Los precios provienen de la **API pública de CoinGecko**. No se requiere API key para el tier gratuito, aunque aplican límites de tasa. Ajusta `PRICE_FETCH_INTERVAL` según las restricciones de tu plan.

---

## 📄 Documentación automática

FastAPI genera documentación interactiva automáticamente:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 🛡️ Variables de entorno

| Variable | Descripción | Ejemplo |
|---|---|---|
| `SECRET_KEY` | Clave secreta para firmar tokens | `una_clave_segura` |
| `PRICE_FETCH_INTERVAL` | Intervalo de actualización en segundos | `60` |
| `DATABASE_URL` | URL de conexión a la base de datos | `sqlite:///./priceradar.db` |

---

## 📄 Licencia

Este proyecto es de uso privado/académico. Contacta al autor para más información.

---

## 👤 Autor

**JaRoncD (Jorge Roncancio)** — [github.com/JaRoncD](https://github.com/JaRoncD)
