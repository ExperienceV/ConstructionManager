# Fase 1 — Base y autenticación

**Duración estimada:** 2 – 3 semanas
**Objetivo:** el sistema puede recibir login con Google, identificar el rol del usuario y proteger rutas. Sin esto no puede construirse nada más.

---

## Estructura de carpetas del proyecto

```
construccion-app/
├── app/
│   ├── main.py                  # Entrada de FastAPI, registro de routers
│   ├── config.py                # Variables de entorno (pydantic-settings)
│   ├── database.py              # Conexión SQLAlchemy, SessionLocal
│   ├── dependencies.py          # get_db, get_current_user, require_rol
│   ├── models/
│   │   ├── __init__.py
│   │   └── usuario.py           # Modelo SQLAlchemy de usuarios
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── usuario.py           # Pydantic schemas de usuarios
│   ├── routers/
│   │   ├── __init__.py
│   │   └── auth.py              # Rutas de login/logout/callback Google
│   └── templates/
│       ├── base.html            # Layout base con navbar
│       ├── login.html           # Pantalla de login
│       ├── pendiente.html       # Cuenta sin rol asignado
│       └── dashboard/
│           ├── ingeniero.html   # Dashboard del ingeniero
│           └── residente.html   # Dashboard del residente
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 001_crear_tabla_usuarios.py
├── static/
│   └── css/
│       └── tailwind.css         # Compilado de Tailwind
├── .env                         # Variables de entorno (no commitear)
├── .env.example                 # Plantilla de variables
├── requirements.txt
└── README.md
```

---

## Dependencias (requirements.txt)

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
alembic==1.13.1
psycopg2-binary==2.9.9
pydantic-settings==2.2.1
python-multipart==0.0.9
jinja2==3.1.4
authlib==1.3.1
httpx==0.27.0
python-jose[cryptography]==3.3.0
pytz==2024.1
python-dotenv==1.0.1
```

---

## Variables de entorno (.env.example)

```env
# Base de datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/construccion_db

# Google OAuth2
GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# JWT
SECRET_KEY=genera-una-clave-aleatoria-larga-aqui
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=8

# App
APP_ENV=development
BASE_URL=http://localhost:8000
TIMEZONE=America/Guayaquil
```

---

## Tareas de esta fase

### 1. Configurar proyecto FastAPI

Crear `app/main.py`:
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routers import auth

app = FastAPI(title="Construcción App")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth.router)
```

Crear `app/config.py` con `pydantic-settings` para leer el `.env`.

Crear `app/database.py` con `create_engine` y `SessionLocal`.

### 2. Crear migración inicial de `usuarios`

```bash
alembic init alembic
alembic revision --autogenerate -m "crear tabla usuarios"
alembic upgrade head
```

El modelo debe incluir todos los campos de la tabla `usuarios` definida en `04-base-de-datos.md`.

### 3. Implementar Google OAuth2

Flujo en `app/routers/auth.py`:

- `GET /auth/login` → redirige a Google con el scope `openid email profile`
- `GET /auth/callback` → recibe el código de Google, obtiene el token, extrae email y nombre, busca o crea el usuario en BD, genera JWT, guarda en cookie HttpOnly, redirige a `/dashboard`
- `GET /auth/logout` → elimina la cookie y redirige a `/`

Usar `authlib` con `AsyncOAuth2Client` o `OAuth2Session`. Configurar las credenciales desde `config.py`.

### 4. Middleware de sesión y dependencias

Crear en `app/dependencies.py`:

```python
async def get_current_user(request: Request, db: Session) -> Usuario:
    """Lee el JWT de la cookie, valida, retorna el usuario o lanza 401."""

def require_rol(*roles: str):
    """Dependencia que lanza 403 si el usuario no tiene uno de los roles dados."""
    async def dependency(user: Usuario = Depends(get_current_user)):
        if user.rol not in roles:
            raise HTTPException(status_code=403)
        return user
    return dependency
```

### 5. Rutas de dashboard

- `GET /` → si hay sesión activa redirige a `/dashboard`, si no muestra `login.html`
- `GET /dashboard` → detecta el rol y redirige a `/dashboard/ingeniero` o `/dashboard/residente`
- `GET /dashboard/ingeniero` → protegido con `require_rol("ingeniero")`, renderiza `dashboard/ingeniero.html`
- `GET /dashboard/residente` → protegido con `require_rol("residente")`, renderiza `dashboard/residente.html`
- Si `rol = null` → muestra `pendiente.html` con mensaje "Tu cuenta está pendiente de activación"

### 6. Templates base

`templates/base.html` debe incluir:
- Navbar con nombre del usuario y botón de logout
- Bloque `{% block content %}` para el contenido de cada página
- Link a Tailwind CSS

`templates/login.html`:
- Pantalla centrada con logo y botón "Iniciar sesión con Google"

---

## Criterios de aceptación

- [ ] Un usuario puede hacer login con Google y se crea/actualiza su registro en BD
- [ ] Si `rol = null`, ve la pantalla de "pendiente de activación"
- [ ] Si `rol = ingeniero`, ve el dashboard del ingeniero
- [ ] Si `rol = residente`, ve el dashboard del residente
- [ ] Una ruta protegida con `require_rol("ingeniero")` devuelve 403 si la accede un residente
- [ ] El logout elimina la cookie y redirige al login
- [ ] La sesión expira correctamente tras 8 horas
- [ ] Las migraciones corren sin errores con `alembic upgrade head`

---

## Cómo probar manualmente

1. Correr la app: `uvicorn app.main:app --reload`
2. Ir a `http://localhost:8000`
3. Hacer login con una cuenta Google de prueba
4. Verificar en la BD que se creó el usuario con `rol = null`
5. Cambiar `rol = 'ingeniero'` manualmente en la BD
6. Recargar la página → debe mostrar dashboard del ingeniero
7. Probar logout → debe volver al login