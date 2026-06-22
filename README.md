# ConstructionManager

Sistema de administracion de proyectos de construccion. La fase 1 implementa la base FastAPI, autenticacion con Google OAuth2, sesion JWT en cookie HTTPOnly, roles y dashboards protegidos.

## Requisitos

- Python 3.12+ (probado con Python 3.13)
- Docker y Docker Compose

## Arranque local

1. Crear entorno e instalar dependencias:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

2. Copiar variables de entorno:

```bash
cp .env.example .env
```

3. Levantar PostgreSQL:

```bash
docker compose up -d db
```

4. Ejecutar migraciones:

```bash
.venv/bin/alembic upgrade head
```

5. Iniciar la app:

```bash
.venv/bin/uvicorn app.main:app --reload
```

La app queda disponible en `http://localhost:8000`.

## Autenticacion

Para Google OAuth2 real, configura en `.env`:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback`
- `MOCK_AUTH=false`

Para desarrollo sin credenciales reales, deja `MOCK_AUTH=true` y usa el formulario simulado en `/auth/login`.
