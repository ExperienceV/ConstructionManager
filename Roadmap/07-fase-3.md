# Fase 3 — Horarios y asistencia

**Duración estimada:** 3 – 4 semanas
**Prerequisito:** Fase 2 completada.
**Objetivo:** el residente puede registrar la asistencia diaria de los trabajadores con bloques de tiempo por obra. El sistema contabiliza días trabajados para el ciclo de pago.

---

## Nuevas tablas en esta fase

Crear migraciones para:
- `registros_horario`
- `bloques_horario`

Ver esquema completo en `04-base-de-datos.md`.

---

## Estructura de carpetas adicional

```
app/
├── models/
│   ├── registro_horario.py
│   └── bloque_horario.py
├── schemas/
│   └── horario.py
├── routers/
│   └── horarios.py
├── services/
│   └── horario_service.py       # Lógica de días trabajados y ciclo
└── templates/
    └── horarios/
        ├── registrar.html       # Formulario de asistencia (mobile-first)
        ├── calendario.html      # Vista de calendario por trabajador
        └── detalle_dia.html     # Detalle de bloques de un día
```

---

## Tareas de esta fase

### 1. Formulario de registro de asistencia

Ruta principal: `GET /asistencia/registrar`

Esta es la pantalla más usada del sistema (el residente la abre desde el celular cada día). Debe ser simple y rápida:

1. **Selección de trabajador:** input con autocompletado que filtra trabajadores activos por nombre. En mobile muestra lista desplegable.
2. **Fecha:** date picker con valor por defecto = hoy en hora Ecuador. Permite registrar días anteriores.
3. **Bloques de tiempo:** sección que empieza con un bloque vacío y permite agregar más.
   - Cada bloque: `hora_entrada (time)` + `hora_salida (time)` + `proyecto (select)`
   - Botón "+ Agregar bloque"
   - Botón "×" para eliminar un bloque (mínimo 1 bloque requerido)
4. **Botón guardar:** envía el formulario completo.

Si ya existe un registro para ese trabajador en esa fecha, el formulario se precarga con los datos existentes (modo edición).

**Ruta POST:** `POST /asistencia/registrar`

Lógica en `horario_service.py`:
```python
def guardar_registro(trabajador_id, fecha, bloques, usuario_id, db):
    # 1. Buscar si ya existe registro para ese trabajador+fecha
    # 2. Si existe: actualizar bloques (eliminar los anteriores, insertar los nuevos)
    #    Guardar editado_por y editado_en
    # 3. Si no existe: crear registro y bloques
    # 4. Para cada bloque calcular horas_trabajadas = hora_salida - hora_entrada
    # 5. Retornar el registro guardado
```

### 2. API de autocompletado de trabajadores

Necesaria para el formulario mobile:

```
GET /api/v1/trabajadores/buscar?q={nombre}&proyecto_id={id}
```

Retorna JSON con lista de trabajadores cuyo nombre contiene `q` (ILIKE). Si se pasa `proyecto_id`, filtra solo los asignados a esa obra. Máximo 10 resultados.

### 3. Validaciones del registro

En el servicio o en el schema Pydantic:
- `hora_salida` debe ser mayor que `hora_entrada`
- Cada bloque debe tener un proyecto válido y activo
- `horas_trabajadas` no puede ser negativo ni mayor a 24
- La fecha no puede ser futura (en hora Ecuador)
- El trabajador debe estar activo

### 4. Vista de calendario por trabajador

Ruta: `GET /personal/{id}/horarios`

Muestra un calendario mensual del trabajador con:
- Días trabajados marcados con color
- Al hacer clic en un día, muestra el detalle de bloques
- Resumen debajo del calendario: total de días trabajados en el mes, total de horas
- **Contador del ciclo actual:** "X de 15 días trabajados en el ciclo actual"

El calendario debe mostrar el mes actual por defecto con navegación a meses anteriores.

### 5. Detalle de un día

Ruta: `GET /personal/{id}/horarios/{fecha}`

Muestra los bloques del día seleccionado:
```
Juan Pérez — Martes 15 de enero 2025
──────────────────────────────────────
Bloque 1:  07:00 → 11:00  →  Edificio Norte  →  4.0 h
Bloque 2:  12:00 → 17:00  →  Casa Playa      →  5.0 h
──────────────────────────────────────
Total del día: 9.0 horas
Registrado por: María González
Editado por: Carlos Pérez (16/01/2025 09:30)
```

Botón "Editar registro" (visible para Ing. y Res.) que lleva al formulario de asistencia precargado.

### 6. Contador de días trabajados (servicio)

Función central en `horario_service.py`:

```python
def dias_en_ciclo_actual(trabajador_id: UUID, db: Session) -> int:
    """
    Cuenta los días trabajados desde el último corte de pago.
    Si no hay cortes previos, cuenta desde el inicio de los registros.
    """
    ultimo_corte = db.query(CicloPago)\
        .filter(CicloPago.trabajador_id == trabajador_id)\
        .order_by(CicloPago.periodo_fin.desc())\
        .first()
    
    fecha_desde = ultimo_corte.periodo_fin if ultimo_corte else date(1900, 1, 1)
    
    count = db.query(func.count(distinct(RegistroHorario.fecha)))\
        .filter(
            RegistroHorario.trabajador_id == trabajador_id,
            RegistroHorario.fecha > fecha_desde
        ).scalar()
    
    return count or 0
```

Esta función se llama:
- Al guardar un registro (para verificar si se alcanzaron los 15 días)
- En la vista del perfil del trabajador
- En el dashboard del residente

### 7. Acceso rápido desde el dashboard

En `dashboard/residente.html` agregar:
- Botón grande "Registrar asistencia de hoy" que lleva directo al formulario
- Lista de los últimos 5 trabajadores con registro reciente (para acceso rápido)

---

## Consideraciones mobile

El formulario de asistencia (`horarios/registrar.html`) debe:
- Usar inputs nativos de HTML para `date` y `time` (el navegador del celular abre el picker nativo)
- Botones con altura mínima de 44px (área táctil cómoda)
- El botón "+ Agregar bloque" debe estar en la parte inferior de la pantalla
- Usar JavaScript vanilla para agregar/eliminar bloques dinámicamente sin recargar la página

---

## Criterios de aceptación

- [ ] El residente puede registrar asistencia de un trabajador con uno o más bloques en el mismo día
- [ ] Se puede asignar cada bloque a una obra distinta
- [ ] `horas_trabajadas` se calcula automáticamente en cada bloque
- [ ] Si ya existe registro para ese trabajador+fecha, el formulario se precarga con los datos
- [ ] El residente puede editar un registro existente; se guarda `editado_por` y `editado_en`
- [ ] `hora_salida <= hora_entrada` devuelve error de validación
- [ ] El calendario del trabajador muestra los días trabajados correctamente
- [ ] El contador de ciclo actual muestra los días correctos después de cada guardado
- [ ] El autocompletado de trabajadores funciona en mobile
- [ ] No se puede registrar asistencia en una fecha futura
- [ ] No se puede registrar asistencia en un proyecto archivado