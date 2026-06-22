import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Trabajador(Base):
    __tablename__ = "trabajadores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(255), nullable=False)
    rol = Column(String(50), nullable=False)
    tarifa_hora = Column(Numeric(8, 2), nullable=False)
    activo = Column(Boolean, default=True, server_default=text("true"), nullable=False)
    creado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    creado_en = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=text("now()"), nullable=False)

    creador = relationship("Usuario")
    proyectos = relationship("ProyectoTrabajador", back_populates="trabajador", cascade="all, delete-orphan")
