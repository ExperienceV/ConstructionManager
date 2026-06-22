from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ProyectoTrabajador(Base):
    __tablename__ = "proyecto_trabajadores"

    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"), primary_key=True)
    trabajador_id = Column(UUID(as_uuid=True), ForeignKey("trabajadores.id", ondelete="CASCADE"), primary_key=True)
    asignado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    asignado_en = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=text("now()"), nullable=False)

    proyecto = relationship("Proyecto", back_populates="trabajadores")
    trabajador = relationship("Trabajador", back_populates="proyectos")
    usuario = relationship("Usuario")
