# Desarrollo Créditos

Proyecto de financiación de créditos con frontend en React + TypeScript + Vite y backend en Python + FastAPI.

## Estructura

```text
backend/
  main.py
  requirements.txt
  database/
    schema.sql
    insert.sql
    session.py
  controllers/
  services/
  repositories/
  models/
  middlewares/
frontend/
  public/
  src/
  package.json
  vite.config.ts
```

## Desarrollo local

Configura el backend desde la raíz del proyecto. Si aún no existe el entorno virtual:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

Configura la conexión a PostgreSQL en la misma terminal:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://postgres:TU_PASSWORD@localhost:5432/DB"
```

Aplica las migraciones y carga los datos iniciales:

```powershell
alembic upgrade head
```

Después ejecuta `backend/database/insert.sql` una sola vez desde pgAdmin Query Tool.

Inicia el backend:

```powershell
python -m uvicorn backend.main:app --reload
```

En otra terminal, instala y ejecuta el frontend desde `frontend`:

```powershell
cd frontend
npm install
npm run dev
```

El frontend queda en `http://localhost:5173` y la documentación interactiva de la API en `http://localhost:8000/api-docs`. Las peticiones a `/api` se redirigen automáticamente al backend durante el desarrollo.

El endpoint inicial es `GET /api/health`.

## Despliegue en Cloudflare Pages

El frontend se despliega en Cloudflare Pages. Desde la carpeta del proyecto:

```powershell
cd frontend
npm install
npm run build
npx wrangler pages deploy dist --project-name desarrollo-creditos
```

En el primer uso, Wrangler solicitará iniciar sesión en Cloudflare y crear el proyecto si todavía no existe. También puedes conectar el repositorio desde **Workers & Pages > Create application > Pages > Connect to Git** con estos valores:

```text
Root directory: frontend
Build command: npm run build
Build output directory: dist
```

El backend FastAPI no se puede publicar como contenido estático de Pages. Publícalo como un servicio Python (por ejemplo, Render, Railway o Fly.io) ejecutando:

```text
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Configura la variable de entorno `CORS_ORIGINS` con el dominio de Pages, por ejemplo `https://desarrollo-creditos.pages.dev`, y configura el frontend para consumir la URL pública de la API. El endpoint de comprobación será `https://TU-BACKEND/api/health`.

Desde la raíz del proyecto, ejecuta las pruebas del backend:

```powershell
python -m pytest backend/tests -q
```

## Migraciones de base de datos

Configura la conexión de PostgreSQL antes de ejecutar Alembic:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://postgres:TU_PASSWORD@localhost:5432/DB"
\.venv\Scripts\alembic.exe upgrade head
```

La revisión `0001_baseline` ejecuta `backend/database/schema.sql`. Los datos iniciales se cargan por separado con `backend/database/insert.sql`.
