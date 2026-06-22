"""crear proyectos y personal

Revision ID: 7f2b2a9c0d31
Revises: 18b9a8640e8f
Create Date: 2026-06-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7f2b2a9c0d31"
down_revision: Union[str, None] = "18b9a8640e8f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "proyectos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("inversion_total", sa.Numeric(12, 2), nullable=True),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_estimada_fin", sa.Date(), nullable=True),
        sa.Column("estado", sa.String(length=20), server_default=sa.text("'activo'"), nullable=False),
        sa.Column("creado_por", sa.UUID(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("archivado_en", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["creado_por"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "trabajadores",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("rol", sa.String(length=50), nullable=False),
        sa.Column("tarifa_hora", sa.Numeric(8, 2), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("creado_por", sa.UUID(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["creado_por"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "proyecto_documentos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("proyecto_id", sa.UUID(), nullable=False),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("url_archivo", sa.Text(), nullable=False),
        sa.Column("public_id_cloudinary", sa.String(length=255), nullable=False),
        sa.Column("subido_por", sa.UUID(), nullable=False),
        sa.Column("subido_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["proyecto_id"], ["proyectos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subido_por"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_proyecto_documentos_proyecto_id"), "proyecto_documentos", ["proyecto_id"], unique=False)

    op.create_table(
        "proyecto_fotos_avance",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("proyecto_id", sa.UUID(), nullable=False),
        sa.Column("url_foto", sa.Text(), nullable=False),
        sa.Column("public_id_cloudinary", sa.String(length=255), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("subida_por", sa.UUID(), nullable=False),
        sa.Column("tomada_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["proyecto_id"], ["proyectos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subida_por"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_proyecto_fotos_avance_proyecto_id"), "proyecto_fotos_avance", ["proyecto_id"], unique=False)

    op.create_table(
        "proyecto_trabajadores",
        sa.Column("proyecto_id", sa.UUID(), nullable=False),
        sa.Column("trabajador_id", sa.UUID(), nullable=False),
        sa.Column("asignado_por", sa.UUID(), nullable=False),
        sa.Column("asignado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["asignado_por"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["proyecto_id"], ["proyectos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trabajador_id"], ["trabajadores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("proyecto_id", "trabajador_id"),
    )


def downgrade() -> None:
    op.drop_table("proyecto_trabajadores")
    op.drop_index(op.f("ix_proyecto_fotos_avance_proyecto_id"), table_name="proyecto_fotos_avance")
    op.drop_table("proyecto_fotos_avance")
    op.drop_index(op.f("ix_proyecto_documentos_proyecto_id"), table_name="proyecto_documentos")
    op.drop_table("proyecto_documentos")
    op.drop_table("trabajadores")
    op.drop_table("proyectos")
