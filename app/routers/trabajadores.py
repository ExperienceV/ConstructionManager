from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session, joinedload

from app.dependencies import get_db, require_rol
from app.models.proyecto_trabajador import ProyectoTrabajador
from app.models.trabajador import Trabajador
from app.models.usuario import Usuario


router = APIRouter(prefix="/personal", tags=["Personal"])
templates = Jinja2Templates(directory="app/templates")

ROLES_TRABAJADOR = ["Contratista", "Electricista", "Pintor", "Albañil", "Oficial Jr", "Oficial Sr", "Maestro"]


def redirect_to(path: str) -> RedirectResponse:
    return RedirectResponse(url=path, status_code=status.HTTP_303_SEE_OTHER)


def get_trabajador_or_404(db: Session, trabajador_id: UUID) -> Trabajador:
    trabajador = db.query(Trabajador).filter(Trabajador.id == trabajador_id).first()
    if not trabajador:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trabajador no encontrado.")
    return trabajador


def dias_en_ciclo_actual(db: Session, trabajador_id: UUID) -> int:
    inspector = inspect(db.bind)
    if not inspector.has_table("registros_horario"):
        return 0
    if inspector.has_table("ciclos_pago"):
        result = db.execute(
            text(
                """
                SELECT COUNT(DISTINCT rh.fecha)
                FROM registros_horario rh
                WHERE rh.trabajador_id = :trabajador_id
                  AND rh.fecha > COALESCE(
                    (SELECT MAX(cp.periodo_fin) FROM ciclos_pago cp WHERE cp.trabajador_id = :trabajador_id),
                    '1900-01-01'::date
                  )
                """
            ),
            {"trabajador_id": trabajador_id},
        ).scalar()
    else:
        result = db.execute(
            text("SELECT COUNT(DISTINCT fecha) FROM registros_horario WHERE trabajador_id = :trabajador_id"),
            {"trabajador_id": trabajador_id},
        ).scalar()
    return int(result or 0)


def tiene_historial(db: Session, trabajador_id: UUID) -> bool:
    inspector = inspect(db.bind)
    for table_name in ("registros_horario", "ciclos_pago"):
        if inspector.has_table(table_name):
            count = db.execute(text(f"SELECT COUNT(*) FROM {table_name} WHERE trabajador_id = :trabajador_id"), {"trabajador_id": trabajador_id}).scalar()
            if count:
                return True
    return False


@router.get("")
async def listar_trabajadores(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero", "residente")),
):
    trabajadores = (
        db.query(Trabajador)
        .options(joinedload(Trabajador.proyectos).joinedload(ProyectoTrabajador.proyecto))
        .filter(Trabajador.activo == True)
        .order_by(Trabajador.nombre.asc())
        .all()
    )
    dias_por_trabajador = {trabajador.id: dias_en_ciclo_actual(db, trabajador.id) for trabajador in trabajadores}
    return templates.TemplateResponse(
        "trabajadores/lista.html",
        {
            "request": request,
            "current_user": current_user,
            "user": current_user,
            "trabajadores": trabajadores,
            "dias_por_trabajador": dias_por_trabajador,
        },
    )


@router.get("/nuevo")
async def nuevo_trabajador(request: Request, current_user: Usuario = Depends(require_rol("ingeniero", "residente"))):
    return templates.TemplateResponse(
        "trabajadores/crear.html",
        {"request": request, "current_user": current_user, "user": current_user, "trabajador": None, "roles": ROLES_TRABAJADOR},
    )


@router.post("")
async def crear_trabajador(
    nombre: str = Form(...),
    rol: str = Form(...),
    tarifa_hora: Decimal = Form(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero", "residente")),
):
    trabajador = Trabajador(nombre=nombre, rol=rol, tarifa_hora=tarifa_hora, creado_por=current_user.id)
    db.add(trabajador)
    db.commit()
    db.refresh(trabajador)
    return redirect_to(f"/personal/{trabajador.id}")


@router.get("/{trabajador_id}")
async def perfil_trabajador(
    trabajador_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero", "residente")),
):
    trabajador = get_trabajador_or_404(db, trabajador_id)
    return templates.TemplateResponse(
        "trabajadores/perfil.html",
        {
            "request": request,
            "current_user": current_user,
            "user": current_user,
            "trabajador": trabajador,
            "dias_en_ciclo": dias_en_ciclo_actual(db, trabajador.id),
        },
    )


@router.get("/{trabajador_id}/editar")
async def editar_trabajador_form(
    trabajador_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero", "residente")),
):
    trabajador = get_trabajador_or_404(db, trabajador_id)
    return templates.TemplateResponse(
        "trabajadores/crear.html",
        {"request": request, "current_user": current_user, "user": current_user, "trabajador": trabajador, "roles": ROLES_TRABAJADOR},
    )


@router.post("/{trabajador_id}/editar")
async def editar_trabajador(
    trabajador_id: UUID,
    nombre: str = Form(...),
    rol: str = Form(...),
    tarifa_hora: Decimal = Form(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero", "residente")),
):
    trabajador = get_trabajador_or_404(db, trabajador_id)
    trabajador.nombre = nombre
    trabajador.rol = rol
    trabajador.tarifa_hora = tarifa_hora
    trabajador.activo = True
    db.commit()
    return redirect_to(f"/personal/{trabajador.id}")


@router.post("/{trabajador_id}/desactivar")
async def desactivar_trabajador(
    trabajador_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero", "residente")),
):
    trabajador = get_trabajador_or_404(db, trabajador_id)
    if tiene_historial(db, trabajador.id):
        trabajador.activo = False
    else:
        db.delete(trabajador)
    db.commit()
    return redirect_to("/personal")
