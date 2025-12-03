# Tombola Analytics - Web Application

Análisis estadístico de lotería argentina: **Telekino** y **Quini 6**

## 🚀 Quick Start

### Método 1: Docker (Recomendado)

```bash
# Build y run con docker-compose
docker-compose up --build

# Acceder a la aplicación
open http://localhost:5000
```

### Método 2: Local Development

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor de desarrollo
python app.py

# Acceder a la aplicación
open http://localhost:5000
```

## 📋 Características

- ✅ **Dashboard interactivo** con estadísticas en tiempo real
- ✅ **API REST** para consulta de stats
- ✅ **Gráficos interactivos** con Chart.js
- ✅ **Sistema de caché** para consultas rápidas
- ✅ **Backtesting** filtrando por fecha
- ✅ **Docker** para deployment fácil
- ⚙️ **Scraping** disponible vía CLI (backend)

## 🎮 Funcionalidades

### Interfaz Web

- **Visualización** de estadísticas con gráficos interactivos
- **Backtesting** con filtros de fecha
- **Caché** automático para consultas rápidas
- Compatible con móvil y desktop

### CLI (Línea de Comandos)

- **Scraping** de sorteos nuevos
- **Verificación** de jugadas (Quini 6)
- **Administración** de datoso

## 🐳 Docker Deployment

### Build imagen

```bash
docker build -t tombola-analytics .
```

### Run container

```bash
docker run -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/visualizaciones:/app/visualizaciones \
  tombola-analytics
```

### Deploy a servidor

```bash
# Tag imagen
docker tag tombola-analytics yourregistry/tombola-analytics:latest

# Push a registry
docker push yourregistry/tombola-analytics:latest

# Pull y run en servidor
docker pull yourregistry/tombola-analytics:latest
docker-compose up -d
```

## ✈️ Deployment a Fly.io

### Pre-requisitos

1. Instala la CLI de Fly.io:
   ```bash
   # macOS
   brew install flyctl
   
   # Linux/WSL
   curl -L https://fly.io/install.sh | sh
   ```

2. Autentícate en Fly.io:
   ```bash
   fly auth login
   ```

### Deploy Inicial (Primera vez)

Si es tu primera vez deployando esta app:

```bash
# Crear app en Fly.io (solo primera vez)
fly launch --no-deploy

# Configurar secrets (API key)
fly secrets set API_KEY=tu_clave_secreta

# Crear volumen persistente para datos
fly volumes create persistent --size 1

# Deploy
fly deploy
```

### Deploy de Actualizaciones

Para deployar cambios después de la configuración inicial:

```bash
# Deploy de la nueva versión
fly deploy

# Ver estado del deploy
fly status

# Ver logs en tiempo real
fly logs
```

### Comandos Útiles

```bash
# Ver logs
fly logs

# Ver estado de la app
fly status

# Ver secrets configurados
fly secrets list

# Agregar/actualizar un secret
fly secrets set NOMBRE=valor

# SSH a la máquina
fly ssh console

# Escalar recursos
fly scale memory 512    # MB
fly scale count 1       # Número de instancias

# Ver dominios
fly info
```

### Verificar Deployment

Después del deploy, verifica que todo funcione:

1. **Health Check**: `https://tu-app.fly.dev/health`
2. **Web App**: `https://tu-app.fly.dev`

### Notas Importantes

- **Volumen Persistente**: Los datos CSV se guardan en `/app/persistent` y persisten entre deploys
- **Auto Sleep**: La app se suspende automáticamente cuando no tiene tráfico y se reactiva al recibir requests
- **HTTPS**: Fly.io provee HTTPS automático
- **Región**: Configurado en `dfw` (Dallas), puedes cambiarlo en `fly.toml`

## 📡 API Endpoints

### Telekino

- `GET /api/telekino/stats?fecha=YYYY-MM-DD` - Obtener estadísticas
- `POST /api/telekino/scrape` - Scrapear último sorteo

### Quini 6

- `GET /api/quini6/stats?fecha=YYYY-MM-DD` - Obtener estadísticas
- `POST /api/quini6/scrape` - Scrapear último sorteo
- `GET /api/quini6/verificar` - Verificar jugadas

### Utilidades

- `GET /health` - Health check

## 🗂️ Estructura del Proyecto

```
tombola-analytics/
├── app.py                  # Flask application
├── main.py                 # CLI (legacy)
├── templates/              # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── telekino.html
│   └── quini6.html
├── static/                 # CSS/JS
│   ├── css/style.css
│   └── js/app.js
├── tombola/                # Core logic
│   ├── telekino.py
│   ├── quini6.py
│   └── stats_cache.py
├── data/                   # CSV data
│   ├── telekino.csv
│   ├── quini6.csv
│   └── stats_cache/
├── visualizaciones/        # Generated images
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 🛠️ Tecnologías

- **Backend**: Flask + Python 3.9
- **Frontend**: Bootstrap 5 + Chart.js
- **Deployment**: Docker + Gunicorn
- **Data**: CSV files + JSON cache

## 📊 CLI (Legacy)

El CLI original sigue disponible:

```bash
# Telekino
python main.py telekino stats [YYYY-MM-DD]
python main.py telekino scrape

# Quini 6
python main.py quini6 stats [YYYY-MM-DD]
python main.py quini6 scrape
python main.py quini6 verificar
```

## 🔧 Configuración

### Variables de Entorno

```bash
FLASK_ENV=production      # production|development
PYTHONUNBUFFERED=1       # Para logs en Docker
```

### Puertos

- **5000**: Flask application (HTTP)

## 📝 Licencia

MIT

## 👨‍💻 Autor

Desarrollado con ❤️ para análisis de lotería argentina
