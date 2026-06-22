from datetime import date
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.dependencies import get_db, require_rol
from app.models.proyecto import Proyecto, ProyectoDocumento, ProyectoFotoAvance
from app.models.proyecto_trabajador import ProyectoTrabajador
from app.models.trabajador import Trabajador
from app.models.usuario import Usuario
from app.services.cloudinary_service import eliminar_archivo, subir_archivo
from app.services.proyecto_service import (
    archivar_proyecto,
    ecuador_now,
    ensure_proyecto_activo,
    get_proyecto_or_404,
    parse_decimal,
    parse_optional_date,
)


router = APIRouter(prefix="/proyectos", tags=["Proyectos"])
templates = Jinja2Templates(directory="app/templates")

DOCUMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".dwg"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def redirect_to(path: str) -> RedirectResponse:
    return RedirectResponse(url=path, status_code=status.HTTP_303_SEE_OTHER)


async def validate_upload(file: UploadFile, allowed_extensions: set[str]) -> None:
    extension = Path(file.filename or "").suffix.lower()
    if extension not in allowed_extensions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de archivo no permitido.")
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo supera el máximo de 20 MB.")
    await file.seek(0)


@router.get("")
async def listar_proyectos(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero", "residente")),
):
    proyectos = db.query(Proyecto).filter(Proyecto.estado == "activo").order_by(Proyecto.creado_en.desc()).all()
    return templates.TemplateResponse(
        "proyectos/lista.html",
        {"request": request, "current_user": current_user, "user": current_user, "proyectos": proyectos, "archivados": False},
    )


@router.get("/archivados")
async def listar_proyectos_archivados(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero", "residente")),
):
    proyectos = db.query(Proyecto).filter(Proyecto.estado == "archivado").order_by(Proyecto.archivado_en.desc()).all()
    return templates.TemplateResponse(
        "proyectos/lista.html",
        {"request": request, "current_user": current_user, "user": current_user, "proyectos": proyectos, "archivados": True},
    )


@router.get("/nuevo")
async def nuevo_proyecto(request: Request, current_user: Usuario = Depends(require_rol("ingeniero"))):
    return templates.TemplateResponse(
        "proyectos/crear.html",
        {"request": request, "current_user": current_user, "user": current_user, "proyecto": None},
    )


@router.post("")
async def crear_proyecto(
    nombre: str = Form(...),
    descripcion: str = Form(None),
    inversion_total: str = Form(None),
    fecha_inicio: date = Form(...),
    fecha_estimada_fin: str = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero")),
):
    proyecto = Proyecto(
        nombre=nombre,
        descripcion=descripcion or None,
        inversion_total=parse_decimal(inversion_total),
        fecha_inicio=fecha_inicio,
        fecha_estimada_fin=parse_optional_date(fecha_estimada_fin),
        creado_por=current_user.id,
    )
    db.add(proyecto)
    db.commit()
    db.refresh(proyecto)
    return redirect_to(f"/proyectos/{proyecto.id}")


@router.get("/{proyecto_id}")
async def detalle_proyecto(
    proyecto_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero", "residente")),
):
    proyecto = get_proyecto_or_404(db, proyecto_id)
    return templates.TemplateResponse(
        "proyectos/detalle.html",
        {"request": request, "current_user": current_user, "user": current_user, "proyecto": proyecto},
    )


@router.get("/{proyecto_id}/editar")
async def editar_proyecto_form(
    proyecto_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero")),
):
    proyecto = get_proyecto_or_404(db, proyecto_id)
    ensure_proyecto_activo(proyecto)
    return templates.TemplateResponse(
        "proyectos/crear.html",
        {"request": request, "current_user": current_user, "user": current_user, "proyecto": proyecto},
    )


@router.post("/{proyecto_id}/editar")
async def actualizar_proyecto(
    proyecto_id: UUID,
    nombre: str = Form(...),
    descripcion: str = Form(None),
    inversion_total: str = Form(None),
    fecha_inicio: date = Form(...),
    fecha_estimada_fin: str = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero")),
):
    proyecto = get_proyecto_or_404(db, proyecto_id)
    ensure_proyecto_activo(proyecto)
    proyecto.nombre = nombre
    proyecto.descripcion = descripcion or None
    proyecto.inversion_total = parse_decimal(inversion_total)
    proyecto.fecha_inicio = fecha_inicio
    proyecto.fecha_estimada_fin = parse_optional_date(fecha_estimada_fin)
    db.commit()
    return redirect_to(f"/proyectos/{proyecto.id}")


@router.post("/{proyecto_id}/archivar")
async def archivar(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero")),
):
    proyecto = get_proyecto_or_404(db, proyecto_id)
    archivar_proyecto(db, proyecto)
    return redirect_to(f"/proyectos/{proyecto.id}")


@router.get("/{proyecto_id}/documentos")
async def documentos_proyecto(
    proyecto_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero", "residente")),
):
    proyecto = get_proyecto_or_404(db, proyecto_id)
    documentos = (
        db.query(ProyectoDocumento)
        .filter(ProyectoDocumento.proyecto_id == proyecto.id)
        .order_by(ProyectoDocumento.subido_en.desc())
        .all()
    )
    return templates.TemplateResponse(
        "proyectos/documentos.html",
        {
            "request": request,
            "current_user": current_user,
            "user": current_user,
            "proyecto": proyecto,
            "documentos": documentos,
        },
    )


@router.post("/{proyecto_id}/documentos")
async def subir_documento(
    proyecto_id: UUID,
    tipo: str = Form(...),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero")),
):
    proyecto = get_proyecto_or_404(db, proyecto_id)
    ensure_proyecto_activo(proyecto)
    await validate_upload(archivo, DOCUMENT_EXTENSIONS)
    result = await subir_archivo(archivo, f"proyectos/{proyecto.id}/documentos")
    documento = ProyectoDocumento(
        proyecto_id=proyecto.id,
        nombre=archivo.filename or "documento",
        tipo=tipo,
        url_archivo=result["url"],
        public_id_cloudinary=result["public_id"],
        subido_por=current_user.id,
    )
    db.add(documento)
    db.commit()
    return redirect_to(f"/proyectos/{proyecto.id}/documentos")


@router.delete("/{proyecto_id}/documentos/{doc_id}")
async def eliminar_documento(
    proyecto_id: UUID,
    doc_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero")),
):
    proyecto = get_proyecto_or_404(db, proyecto_id)
    ensure_proyecto_activo(proyecto)
    documento = db.query(ProyectoDocumento).filter_by(id=doc_id, proyecto_id=proyecto.id).first()
    if not documento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")
    eliminar_archivo(documento.public_id_cloudinary)
    db.delete(documento)
    db.commit()
    return JSONResponse({"ok": True})


@router.post("/{proyecto_id}/documentos/{doc_id}/eliminar")
async def eliminar_documento_form(proyecto_id: UUID, doc_id: UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(require_rol("ingeniero"))):
    await eliminar_documento(proyecto_id, doc_id, db, current_user)
    return redirect_to(f"/proyectos/{proyecto_id}/documentos")


@router.get("/{proyecto_id}/fotos")
async def fotos_proyecto(
    proyecto_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero", "residente")),
):
    proyecto = get_proyecto_or_404(db, proyecto_id)
    fotos = (
        db.query(ProyectoFotoAvance)
        .filter(ProyectoFotoAvance.proyecto_id == proyecto.id)
        .order_by(ProyectoFotoAvance.tomada_en.desc())
        .all()
    )
    return templates.TemplateResponse(
        "proyectos/fotos.html",
        {"request": request, "current_user": current_user, "user": current_user, "proyecto": proyecto, "fotos": fotos},
    )


@router.post("/{proyecto_id}/fotos")
async def subir_foto(
    proyecto_id: UUID,
    descripcion: str = Form(None),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero", "residente")),
):
    proyecto = get_proyecto_or_404(db, proyecto_id)
    ensure_proyecto_activo(proyecto)
    await validate_upload(archivo, IMAGE_EXTENSIONS)
    result = await subir_archivo(archivo, f"proyectos/{proyecto.id}/fotos")
    foto = ProyectoFotoAvance(
        proyecto_id=proyecto.id,
        url_foto=result["url"],
        public_id_cloudinary=result["public_id"],
        descripcion=descripcion or None,
        subida_por=current_user.id,
        tomada_en=ecuador_now(),
    )
    db.add(foto)
    db.commit()
    return redirect_to(f"/proyectos/{proyecto.id}/fotos")


@router.delete("/{proyecto_id}/fotos/{foto_id}")
async def eliminar_foto(
    proyecto_id: UUID,
    foto_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero")),
):
    proyecto = get_proyecto_or_404(db, proyecto_id)
    ensure_proyecto_activo(proyecto)
    foto = db.query(ProyectoFotoAvance).filter_by(id=foto_id, proyecto_id=proyecto.id).first()
    if not foto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto no encontrada.")
    eliminar_archivo(foto.public_id_cloudinary)
    db.delete(foto)
    db.commit()
    return JSONResponse({"ok": True})


@router.post("/{proyecto_id}/fotos/{foto_id}/eliminar")
async def eliminar_foto_form(proyecto_id: UUID, foto_id: UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(require_rol("ingeniero"))):
    await eliminar_foto(proyecto_id, foto_id, db, current_user)
    return redirect_to(f"/proyectos/{proyecto_id}/fotos")


@router.get("/{proyecto_id}/personal")
async def personal_proyecto(
    proyecto_id: UUID,
    request: Request,
    q: str = "",
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero", "residente")),
):
    proyecto = get_proyecto_or_404(db, proyecto_id)
    asignaciones = (
        db.query(ProyectoTrabajador)
        .options(joinedload(ProyectoTrabajador.trabajador))
        .filter(ProyectoTrabajador.proyecto_id == proyecto.id)
        .order_by(ProyectoTrabajador.asignado_en.desc())
        .all()
    )
    asignados_ids = [item.trabajador_id for item in asignaciones]
    disponibles_query = db.query(Trabajador).filter(Trabajador.activo == True)
    if asignados_ids:
        disponibles_query = disponibles_query.filter(Trabajador.id.notin_(asignados_ids))
    if q:
        disponibles_query = disponibles_query.filter(Trabajador.nombre.ilike(f"%{q}%"))
    disponibles = disponibles_query.order_by(Trabajador.nombre.asc()).limit(20).all()
    return templates.TemplateResponse(
        "proyectos/personal.html",
        {
            "request": request,
            "current_user": current_user,
            "user": current_user,
            "proyecto": proyecto,
            "asignaciones": asignaciones,
            "disponibles": disponibles,
            "q": q,
        },
    )


@router.post("/{proyecto_id}/personal")
async def asignar_personal(
    proyecto_id: UUID,
    trabajador_id: UUID = Form(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero", "residente")),
):
    proyecto = get_proyecto_or_404(db, proyecto_id)
    ensure_proyecto_activo(proyecto)
    trabajador = db.query(Trabajador).filter(Trabajador.id == trabajador_id, Trabajador.activo == True).first()
    if not trabajador:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trabajador no encontrado.")
    exists = db.query(ProyectoTrabajador).filter_by(proyecto_id=proyecto.id, trabajador_id=trabajador.id).first()
    if not exists:
        db.add(ProyectoTrabajador(proyecto_id=proyecto.id, trabajador_id=trabajador.id, asignado_por=current_user.id))
        db.commit()
    return redirect_to(f"/proyectos/{proyecto.id}/personal")


@router.delete("/{proyecto_id}/personal/{trabajador_id}")
async def quitar_personal(
    proyecto_id: UUID,
    trabajador_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol("ingeniero", "residente")),
):
    proyecto = get_proyecto_or_404(db, proyecto_id)
    ensure_proyecto_activo(proyecto)
    asignacion = db.query(ProyectoTrabajador).filter_by(proyecto_id=proyecto.id, trabajador_id=trabajador_id).first()
    if not asignacion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada.")
    db.delete(asignacion)
    db.commit()
    return JSONResponse({"ok": True})


@router.post("/{proyecto_id}/personal/{trabajador_id}/quitar")
async def quitar_personal_form(proyecto_id: UUID, trabajador_id: UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(require_rol("ingeniero", "residente"))):
    await quitar_personal(proyecto_id, trabajador_id, db, current_user)
    return redirect_to(f"/proyectos/{proyecto_id}/personal")
