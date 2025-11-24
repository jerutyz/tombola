# GitHub Actions - Automated Scraping

Este directorio contiene workflows de GitHub Actions para scraping automático de datos de lotería.

## Workflows Configurados

### 1. `scrape-telekino.yml`
- **Schedule**: Lunes a las 5 AM (Argentina)
- **Endpoint**: POST `/api/telekino/scrape`
- **Ejecución manual**: Sí (workflow_dispatch)

### 2. `scrape-quini6.yml`
- **Schedule**: Lunes y Jueves a las 5 AM (Argentina)
- **Endpoint**: POST `/api/quini6/scrape`
- **Ejecución manual**: Sí (workflow_dispatch)

## Configuración Requerida

### Secret en GitHub

Debes configurar el siguiente secret en tu repositorio de GitHub:

1. Ve a: **Settings** → **Secrets and variables** → **Actions**
2. Click en **New repository secret**
3. Nombre: `SCRAPE_API_KEY`
4. Value: `(Tu token generado - ver .env local)`

## Ejecución Manual

Puedes ejecutar los workflows manualmente desde:
**Actions** → Selecciona el workflow → **Run workflow**

## Horarios (UTC vs Argentina)

- Argentina Time: UTC-3
- 5 AM Argentina = 8 AM UTC
- Cron: `0 8 * * 1,4` = Lunes y Jueves a las 8 AM UTC

## Monitoreo

Puedes ver los resultados de cada ejecución en:
**Actions** → Selecciona el workflow → Click en la ejecución específica
