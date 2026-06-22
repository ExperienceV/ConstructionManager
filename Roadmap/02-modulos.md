# Módulos del sistema

## Módulo 1 — Autenticación

### Flujo de login

1. El usuario entra a la app y ve un botón "Iniciar sesión con Google".
2. Al hacer clic, se redirige a Google OAuth2.
3. Google devuelve un token con el email y nombre del usuario.
4. El backend busca ese email en la tabla `usuarios`:
   - Si **existe**: carga su rol y crea una sesión.
   - Si **no existe**: crea el registro con `rol = null` y devuelve error 403 (acceso pendiente de asignación).
5. Si el rol es `null`, el usuario ve una pantalla de "Tu cuenta está pendiente de activación".
6. Si el rol es `ingeniero` o `residente`, accede al dashboard correspondiente.

### Sesión

- Se usa JWT (JSON Web Token) almacenado en una cookie HttpOnly.
- El token expira en 8 horas.
- Cada request a la API valida el token y extrae el rol para aplicar los permisos.

---

## Módulo 2 — Proyectos

### Creación (solo Ingeniero)

El ingeniero llena un formulario con:
- Nombre del proyecto
- Descripción (opcional)
- Inversión total (monto en dólares)
- Fecha de inicio
- Fecha estimada de finalización

Al guardar, el proyecto queda en estado `activo`.

### Documentos y planos

El ingeniero puede subir archivos (PDF, imágenes, DWG) al proyecto. Cada archivo se sube a Cloudinary y se guarda la URL en `proyecto_documentos`. El residente puede **ver y descargar** estos archivos pero no subir nuevos.

### Fotos de avance

Tanto el ingeniero como el residente pueden subir fotos de progreso. Cada foto tiene:
- Imagen (subida a Cloudinary)
- Descripción opcional
- Fecha y hora automática (hora Ecuador)
- Quién la subió

Las fotos se muestran en una galería ordenada por fecha, permitiendo ver la evolución visual de la obra.

### Archivado

Cuando una obra termina, el ingeniero la archiva. El proyecto pasa a estado `archivado` y queda en modo solo lectura. Aparece en una sección separada "Proyectos archivados" en el dashboard.

---

## Módulo 3 — Personal

### Gestión de trabajadores

El ingeniero y el residente pueden:
- **Agregar** un trabajador: nombre, rol (de la lista predefinida), tarifa por hora
- **Editar** sus datos (nombre, rol, tarifa)
- **Eliminar** un trabajador (solo si no tiene registros de horario activos)
- **Asignar** a uno o varios proyectos

Un trabajador eliminado con historial de pagos no se borra físicamente — queda marcado como `activo = false` para preservar el historial.

### Asignación a proyectos

Desde la vista de un proyecto, el residente puede buscar trabajadores existentes y agregarlos. Un trabajador puede aparecer en múltiples proyectos al mismo tiempo. La asignación solo se puede hacer sobre proyectos activos.

---

## Módulo 4 — Horarios

### Registro diario

El residente entra a "Registrar asistencia" y selecciona:
1. El trabajador
2. La fecha (por defecto hoy en hora Ecuador)
3. Uno o más bloques: `{hora entrada, hora salida, proyecto}`

El sistema calcula automáticamente las horas de cada bloque (`hora_salida - hora_entrada`).

Si ya existe un registro para ese trabajador en esa fecha, se puede editar.

### Múltiples obras en un día

Un trabajador puede trabajar en varias obras el mismo día. El residente agrega tantos bloques como sean necesarios. Ejemplo:

```
Trabajador: Juan Pérez — Fecha: 15/06/2025
  Bloque 1: 07:00 → 11:00 — Obra: Edificio Norte (4h)
  Bloque 2: 12:00 → 17:00 — Obra: Casa Playa (5h)
Total del día: 9h
Días trabajados para ciclo de pago: +1
```

### Edición de registros

El residente puede editar cualquier registro existente. El sistema guarda en `registros_horario`:
- `editado_en`: timestamp de la última edición
- `editado_por`: id del usuario que editó

### Vista de asistencia

Hay una vista de calendario por trabajador que muestra los días trabajados, con resumen de horas por día y por obra. También muestra el progreso del ciclo de pago actual (por ejemplo: "8 de 15 días trabajados").

---

## Módulo 5 — Cobros

### Ciclo de pago automático

El sistema revisa constantemente (o al guardar un registro) si un trabajador alcanzó 15 días trabajados en su ciclo actual. Cuando llega a 15:

1. Se crea un registro en `ciclos_pago` con:
   - Monto: `15 × 10 × tarifa_hora`
   - Periodo: fecha del primer día del ciclo hasta el día 15
   - Fecha de corte: fecha actual en hora Ecuador

2. El contador de días del trabajador reinicia.

### Historial de cobros

Cada trabajador tiene una pestaña "Historial de cobros" que muestra todos sus cortes anteriores con fecha, periodo y monto. Es solo informativo — no hay botón de "pagar" ni estados de pago.

### Vista del Ingeniero

El ingeniero puede ver el historial de cualquier trabajador desde el perfil del trabajador, que también incluye el ciclo actual en curso.

---

## Módulo 6 — Gastos de materiales

### Registro de gasto

Desde un proyecto activo, el ingeniero o residente puede registrar un gasto:
- Descripción (texto libre)
- Monto (en dólares)
- Foto del comprobante (opcional — imagen subida a Cloudinary)
- Fecha: se asigna automáticamente al momento del registro en hora Ecuador

### Visibilidad

El residente puede **registrar** gastos pero **no puede verlos** en el listado ni en el panel financiero. Solo puede registrar y recibir confirmación de que se guardó.

El ingeniero ve el listado completo de gastos por proyecto con total acumulado.

---

## Módulo 7 — Panel financiero (solo Ingeniero)

Visible solo para el ingeniero. En cada proyecto activo o archivado muestra:

```
Proyecto: Edificio Norte
─────────────────────────────────────────
Inversión total:          $85,000.00
─────────────────────────────────────────
Costo laboral acumulado:  $12,450.00
Costo de materiales:       $8,320.00
─────────────────────────────────────────
Gasto total real:         $20,770.00
Diferencia:               $64,230.00  ✓ Dentro de presupuesto
```

El costo laboral se calcula en tiempo real desde los bloques de horario vinculados a esa obra (`horas_trabajadas × tarifa_hora` del trabajador en ese momento del registro).

---

## Módulo 8 — Reportes

El ingeniero puede exportar un reporte por proyecto en formato Excel o PDF con:
- Lista de trabajadores asignados
- Días y horas trabajadas por cada uno
- Costo laboral individual y total
- Lista de gastos de materiales
- Resumen financiero (inversión vs gasto real)
- Fotos de avance (solo en PDF, miniaturas)