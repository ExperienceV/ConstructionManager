# Base de datos

Motor: **PostgreSQL 15+**
ORM: **SQLAlchemy 2.0** con migraciones via **Alembic**
Zona horaria del servidor de BD: **UTC** (las conversiones a Ecuador se hacen en la app)

---

## Tablas

### `usuarios`
Usuarios con acceso a la app (Ingeniero y Residente únicamente).

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | Identificador único |
| `email` | VARCHAR(255) UNIQUE | Email de la cuenta Google |
| `nombre` | VARCHAR(255) | Nombre completo de Google |
| `rol` | VARCHAR(50) NULL | `ingeniero` o `residente`. NULL = pendiente de activación |
| `activo` | BOOLEAN DEFAULT true | Permite desactivar sin borrar |
| `creado_en` | TIMESTAMPTZ | Fecha de primer login |
| `ultimo_login` | TIMESTAMPTZ | Fecha del último login |

---

### `proyectos`
Obras de construcción gestionadas en el sistema.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | Identificador único |
| `nombre` | VARCHAR(255) | Nombre del proyecto |
| `descripcion` | TEXT NULL | Descripción libre |
| `inversion_total` | NUMERIC(12,2) NULL | Presupuesto estimado en USD |
| `fecha_inicio` | DATE | Fecha de inicio de obra |
| `fecha_estimada_fin` | DATE NULL | Fecha estimada de entrega |
| `estado` | VARCHAR(20) DEFAULT 'activo' | `activo` o `archivado` |
| `creado_por` | UUID FK → usuarios.id | Ingeniero que creó el proyecto |
| `creado_en` | TIMESTAMPTZ | Timestamp de creación |
| `archivado_en` | TIMESTAMPTZ NULL | Timestamp de archivado |

---

### `proyecto_documentos`
Planos, contratos y archivos subidos al proyecto.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | Identificador único |
| `proyecto_id` | UUID FK → proyectos.id | Proyecto al que pertenece |
| `nombre` | VARCHAR(255) | Nombre del archivo |
| `tipo` | VARCHAR(50) | `plano`, `contrato`, `resultado_final`, `otro` |
| `url_archivo` | TEXT | URL de Cloudinary |
| `public_id_cloudinary` | VARCHAR(255) | ID en Cloudinary para eliminar |
| `subido_por` | UUID FK → usuarios.id | Usuario que subió el archivo |
| `subido_en` | TIMESTAMPTZ | Timestamp de subida |

---

### `proyecto_fotos_avance`
Fotos de progreso de la obra con fecha.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | Identificador único |
| `proyecto_id` | UUID FK → proyectos.id | Proyecto al que pertenece |
| `url_foto` | TEXT | URL de Cloudinary |
| `public_id_cloudinary` | VARCHAR(255) | ID en Cloudinary para eliminar |
| `descripcion` | TEXT NULL | Descripción opcional |
| `subida_por` | UUID FK → usuarios.id | Usuario que subió la foto |
| `tomada_en` | TIMESTAMPTZ | Fecha/hora en hora Ecuador al momento de subir |

---

### `trabajadores`
Empleados de campo sin acceso a la app.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | Identificador único |
| `nombre` | VARCHAR(255) | Nombre completo |
| `rol` | VARCHAR(50) | `Contratista`, `Electricista`, `Pintor`, `Albañil`, `Oficial Jr`, `Oficial Sr`, `Maestro` |
| `tarifa_hora` | NUMERIC(8,2) | Tarifa en USD por hora |
| `activo` | BOOLEAN DEFAULT true | false si fue "eliminado" pero tiene historial |
| `creado_por` | UUID FK → usuarios.id | Quien lo registró |
| `creado_en` | TIMESTAMPTZ | Timestamp de creación |

---

### `proyecto_trabajadores`
Relación muchos a muchos entre proyectos y trabajadores.

| Columna | Tipo | Descripción |
|---|---|---|
| `proyecto_id` | UUID FK → proyectos.id | PK compuesto |
| `trabajador_id` | UUID FK → trabajadores.id | PK compuesto |
| `asignado_por` | UUID FK → usuarios.id | Quien hizo la asignación |
| `asignado_en` | TIMESTAMPTZ | Timestamp de asignación |

**PK compuesta:** `(proyecto_id, trabajador_id)`

---

### `registros_horario`
Un registro por trabajador por día. Es el "sobre" que contiene los bloques.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | Identificador único |
| `trabajador_id` | UUID FK → trabajadores.id | Trabajador |
| `fecha` | DATE | Fecha del día trabajado (en hora Ecuador) |
| `creado_por` | UUID FK → usuarios.id | Quien creó el registro |
| `creado_en` | TIMESTAMPTZ | Timestamp de creación |
| `editado_por` | UUID FK → usuarios.id NULL | Quien hizo la última edición |
| `editado_en` | TIMESTAMPTZ NULL | Timestamp de última edición |

**UNIQUE:** `(trabajador_id, fecha)` — solo un registro por trabajador por día.

---

### `bloques_horario`
Tramos de trabajo dentro de un día, cada uno vinculado a una obra.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | Identificador único |
| `registro_id` | UUID FK → registros_horario.id | Registro del día al que pertenece |
| `proyecto_id` | UUID FK → proyectos.id | Obra en la que trabajó este tramo |
| `hora_entrada` | TIME | Hora de inicio del tramo |
| `hora_salida` | TIME | Hora de fin del tramo |
| `horas_trabajadas` | NUMERIC(4,2) | Calculado: `hora_salida - hora_entrada` en horas |

---

### `ciclos_pago`
Cortes de pago generados automáticamente cada 15 días trabajados.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | Identificador único |
| `trabajador_id` | UUID FK → trabajadores.id | Trabajador |
| `periodo_inicio` | DATE | Fecha del primer día del ciclo |
| `periodo_fin` | DATE | Fecha del día 15 del ciclo |
| `dias_trabajados` | INTEGER DEFAULT 15 | Siempre 15 al cerrar |
| `tarifa_hora` | NUMERIC(8,2) | Tarifa al momento del corte (snapshot) |
| `monto_total` | NUMERIC(10,2) | `15 × 10 × tarifa_hora` |
| `fecha_corte` | TIMESTAMPTZ | Cuando se generó el corte (hora Ecuador) |

> **Nota:** `tarifa_hora` se guarda como snapshot porque la tarifa del trabajador puede cambiar en el futuro.

---

### `gastos_materiales`
Gastos de herramientas y materiales por proyecto.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | Identificador único |
| `proyecto_id` | UUID FK → proyectos.id | Obra a la que pertenece el gasto |
| `registrado_por` | UUID FK → usuarios.id | Quien registró el gasto |
| `descripcion` | TEXT | Descripción del material o herramienta |
| `monto` | NUMERIC(10,2) | Monto en USD |
| `url_comprobante` | TEXT NULL | URL de Cloudinary (opcional) |
| `public_id_cloudinary` | VARCHAR(255) NULL | ID en Cloudinary para eliminar |
| `fecha` | TIMESTAMPTZ | Fecha automática en hora Ecuador |

---

## Índices recomendados

```sql
-- Para buscar registros de asistencia de un trabajador en un rango de fechas
CREATE INDEX idx_registros_trabajador_fecha ON registros_horario(trabajador_id, fecha);

-- Para calcular días trabajados de un trabajador en el ciclo actual
CREATE INDEX idx_registros_trabajador ON registros_horario(trabajador_id);

-- Para calcular costo laboral por proyecto
CREATE INDEX idx_bloques_proyecto ON bloques_horario(proyecto_id);

-- Para historial de cortes de un trabajador
CREATE INDEX idx_ciclos_trabajador ON ciclos_pago(trabajador_id);

-- Para gastos de un proyecto
CREATE INDEX idx_gastos_proyecto ON gastos_materiales(proyecto_id);
```

---

## Consulta clave: días trabajados en ciclo actual

```sql
-- Días trabajados por un trabajador después de su último corte
SELECT COUNT(DISTINCT rh.fecha) as dias_en_ciclo_actual
FROM registros_horario rh
WHERE rh.trabajador_id = :trabajador_id
  AND rh.fecha > COALESCE(
    (SELECT MAX(cp.periodo_fin)
     FROM ciclos_pago cp
     WHERE cp.trabajador_id = :trabajador_id),
    '1900-01-01'::date
  );
```

---

## Consulta clave: costo laboral de un proyecto

```sql
-- Costo laboral total de una obra
SELECT
  t.nombre,
  t.tarifa_hora,
  SUM(bh.horas_trabajadas) as horas_totales,
  SUM(bh.horas_trabajadas * t.tarifa_hora) as costo_total
FROM bloques_horario bh
JOIN registros_horario rh ON bh.registro_id = rh.id
JOIN trabajadores t ON rh.trabajador_id = t.id
WHERE bh.proyecto_id = :proyecto_id
GROUP BY t.id, t.nombre, t.tarifa_hora;
```