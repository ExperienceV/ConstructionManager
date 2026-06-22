# Fase 2 — Proyectos y personal

**Duración estimada:** 3 – 4 semanas
**Prerequisito:** Fase 1 completada y funcionando.
**Objetivo:** el ingeniero puede crear y gestionar proyectos con documentos y fotos. El residente puede gestionar trabajadores y asignarlos a obras.

---

## Nuevas tablas en esta fase

Crear migraciones para:
- `proyectos`
- `proyecto_documentos`
- `proyecto_fotos_avance`
- `trabajadores`
- `proyecto_trabajadores`

Ver esquema completo en `04-base-de-datos.md`.

---

## Estructura de carpetas adicional

```
app/
├── models/
│   ├── proyecto.py
│   ├── trabajador.py
│   └── proyecto_trabajador.py
├── schemas/
│   ├── proyecto.py
│   └── trabajador.py
├── routers/
│   ├── proyectos.py
│   └── trabajadores.py
├── services/
│   ├── cloudinary_service.py    # Subida y eliminación de archivos
│   └── proyecto_service.py     # Lógica de negocio de proyectos
└── templates/
    ├── proyectos/
    │   ├── lista.html
    │   ├── detalle.html
    │   ├── crear.html
    │   ├── documentos.html
    │   └── fotos.html
    └── trabajadores/
        ├── lista.html
        ├── perfil.html
        └── crear.html
```

---

## Configuración de Cloudinary

Agregar al `.env`:
```env
CLOUDINARY_CLOUD_NAME=tu-cloud-name
CLOUDINARY_API_KEY=tu-api-key
CLOUDINARY_API_SECRET=tu-api-secret
```

Agregar al `requirements.txt`:
```
cloudinary==1.40.0
```

`app/services/cloudinary_service.py` debe exponer:
- `subir_archivo(file: UploadFile, carpeta: str) -> dict` → retorna `{url, public_id}`
- `eliminar_archivo(public_id: str) -> bool`

Las carpetas en Cloudinary se organizan así:
- `proyectos/{proyecto_id}/documentos/`
- `proyectos/{proyecto_id}/fotos/`
- `proyectos/{proyecto_id}/comprobantes/`

---

## Tareas de esta fase

### 1. Módulo de proyectos

Rutas en `app/routers/proyectos.py`:

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| GET | `/proyectos` | Ing + Res | Lista proyectos activos |
| GET | `/proyectos/archivados` | Ing + Res | Lista proyectos archivados |
| GET | `/proyectos/nuevo` | Solo Ing | Formulario de creación |
| POST | `/proyectos` | Solo Ing | Crear proyecto |
| GET | `/proyectos/{id}` | Ing + Res | Detalle del proyecto |
| GET | `/proyectos/{id}/editar` | Solo Ing | Formulario de edición |
| POST | `/proyectos/{id}/editar` | Solo Ing | Actualizar proyecto |
| POST | `/proyectos/{id}/archivar` | Solo Ing | Archivar proyecto |

**Reglas de negocio en el servicio:**
- Al archivar, guardar `archivado_en = now()` en hora Ecuador y cambiar `estado = 'archivado'`
- Los proyectos archivados no permiten agregar trabajadores, documentos nuevos ni registros de horario

### 2. Módulo de documentos

Rutas:

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| GET | `/proyectos/{id}/documentos` | Ing + Res | Ver documentos del proyecto |
| POST | `/proyectos/{id}/documentos` | Solo Ing | Subir documento |
| DELETE | `/proyectos/{id}/documentos/{doc_id}` | Solo Ing | Eliminar documento |

La subida usa `multipart/form-data`. El archivo se sube a Cloudinary y se guarda la URL en BD. Tipos aceptados: PDF, imágenes (jpg, png, webp), archivos DWG. Tamaño máximo: 20 MB.

### 3. Módulo de fotos de avance

Rutas:

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| GET | `/proyectos/{id}/fotos` | Ing + Res | Galería de fotos |
| POST | `/proyectos/{id}/fotos` | Ing + Res | Subir foto |
| DELETE | `/proyectos/{id}/fotos/{foto_id}` | Solo Ing | Eliminar foto |

La galería muestra las fotos ordenadas por `tomada_en` descendente (más reciente primero). La fecha `tomada_en` se asigna automáticamente en hora Ecuador al momento de la subida.

### 4. Módulo de trabajadores

Rutas en `app/routers/trabajadores.py`:

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| GET | `/personal` | Ing + Res | Lista global de trabajadores activos |
| GET | `/personal/nuevo` | Ing + Res | Formulario de creación |
| POST | `/personal` | Ing + Res | Crear trabajador |
| GET | `/personal/{id}` | Ing + Res | Perfil del trabajador |
| POST | `/personal/{id}/editar` | Ing + Res | Editar datos |
| POST | `/personal/{id}/desactivar` | Ing + Res | Desactivar (soft delete) |

**Regla de soft delete:** si el trabajador tiene registros en `registros_horario` o `ciclos_pago`, no se elimina físicamente — se marca `activo = false`. Si no tiene registros, se puede eliminar físicamente.

### 5. Asignación de trabajadores a proyectos

Desde la vista `/proyectos/{id}/personal`:

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| GET | `/proyectos/{id}/personal` | Ing + Res | Ver trabajadores del proyecto |
| POST | `/proyectos/{id}/personal` | Ing + Res | Asignar trabajador al proyecto |
| DELETE | `/proyectos/{id}/personal/{trabajador_id}` | Ing + Res | Quitar del proyecto |

El formulario de asignación incluye un campo de búsqueda que filtra trabajadores activos que no estén ya asignados al proyecto. La búsqueda es por nombre (ILIKE).

---

## Templates clave

### `proyectos/lista.html`
- Cards con nombre del proyecto, fechas, estado
- Barra de progreso (gasto vs inversión) — **solo visible para el ingeniero**
- Botón "Nuevo proyecto" — **solo visible para el ingeniero**

### `proyectos/detalle.html`
- Tabs: Información | Personal | Documentos | Fotos | Finanzas (esta última solo para Ing.)
- La tab "Finanzas" no debe renderizarse en el HTML si el usuario es residente (verificar en el template con `{% if user.rol == 'ingeniero' %}`)

### `trabajadores/lista.html`
- Tabla con nombre, rol, tarifa/hora, proyectos asignados, días en ciclo actual
- La columna "tarifa/hora" — **solo visible para el ingeniero**

---

## Criterios de aceptación

- [ ] El ingeniero puede crear un proyecto con todos sus campos
- [ ] El ingeniero puede subir documentos y fotos al proyecto
- [ ] El residente puede ver documentos y subir fotos, pero no subir documentos
- [ ] Se puede archivar un proyecto y queda en solo lectura
- [ ] Se puede crear un trabajador con nombre, rol y tarifa
- [ ] Se puede asignar un trabajador a uno o múltiples proyectos
- [ ] La tab "Finanzas" no aparece en el HTML cuando accede el residente
- [ ] La columna "tarifa/hora" en la lista de trabajadores no aparece para el residente
- [ ] El soft delete funciona: trabajadores con historial quedan como `activo = false`