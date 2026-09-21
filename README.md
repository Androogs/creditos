# Desarrollo Créditos

Proyecto de financiación de créditos con frontend en React + TypeScript + Vite y backend en Python + FastAPI.

## Requisitos previos

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ (probado con PostgreSQL 18)

## Estructura

```text
.env.example
.gitignore
alembic.ini
alembic/
package.json
package-lock.json
.husky/
README.md
backend/
  main.py
  config.py
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
  tests/
frontend/
  .env.example
  eslint.config.js
  .prettierrc.json
  .prettierignore
  package.json
  vite.config.ts
  public/
  src/
    env.ts
    App.tsx
    main.tsx
```

## Variables de entorno

Copia los archivos de ejemplo y ajusta los valores locales:

```powershell
Copy-Item .env.example .env
Copy-Item frontend\.env.example frontend\.env
```

Edita `.env` en la raíz con tu contraseña de PostgreSQL:

```text
DATABASE_URL=postgresql+psycopg://postgres:TU_PASSWORD@localhost:5432/DB
CORS_ORIGINS=http://localhost:5173
APP_TITLE=Creditos API
APP_VERSION=0.2.0
```

El backend valida `DATABASE_URL`, `CORS_ORIGINS`, `APP_TITLE` y `APP_VERSION` con Pydantic Settings (`backend/config.py`). El frontend valida `VITE_API_URL` con Zod (`frontend/src/env.ts`).

## Calidad de código

Desde la raíz (una vez):

```powershell
npm install
```

Esto instala Husky. En cada commit, `lint-staged` ejecuta ESLint y Prettier sobre los archivos de `frontend`.

Desde `frontend`:

```powershell
npm run lint
npm run format
```

## Desarrollo local

### Backend

Desde la raíz del proyecto:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

Asegúrate de que la base de datos exista en PostgreSQL:

```sql
CREATE DATABASE "DB";
```

Aplica las migraciones:

```powershell
alembic upgrade head
```

Carga los datos iniciales (solo la primera vez, requiere que las tablas ya existan):

```powershell
& "C:\Program Files\PostgreSQL\<versión>\bin\psql.exe" -U postgres -h localhost -d DB -f backend\database\insert.sql
```

Ajusta `<versión>` (por ejemplo, `18`). También puedes cargar `insert.sql` desde pgAdmin Query Tool.

Inicia el backend:

```powershell
python -m uvicorn backend.main:app --reload
```

### Frontend

En otra terminal:

```powershell
cd frontend
npm install
npm run dev
```

El frontend queda en `http://localhost:5173` y la documentación interactiva de la API en `http://localhost:8000/api-docs` (ruta personalizada; FastAPI por defecto usa `/docs`). Las peticiones a `/api` se redirigen automáticamente al backend durante el desarrollo.

`GET /api/health` funciona sin PostgreSQL. El resto de rutas requieren `DATABASE_URL` válida.

## Pruebas

Desde la raíz del proyecto, con el venv activo:

```powershell
python -m pytest backend/tests -q
```

Configura `VITE_API_URL` en **Settings > Environment variables** del proyecto Pages con la URL pública del backend (por ejemplo `https://tu-backend.onrender.com`). Sin esta variable, el build usa `http://localhost:8000` por defecto y no funcionará en producción.

El backend FastAPI no se puede publicar como contenido estático de Pages. Publícalo como servicio Python (Render, Railway o Fly.io):

```text
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Configura `CORS_ORIGINS` con el dominio de Pages, por ejemplo `https://desarrollo-creditos.pages.dev`. El endpoint de comprobación será `https://TU-BACKEND/api/health`.

## Migraciones de base de datos

La revisión `0001_baseline` ejecuta `backend/database/schema.sql`. Para crear una nueva migración después de cambiar los modelos:

```powershell
alembic revision --autogenerate -m "descripción del cambio"
alembic upgrade head
```

Comandos útiles desde la raíz (con venv activo):

```powershell
alembic current   # muestra la revisión aplicada
alembic history   # lista las revisiones disponibles
```

Los datos iniciales se cargan por separado con `backend/database/insert.sql` (ver arriba).