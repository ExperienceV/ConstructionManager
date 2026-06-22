from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth

from app.config import settings
from app.dependencies import get_db, create_access_token
from app.models.usuario import Usuario

router = APIRouter(prefix="/auth", tags=["Autenticación"])
templates = Jinja2Templates(directory="app/templates")

# Configurar OAuth de Google
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)

def use_secure_cookies() -> bool:
    return settings.APP_ENV.lower() in {"production", "prod"}

def process_user_login(db: Session, email: str, nombre: str) -> Usuario:
    """Busca al usuario por email; si no existe, lo crea con rol NULL."""
    user = db.query(Usuario).filter(Usuario.email == email).first()
    now_utc = datetime.now(timezone.utc)
    if user:
        user.nombre = nombre
        user.ultimo_login = now_utc
        db.commit()
        db.refresh(user)
    else:
        user = Usuario(
            email=email,
            nombre=nombre,
            rol=None,  # Pendiente de asignación manual
            activo=True,
            creado_en=now_utc,
            ultimo_login=now_utc
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@router.get("/login")
async def login(request: Request):
    """Redirige al login de Google o muestra el panel de login simulado si MOCK_AUTH=true."""
    if settings.MOCK_AUTH:
        return templates.TemplateResponse("mock_login.html", {"request": request})
    
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    """Callback de Google OAuth2 que procesa el login e inyecta la cookie de sesión JWT."""
    if settings.MOCK_AUTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mock auth está activo. Usa el endpoint de login de prueba."
        )
    
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en callback de Google: {str(e)}"
        )
    
    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo obtener la información del usuario de Google."
        )
    
    email = user_info.get("email")
    nombre = user_info.get("name") or email
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google no devolvió un email válido para el usuario."
        )
    
    user = process_user_login(db, email, nombre)
    
    # Si el usuario está inactivo, rechazar acceso
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta de usuario desactivada."
        )
    
    access_token = create_access_token(data={"sub": user.email})
    
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="session_token",
        value=access_token,
        httponly=True,
        max_age=settings.JWT_EXPIRE_HOURS * 3600,
        expires=settings.JWT_EXPIRE_HOURS * 3600,
        samesite="lax",
        secure=use_secure_cookies()
    )
    return response

@router.post("/mock-login")
async def mock_login(
    request: Request,
    email: str = Form(...),
    nombre: str = Form(...),
    rol: str = Form(None),
    db: Session = Depends(get_db)
):
    """Endpoint exclusivo de desarrollo para simular login con distintos roles."""
    if not settings.MOCK_AUTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El inicio de sesión simulado no está activo en este entorno."
        )
    
    # Tratamiento de rol nulo
    if rol == "null" or rol == "":
        rol = None
    elif rol not in {"ingeniero", "residente"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rol de prueba inválido."
        )
        
    user = db.query(Usuario).filter(Usuario.email == email).first()
    now_utc = datetime.now(timezone.utc)
    if user:
        user.nombre = nombre
        user.rol = rol
        user.ultimo_login = now_utc
        db.commit()
        db.refresh(user)
    else:
        user = Usuario(
            email=email,
            nombre=nombre,
            rol=rol,
            activo=True,
            creado_en=now_utc,
            ultimo_login=now_utc
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta de usuario desactivada."
        )
        
    access_token = create_access_token(data={"sub": user.email})
    
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="session_token",
        value=access_token,
        httponly=True,
        max_age=settings.JWT_EXPIRE_HOURS * 3600,
        expires=settings.JWT_EXPIRE_HOURS * 3600,
        samesite="lax",
        secure=use_secure_cookies()
    )
    return response

@router.get("/logout")
async def logout():
    """Cierra la sesión del usuario eliminando la cookie JWT."""
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session_token")
    return response
