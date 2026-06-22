from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProyectoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    inversion_total: Optional[Decimal] = None
    fecha_inicio: date
    fecha_estimada_fin: Optional[date] = None


class ProyectoCreate(ProyectoBase):
    pass


class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    inversion_total: Optional[Decimal] = None
    fecha_inicio: Optional[date] = None
    fecha_estimada_fin: Optional[date] = None


class ProyectoResponse(ProyectoBase):
    id: UUID
    estado: str
    creado_por: UUID
    creado_en: datetime
    archivado_en: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
