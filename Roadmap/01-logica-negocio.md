# Lógica de negocio

## Roles del sistema

El sistema tiene dos tipos de usuarios que requieren autenticación (Google OAuth2) y trabajadores de campo que son solo registros de texto sin acceso a la app.

### Usuarios con acceso

| Rol | Descripción |
|---|---|
| `ingeniero` | Propietario del sistema. Acceso total. |
| `residente` | Mano derecha del ingeniero. Acceso operativo sin datos financieros. |

El rol se asigna **manualmente en la base de datos**. No hay registro público. El flujo es:
1. El ingeniero inicia sesión con Google por primera vez → se crea su registro en `usuarios`
2. Un administrador cambia su campo `rol` a `ingeniero` directamente en la BD
3. El ingeniero agrega al residente desde la app → el residente inicia sesión con Google → ya tiene su rol asignado

### Trabajadores de campo

No tienen cuenta en el sistema. Son registros simples con nombre, rol y tarifa. El residente los crea y gestiona. Los roles disponibles son:

`Contratista`, `Electricista`, `Pintor`, `Albañil`, `Oficial Jr`, `Oficial Sr`, `Maestro`

---

## Matriz de permisos

| Acción | Ingeniero | Residente |
|---|:---:|:---:|
| Crear proyecto | ✓ | ✗ |
| Editar proyecto | ✓ | ✗ |
| Archivar proyecto | ✓ | ✗ |
| Ver planos y documentos | ✓ | ✓ |
| Subir planos y documentos | ✓ | ✗ |
| Subir fotos de avance | ✓ | ✓ |
| Agregar trabajadores | ✓ | ✓ |
| Editar trabajadores | ✓ | ✓ |
| Eliminar trabajadores | ✓ | ✓ |
| Registrar horarios | ✓ | ✓ |
| Editar horarios | ✓ | ✓ |
| Ver historial de cobros | ✓ | ✓ |
| Ver inversión del proyecto | ✓ | ✗ |
| Ver costo laboral por obra | ✓ | ✗ |
| Ver gastos de materiales | ✓ | ✗ |
| Registrar gastos de materiales | ✓ | ✓ |
| Ver panel financiero | ✓ | ✗ |
| Exportar reportes | ✓ | ✗ |

---

## Reglas de proyectos

- Un proyecto puede estar en estado `activo` o `archivado`.
- Solo el ingeniero puede cambiar el estado.
- Los proyectos archivados son de solo lectura — no se pueden agregar registros nuevos.
- Un trabajador puede estar asignado a múltiples proyectos simultáneamente.
- Al archivar un proyecto, los ciclos de pago abiertos de sus trabajadores **no se cierran automáticamente** — siguen corriendo con los días ya acumulados.

---

## Reglas de horarios

- El residente registra la asistencia manualmente. No hay checkin automático.
- Un registro de asistencia es por **trabajador + fecha**.
- Dentro de un mismo día, un trabajador puede tener múltiples **bloques de tiempo**, cada uno vinculado a una obra distinta. Ejemplo: 4h en Obra A y 6h en Obra B.
- Un día se cuenta como **1 día trabajado** para el ciclo de pago, independientemente de cuántas horas o cuántas obras tenga ese día.
- El residente puede editar registros existentes. Cada edición queda en un log con quién la hizo y cuándo.
- **No hay validación de solapamiento de horas** — se confía en el criterio del residente.
- El día laboral de referencia es de **10 horas**. Las horas extras se pagan a la misma tarifa que la hora normal.

---

## Reglas de ciclos de pago

El ciclo de pago es el módulo más delicado del sistema. Las reglas son:

1. El sistema cuenta los **días distintos** en que un trabajador tiene al menos un bloque de horas registrado.
2. Cuando ese conteo llega a **15 días**, se genera automáticamente un **corte de pago**.
3. El monto del corte se calcula como: `15 días × 10 horas × tarifa_hora`
4. El contador de días reinicia a 0 después del corte.
5. Los días trabajados antes del corte NO se eliminan — solo se marca que ese período ya fue procesado con `fecha_corte` en la tabla `ciclos_pago`.
6. El historial de cortes es **solo informativo**. No hay flujo de pago dentro de la app.
7. Si un trabajador acumula días en múltiples proyectos, todos cuentan para el mismo ciclo (el ciclo es global, no por obra).

### Ejemplo de ciclo

```
Día 1  → trabaja en Obra A (4h) y Obra B (6h) → contador: 1
Día 2  → trabaja en Obra A (10h)               → contador: 2
Día 5  → trabaja en Obra C (8h)                → contador: 3
...
Día N  → trabaja cualquier obra                 → contador: 15 → CORTE AUTOMÁTICO
         Monto = 15 × 10 × tarifa/hora
         Contador reinicia a 0
```

---

## Reglas de gastos de materiales

- Cualquier gasto va vinculado a **una obra específica**.
- Campos requeridos: descripción, obra, monto.
- Campos opcionales: foto del comprobante (imagen subida a Cloudinary).
- La fecha se asigna **automáticamente** en hora Ecuador (America/Guayaquil) al momento del registro.
- No se puede editar la fecha manualmente.
- Tanto el ingeniero como el residente pueden registrar gastos, pero **solo el ingeniero puede verlos** en el panel financiero.

---

## Reglas financieras (solo Ingeniero)

El ingeniero ve en cada proyecto:

- **Inversión total:** valor ingresado al crear el proyecto (estimado del dueño/cliente).
- **Costo laboral real:** suma de `horas trabajadas × tarifa/hora` de todos los trabajadores asignados a esa obra, calculado desde los bloques de horario vinculados a ese proyecto.
- **Costo de materiales real:** suma de todos los gastos registrados en esa obra.
- **Gasto total real:** costo laboral + costo de materiales.
- **Diferencia:** inversión total − gasto total real (positivo = dentro de presupuesto, negativo = sobrepasado).

---

## Zona horaria

Todas las fechas se almacenan en UTC en la base de datos. Al mostrarlas al cliente se convierten a `America/Guayaquil` (UTC-5). Los campos de fecha automática (como `fecha` en gastos de materiales) se calculan en el servidor usando la hora actual de Ecuador.