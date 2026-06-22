from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional

class UsuarioBase(BaseModel):
    email: EmailStr
    nombre: str
    rol: Optional[str] = None
    activo: bool = True

class UsuarioCreate(UsuarioBase):
    pass

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    rol: Optional[str] = None
    activo: Optional[bool] = None

class UsuarioResponse(UsuarioBase):
    id: UUID
    creado_en: datetime
    ultimo_login: datetime

    model_config = ConfigDict(from_attributes=True)
