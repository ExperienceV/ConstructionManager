from datetime import datetime, timedelta, timezone
from typing import Generator
from fastapi import Depends, HTTPException, Request, status
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.usuario import Usuario

def get_db() -> Generator[Session, None, None]:
    """Inyecta la sesión de la base de datos y asegura su cierre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Genera un token JWT firmado para la sesión del usuario."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

async def get_current_user(request: Request, db: Session = Depends(get_db)) -> Usuario:
    """Extrae el JWT de la cookie 'session_token', lo valida y retorna el usuario correspondiente."""
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autorizado: Falta el token de sesión"
        )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No autorizado: Token inválido"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autorizado: Token corrupto o expirado"
        )

    user = db.query(Usuario).filter(Usuario.email == email, Usuario.activo == True).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autorizado: Usuario inexistente o inactivo"
        )
    return user

def require_rol(*roles: str):
    """Dependencia que valida si el usuario logueado tiene alguno de los roles indicados."""
    async def dependency(user: Usuario = Depends(get_current_user)):
        if user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado: Rol insuficiente"
            )
        return user
    return dependency
