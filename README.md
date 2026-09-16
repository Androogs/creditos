# Desarrollo Créditos

Proyecto de financiación de créditos con frontend en React + TypeScript + Vite y backend en Python + FastAPI.

## Estructura

```text
backend/
  main.py
  requirements.txt
  controllers/
  services/
  repositories/
  models/
  middlewares/
  .venv/
frontend/
  public/
  src/
  package.json
  vite.config.ts
```

## Desarrollo local

Configura y ejecuta el backend desde `backend`:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
fastapi dev main.py
```

En otra terminal, instala y ejecuta el frontend desde `frontend`:

```powershell
cd frontend
npm install
npm run dev
```

El frontend queda en `http://localhost:5173` y la documentación interactiva de la API en `http://localhost:8000/docs`. Las peticiones a `/api` se redirigen automáticamente al backend durante el desarrollo.

El endpoint inicial es `GET /api/health`.
