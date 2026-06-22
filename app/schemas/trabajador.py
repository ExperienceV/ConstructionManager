from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TrabajadorBase(BaseModel):
    nombre: str
    rol: str
    tarifa_hora: Decimal
    activo: bool = True


class TrabajadorCreate(TrabajadorBase):
    pass


class TrabajadorUpdate(BaseModel):
    nombre: Optional[str] = None
    rol: Optional[str] = None
    tarifa_hora: Optional[Decimal] = None
    activo: Optional[bool] = None


class TrabajadorResponse(TrabajadorBase):
    id: UUID
    creado_por: UUID
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)
