from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.proyecto import Proyecto


def ecuador_now() -> datetime:
    return datetime.now(ZoneInfo(settings.TIMEZONE))


def parse_decimal(value: Optional[str]) -> Optional[Decimal]:
    if value in (None, ""):
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El valor numérico ingresado no es válido.",
        )


def parse_optional_date(value: Optional[str]) -> Optional[date]:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha ingresada no es válida.",
        )


def get_proyecto_or_404(db: Session, proyecto_id) -> Proyecto:
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado.")
    return proyecto


def ensure_proyecto_activo(proyecto: Proyecto) -> None:
    if proyecto.estado == "archivado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El proyecto está archivado y no admite nuevos cambios operativos.",
        )


def archivar_proyecto(db: Session, proyecto: Proyecto) -> Proyecto:
    proyecto.estado = "archivado"
    proyecto.archivado_en = ecuador_now()
    db.commit()
    db.refresh(proyecto)
    return proyecto
