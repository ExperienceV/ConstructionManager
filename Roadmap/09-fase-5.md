# Fase 5 — Reportes, notificaciones y despliegue

**Duración estimada:** 2 – 3 semanas
**Prerequisito:** Fase 4 completada.
**Objetivo:** la app está lista para producción con reportes exportables, notificaciones por email, búsquedas/filtros y despliegue en Railway o Render.

---

## Dependencias adicionales (agregar a requirements.txt)

```
openpyxl==3.1.2          # Reportes Excel
reportlab==4.2.0          # Reportes PDF
apscheduler==3.10.4       # Tareas programadas (notificaciones)
resend==2.0.0             # Envío de emails (o usar sendgrid)
```

---

## Estructura de carpetas adicional

```
app/
├── routers/
│   └── reportes.py
├── services/
│   ├── reporte_service.py       # Generación de Excel y PDF
│   └── notificacion_service.py  # Envío de emails y scheduler
└── templates/
    └── emails/
        ├── proyecto_por_vencer.html
        └── proyecto_vencido.html
```

---

## Tareas de esta fase

### 1. Reportes exportables (solo Ingeniero)

Ruta: `GET /proyectos/{id}/reporte?formato=excel` o `?formato=pdf`

Acceso: solo Ingeniero.

#### Reporte Excel (`openpyxl`)

El archivo Excel debe tener estas hojas:

**Hoja 1 — Resumen financiero**
| Campo | Valor |
|---|---|
| Proyecto | Edificio Norte |
| Fecha de inicio | 01/01/2025 |
| Fecha estimada de fin | 30/06/2025 |
| Estado | Activo |
| Inversión total | $85,000.00 |
| Costo laboral | $12,450.00 |
| Costo de materiales | $8,320.00 |
| Gasto total | $20,770.00 |
| Diferencia | $64,230.00 |

**Hoja 2 — Personal y horas**
| Trabajador | Rol | Tarifa/h | Horas totales | Costo total |
|---|---|---|---|---|
| Juan Pérez | Albañil | $5.00 | 320h | $1,600.00 |
| ... | | | | |

**Hoja 3 — Gastos de materiales**
| Fecha | Descripción | Monto | Registrado por |
|---|---|---|---|
| 15/01/2025 | Cemento 20 sacos | $180.00 | María G. |
| ... | | | |

**Hoja 4 — Historial de cortes**
| Trabajador | Período | Días | Tarifa/h | Monto |
|---|---|---|---|---|
| Juan Pérez | 01/01 → 15/01 | 15 | $5.00 | $750.00 |
| ... | | | | |

#### Reporte PDF (`reportlab`)

Una sola página por sección con el mismo contenido que Excel, más:
- Logo/encabezado con nombre del proyecto y fecha de generación
- Tabla resumen financiera destacada
- Tabla de personal y costos
- Tabla de materiales
- Pie de página con "Generado el {fecha} por {nombre del usuario}"

No incluir miniaturas de fotos en el PDF (agrega complejidad innecesaria en esta fase).

#### Implementación

```python
# app/services/reporte_service.py

def generar_excel(proyecto_id: UUID, db: Session) -> bytes:
    """Retorna el archivo Excel como bytes para enviar como respuesta."""
    
def generar_pdf(proyecto_id: UUID, db: Session) -> bytes:
    """Retorna el archivo PDF como bytes."""
```

La ruta devuelve el archivo como `StreamingResponse` con el header `Content-Disposition: attachment`:

```python
@router.get("/proyectos/{id}/reporte")
async def descargar_reporte(
    id: UUID,
    formato: str = "excel",
    usuario = Depends(require_rol("ingeniero")),
    db: Session = Depends(get_db)
):
    if formato == "excel":
        contenido = generar_excel(id, db)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"reporte_{id}.xlsx"
    else:
        contenido = generar_pdf(id, db)
        media_type = "application/pdf"
        filename = f"reporte_{id}.pdf"
    
    return StreamingResponse(
        io.BytesIO(contenido),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

### 2. Sistema de notificaciones por email

Agregar al `.env`:
```env
RESEND_API_KEY=re_tu-api-key
EMAIL_FROM=notificaciones@tudominio.com
```

#### Scheduler

Usar `APScheduler` con el scheduler de FastAPI:

```python
# app/main.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def start_scheduler():
    scheduler.add_job(
        verificar_proyectos_por_vencer,
        "cron",
        hour=8,           # 8:00 AM
        minute=0,
        timezone="America/Guayaquil"
    )
    scheduler.start()

@app.on_event("shutdown")
async def stop_scheduler():
    scheduler.shutdown()
```

#### Lógica de notificaciones

`app/services/notificacion_service.py`:

```python
async def verificar_proyectos_por_vencer(db: Session):
    """Corre cada día a las 8:00 AM hora Ecuador."""
    hoy = date.today()  # en hora Ecuador
    
    proyectos = db.query(Proyecto).filter(
        Proyecto.estado == "activo",
        Proyecto.fecha_estimada_fin.isnot(None)
    ).all()
    
    for proyecto in proyectos:
        dias_restantes = (proyecto.fecha_estimada_fin - hoy).days
        ingeniero = db.get(Usuario, proyecto.creado_por)
        
        if dias_restantes == 7:
            await enviar_email_por_vencer(ingeniero.email, proyecto, dias_restantes)
        elif dias_restantes == 1:
            await enviar_email_por_vencer(ingeniero.email, proyecto, dias_restantes)
        elif dias_restantes < 0:
            await enviar_email_vencido(ingeniero.email, proyecto, abs(dias_restantes))
```

Los emails usan templates HTML en `templates/emails/`. Deben ser simples, sin imágenes externas, con estilos inline para compatibilidad con clientes de email.

### 3. Búsqueda y filtros

Agregar filtros en las vistas principales:

**Lista de proyectos:**
- Filtro por estado: `activo | archivado | todos`
- Búsqueda por nombre (ILIKE)

**Lista de trabajadores:**
- Búsqueda por nombre
- Filtro por rol

**Lista de gastos de materiales:**
- Filtro por rango de fechas
- Búsqueda en descripción

Los filtros se implementan como parámetros GET en las rutas y se procesan en la consulta SQLAlchemy. Los formularios de filtro usan `GET` para que los filtros queden en la URL y sean compartibles.

### 4. Pruebas

Instalar:
```
pytest==8.2.0
pytest-asyncio==0.23.6
httpx==0.27.0
```

Estructura de pruebas:
```
tests/
├── conftest.py              # Base de datos de prueba, fixtures de usuarios
├── test_auth.py             # Login, logout, protección de rutas
├── test_proyectos.py        # CRUD de proyectos, permisos
├── test_horarios.py         # Registro de asistencia, validaciones
├── test_ciclos_pago.py      # Generación de cortes, contador de días
└── test_financiero.py       # Cálculos del panel financiero
```

Casos críticos que deben tener prueba:
- El ciclo de pago se genera exactamente al día 15, no antes ni después
- La tarifa del corte no cambia si se edita la tarifa del trabajador después
- Un residente no puede acceder a rutas financieras (403)
- Un proyecto archivado no acepta nuevos registros de asistencia

### 5. Despliegue en Railway

#### Archivos necesarios

`Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

`runtime.txt`:
```
python-3.12.3
```

#### Pasos de despliegue

1. Crear cuenta en [railway.app](https://railway.app)
2. Nuevo proyecto → "Deploy from GitHub repo"
3. Agregar servicio PostgreSQL desde el marketplace de Railway
4. En variables de entorno, agregar todas las del `.env` (excepto DATABASE_URL que Railway genera automáticamente)
5. En "Settings" del servicio web, verificar que el Procfile sea detectado
6. Al primer deploy, correr migraciones: en la terminal de Railway ejecutar `alembic upgrade head`
7. Configurar dominio personalizado si se tiene uno

#### Variables de entorno en Railway

Copiar todas las variables del `.env.example` y completarlas con los valores de producción:
- `DATABASE_URL` → se genera automáticamente por Railway al agregar PostgreSQL
- `GOOGLE_REDIRECT_URI` → cambiar a la URL de producción: `https://tu-app.railway.app/auth/callback`
- `APP_ENV` → `production`
- `BASE_URL` → `https://tu-app.railway.app`

#### HTTPS y OAuth

Railway provee HTTPS automáticamente. Antes de ir a producción:
1. En Google Cloud Console, agregar la URL de producción a los "Authorized redirect URIs" de las credenciales OAuth
2. Verificar que la cookie de sesión usa `secure=True` en producción (condicional según `APP_ENV`)

---

## Criterios de aceptación

- [ ] El reporte Excel descarga correctamente con las 4 hojas y datos reales
- [ ] El reporte PDF descarga correctamente con el resumen financiero
- [ ] Las notificaciones de email se envían a las 8:00 AM hora Ecuador
- [ ] Un proyecto a 7 días de vencer dispara el email
- [ ] Un proyecto a 1 día de vencer dispara el email
- [ ] Un proyecto vencido (fecha pasada y aún activo) dispara el email
- [ ] Los filtros y búsqueda funcionan en proyectos, trabajadores y gastos
- [ ] Las pruebas del ciclo de pago pasan sin errores
- [ ] Las pruebas de permisos (403) pasan sin errores
- [ ] La app está desplegada y accesible desde `https://tu-app.railway.app`
- [ ] El login con Google funciona en producción con la URL correcta en OAuth
- [ ] `alembic upgrade head` corre sin errores en el servidor de producción