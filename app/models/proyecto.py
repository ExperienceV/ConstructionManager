import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Proyecto(Base):
    __tablename__ = "proyectos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    inversion_total = Column(Numeric(12, 2), nullable=True)
    fecha_inicio = Column(Date, nullable=False)
    fecha_estimada_fin = Column(Date, nullable=True)
    estado = Column(String(20), nullable=False, default="activo", server_default=text("'activo'"))
    creado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    creado_en = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=text("now()"), nullable=False)
    archivado_en = Column(DateTime(timezone=True), nullable=True)

    creador = relationship("Usuario")
    documentos = relationship("ProyectoDocumento", back_populates="proyecto", cascade="all, delete-orphan")
    fotos = relationship("ProyectoFotoAvance", back_populates="proyecto", cascade="all, delete-orphan")
    trabajadores = relationship("ProyectoTrabajador", back_populates="proyecto", cascade="all, delete-orphan")


class ProyectoDocumento(Base):
    __tablename__ = "proyecto_documentos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String(255), nullable=False)
    tipo = Column(String(50), nullable=False)
    url_archivo = Column(Text, nullable=False)
    public_id_cloudinary = Column(String(255), nullable=False)
    subido_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    subido_en = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=text("now()"), nullable=False)

    proyecto = relationship("Proyecto", back_populates="documentos")
    usuario = relationship("Usuario")


class ProyectoFotoAvance(Base):
    __tablename__ = "proyecto_fotos_avance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False, index=True)
    url_foto = Column(Text, nullable=False)
    public_id_cloudinary = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    subida_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    tomada_en = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=text("now()"), nullable=False)

    proyecto = relationship("Proyecto", back_populates="fotos")
    usuario = relationship("Usuario")
