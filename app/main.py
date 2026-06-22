from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.dependencies import get_db, get_current_user, require_rol
from app.models.usuario import Usuario
from app.routers.auth import router as auth_router
from app.routers.proyectos import router as proyectos_router
from app.routers.trabajadores import router as trabajadores_router

app = FastAPI(
    title="Construcción App",
    description="Sistema de administración de proyectos de construcción - Fase 1",
    version="1.0.0"
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",
    https_only=settings.APP_ENV.lower() in {"production", "prod"},
)

# Servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Registrar enrutadores
app.include_router(auth_router)
app.include_router(proyectos_router)
app.include_router(trabajadores_router)

templates = Jinja2Templates(directory="app/templates")

# Manejo global de excepciones HTTP para redireccionar al login en el navegador
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Si la petición es de API (JSON), retornamos JSON
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    # Redirección al login (raíz) si la sesión es inválida o expiró (401)
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        # Limpiamos la cookie de sesión por si acaso estuviera corrupta
        response.delete_cookie("session_token")
        return response

    # Respuesta amigable para acceso denegado (403)
    if exc.status_code == status.HTTP_403_FORBIDDEN:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "status_code": exc.status_code, "detail": exc.detail},
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # Respuesta genérica para otros errores
    return HTMLResponse(
        content=f"<h1>Error {exc.status_code}</h1><p>{exc.detail}</p>",
        status_code=exc.status_code
    )

@app.get("/")
async def root(request: Request, db: Session = Depends(get_db)):
    """Landing/Login: Si ya hay sesión activa redirige al dashboard; sino, muestra login."""
    token = request.cookies.get("session_token")
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            email = payload.get("sub")
            if email:
                user = db.query(Usuario).filter(Usuario.email == email, Usuario.activo == True).first()
                if user:
                    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        except JWTError:
            # Si el token es inválido o expiró, dejamos que acceda al login y limpie la sesión
            pass
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard")
async def dashboard(request: Request, current_user: Usuario = Depends(get_current_user)):
    """Enrutador de Dashboard: Detecta el rol y redirige a la vista apropiada."""
    if not current_user.rol:
        return RedirectResponse(url="/pendiente", status_code=status.HTTP_303_SEE_OTHER)
    
    if current_user.rol == "ingeniero":
        return RedirectResponse(url="/dashboard/ingeniero", status_code=status.HTTP_303_SEE_OTHER)
    elif current_user.rol == "residente":
        return RedirectResponse(url="/dashboard/residente", status_code=status.HTTP_303_SEE_OTHER)
        
    return RedirectResponse(url="/pendiente", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/pendiente")
async def pendiente(request: Request, current_user: Usuario = Depends(get_current_user)):
    """Página de espera para usuarios que no tienen un rol asignado."""
    if current_user.rol:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("pendiente.html", {"request": request, "current_user": current_user})

@app.get("/dashboard/ingeniero")
async def dashboard_ingeniero(request: Request, current_user: Usuario = Depends(require_rol("ingeniero"))):
    """Panel privado para el Ingeniero."""
    return templates.TemplateResponse(
        "dashboard/ingeniero.html", 
        {"request": request, "current_user": current_user}
    )

@app.get("/dashboard/residente")
async def dashboard_residente(request: Request, current_user: Usuario = Depends(require_rol("residente"))):
    """Panel privado para el Residente."""
    return templates.TemplateResponse(
        "dashboard/residente.html", 
        {"request": request, "current_user": current_user}
    )
