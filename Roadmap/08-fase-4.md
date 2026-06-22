# Fase 4 — Cobros y materiales

**Duración estimada:** 2 – 3 semanas
**Prerequisito:** Fase 3 completada.
**Objetivo:** el sistema genera cortes de pago automáticamente al llegar a 15 días trabajados, lleva historial de cobros por trabajador, registra gastos de materiales y el ingeniero puede ver el panel financiero completo de cada obra.

---

## Nuevas tablas en esta fase

Crear migraciones para:
- `ciclos_pago`
- `gastos_materiales`

Ver esquema completo en `04-base-de-datos.md`.

---

## Estructura de carpetas adicional

```
app/
├── models/
│   ├── ciclo_pago.py
│   └── gasto_material.py
├── schemas/
│   ├── ciclo_pago.py
│   └── gasto_material.py
├── routers/
│   ├── cobros.py
│   └── materiales.py
├── services/
│   ├── ciclo_pago_service.py    # Lógica de generación de cortes
│   └── financiero_service.py   # Cálculos del panel del ingeniero
└── templates/
    ├── cobros/
    │   └── historial.html       # Historial de cortes de un trabajador
    └── materiales/
        ├── lista.html           # Solo Ingeniero
        └── registrar.html      # Ing + Res
```

---

## Tareas de esta fase

### 1. Servicio de ciclos de pago

`app/services/ciclo_pago_service.py` — función principal:

```python
def verificar_y_generar_corte(trabajador_id: UUID, db: Session) -> CicloPago | None:
    """
    Verifica si el trabajador alcanzó 15 días en el ciclo actual.
    Si es así, genera el corte y retorna el objeto CicloPago creado.
    Si no, retorna None.
    
    Esta función se llama cada vez que se guarda un registro de horario.
    """
    dias = dias_en_ciclo_actual(trabajador_id, db)
    
    if dias < 15:
        return None
    
    trabajador = db.get(Trabajador, trabajador_id)
    
    # Obtener el rango de fechas del ciclo
    ultimo_corte = obtener_ultimo_corte(trabajador_id, db)
    fecha_desde = ultimo_corte.periodo_fin if ultimo_corte else None
    
    fechas_del_ciclo = obtener_fechas_ciclo(trabajador_id, fecha_desde, db)
    
    corte = CicloPago(
        trabajador_id=trabajador_id,
        periodo_inicio=min(fechas_del_ciclo),
        periodo_fin=max(fechas_del_ciclo),
        dias_trabajados=15,
        tarifa_hora=trabajador.tarifa_hora,  # snapshot de la tarifa actual
        monto_total=Decimal("15") * Decimal("10") * trabajador.tarifa_hora,
        fecha_corte=datetime.now(pytz.timezone("America/Guayaquil"))
    )
    
    db.add(corte)
    db.commit()
    db.refresh(corte)
    
    return corte
```

**Importante:** la tarifa se guarda como snapshot (`tarifa_hora` en `ciclos_pago`) porque si el residente cambia la tarifa del trabajador en el futuro, los cortes anteriores deben conservar el valor que tenían en ese momento.

### 2. Integrar verificación en el guardado de horarios

En `horario_service.py`, al final de `guardar_registro`:

```python
# Después de guardar el registro
corte_generado = verificar_y_generar_corte(trabajador_id, db)
return {
    "registro": registro,
    "corte_generado": corte_generado  # None o el objeto del corte
}
```

Si se generó un corte, el template debe mostrar un banner de notificación:
```
✓ Asistencia guardada.
💰 Se generó un corte de pago para Juan Pérez: $1,500.00 (ciclo del 01/01 al 15/01)
```

### 3. Historial de cobros del trabajador

Ruta: `GET /personal/{id}/cobros`

Lista todos los cortes de pago del trabajador en orden cronológico descendente:

```
Juan Pérez — Historial de cobros
────────────────────────────────────────────────
Corte #5   01/05/2025 → 20/05/2025   $1,500.00
Corte #4   05/04/2025 → 25/04/2025   $1,500.00
Corte #3   08/03/2025 → 28/03/2025   $1,500.00
...
────────────────────────────────────────────────
Ciclo actual: 8 de 15 días  |  Acumulado: $800.00 (estimado)
```

El "acumulado estimado" del ciclo actual = `dias_en_ciclo_actual × 10 × tarifa_hora` (no es un corte real, es una proyección).

Esta vista es accesible para **ambos roles** (Ing. y Res.). El monto total está visible para ambos porque es información del trabajador, no de la obra. La información financiera restringida es la de los proyectos.

### 4. Módulo de gastos de materiales

**Formulario de registro** — `GET/POST /proyectos/{id}/materiales/nuevo`:

Acceso: Ing. y Res.

Campos:
- Descripción (textarea)
- Monto (input numérico con dos decimales)
- Foto del comprobante (file input, opcional)

La fecha se asigna automáticamente. No hay campo de fecha en el formulario.

Al guardar: si hay foto, se sube a Cloudinary en la carpeta `proyectos/{proyecto_id}/comprobantes/`. Se guarda la URL y el `public_id` en BD.

**Listado de gastos** — `GET /proyectos/{id}/materiales`:

Acceso: **solo Ingeniero**. Si un residente intenta acceder, devuelve 403.

Muestra la lista de gastos con fecha, descripción, monto y miniatura del comprobante (si existe). Total acumulado al final.

**Eliminar gasto** — `DELETE /proyectos/{id}/materiales/{gasto_id}`:

Acceso: solo Ingeniero. Elimina el registro de BD y el archivo de Cloudinary si existe.

### 5. Panel financiero del proyecto

Ruta: `GET /proyectos/{id}/finanzas`

Acceso: **solo Ingeniero**. Protegido con `require_rol("ingeniero")`.

Cálculos en `financiero_service.py`:

```python
def calcular_panel_financiero(proyecto_id: UUID, db: Session) -> dict:
    # Costo laboral: suma de horas_trabajadas × tarifa_hora por bloque
    costo_laboral = db.query(
        func.sum(BloqueHorario.horas_trabajadas * Trabajador.tarifa_hora)
    ).join(...).filter(BloqueHorario.proyecto_id == proyecto_id).scalar() or 0
    
    # Costo de materiales
    costo_materiales = db.query(
        func.sum(GastoMaterial.monto)
    ).filter(GastoMaterial.proyecto_id == proyecto_id).scalar() or 0
    
    proyecto = db.get(Proyecto, proyecto_id)
    gasto_total = costo_laboral + costo_materiales
    diferencia = (proyecto.inversion_total or 0) - gasto_total
    
    return {
        "inversion_total": proyecto.inversion_total,
        "costo_laboral": costo_laboral,
        "costo_materiales": costo_materiales,
        "gasto_total": gasto_total,
        "diferencia": diferencia,
        "dentro_de_presupuesto": diferencia >= 0
    }
```

La vista también incluye un desglose de costo laboral por trabajador (nombre, horas totales, costo individual).

---

## Criterios de aceptación

- [ ] Al guardar un registro de horario que lleva el contador a 15 días, se genera un corte automáticamente
- [ ] El corte guarda la tarifa como snapshot (no referencia)
- [ ] El monto del corte es siempre `15 × 10 × tarifa_hora`
- [ ] El contador de días reinicia a 0 después del corte
- [ ] El historial de cobros del trabajador muestra todos sus cortes anteriores
- [ ] El estimado del ciclo actual se muestra correctamente
- [ ] El residente puede registrar un gasto de materiales con o sin foto
- [ ] El residente NO puede ver el listado de gastos (devuelve 403)
- [ ] El ingeniero ve el listado completo de gastos con total
- [ ] El panel financiero del ingeniero muestra inversión, costos y diferencia correctamente
- [ ] Si la tarifa del trabajador cambia, los cortes anteriores conservan la tarifa original
- [ ] Un proyecto sin inversión ingresada muestra "No definida" en lugar de $0.00