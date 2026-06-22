# Uso desde el cliente

## Tecnología del frontend

La app usa **FastAPI + Jinja2** para renderizar HTML desde el servidor. No hay un frontend separado — el backend devuelve páginas HTML completas. Esto simplifica el desarrollo inicial y permite que funcione bien tanto en escritorio como en móvil desde el navegador.

Para estilos se usa **Tailwind CSS** (vía CDN en desarrollo, compilado en producción). No se requiere ninguna instalación de frontend por parte del usuario — basta con abrir el navegador.

---

## Acceso a la app

La app es una **web app accesible desde cualquier navegador**: Chrome, Safari, Firefox. No hay app nativa que instalar.

- **Ingeniero:** la usará principalmente desde computadora de escritorio para gestionar proyectos, revisar finanzas y exportar reportes.
- **Residente:** la usará principalmente desde **celular en obra** para registrar asistencia y subir fotos. El diseño es mobile-first.

URL de acceso: `https://nombre-del-proyecto.railway.app` (o dominio personalizado).

---

## Flujos de uso por rol

### Flujo del Ingeniero

#### Primer uso
1. Entra a la URL de la app
2. Clic en "Iniciar sesión con Google"
3. Selecciona su cuenta Google
4. El administrador activa su rol `ingeniero` en la BD
5. Al recargar, accede al dashboard del ingeniero

#### Dashboard del Ingeniero
Muestra:
- Lista de proyectos activos con barra de progreso (inversión vs gasto)
- Acceso rápido a proyectos archivados
- Notificaciones de proyectos próximos a vencer

#### Crear un proyecto
1. Clic en "Nuevo proyecto"
2. Completa el formulario: nombre, descripción, inversión, fechas
3. Guarda → proyecto creado en estado `activo`
4. Opcionalmente sube planos desde la pestaña "Documentos"
5. Desde la pestaña "Personal", agrega trabajadores al proyecto

#### Revisar finanzas
1. Entra al proyecto
2. Pestaña "Finanzas" → ve inversión, costo laboral, materiales y diferencia
3. Puede entrar al detalle de cada trabajador para ver su historial de cobros
4. Exporta reporte si necesita compartirlo

---

### Flujo del Residente

#### Primer uso
1. El ingeniero le comparte la URL de la app
2. El residente entra y hace login con su cuenta Google
3. El ingeniero ya creó su cuenta con rol `residente` en la BD
4. Accede directamente al dashboard del residente

#### Dashboard del Residente
Muestra:
- Lista de proyectos activos (sin datos financieros)
- Acceso rápido a "Registrar asistencia" (acción más frecuente)
- Lista de trabajadores con su ciclo de pago actual

#### Registrar asistencia (acción diaria principal)
1. Desde el celular, entra a la app
2. Clic en "Registrar asistencia"
3. Selecciona el trabajador desde un buscador con autocompletado
4. La fecha se autocompleta con hoy (editable si necesita registrar días anteriores)
5. Agrega bloques: selecciona proyecto, hora de entrada, hora de salida
6. Si trabajó en varias obras, clic en "+ Agregar bloque"
7. Guarda → confirmación visual inmediata

#### Agregar un trabajador nuevo
1. Menú "Personal"
2. Clic en "Nuevo trabajador"
3. Ingresa nombre, rol (dropdown), tarifa por hora
4. Guarda → aparece en la lista y puede asignarse a proyectos

#### Subir foto de avance
1. Entra al proyecto
2. Pestaña "Fotos"
3. Clic en "Subir foto" → selecciona desde galería del celular o toma foto
4. Agrega descripción opcional
5. Guarda → aparece en la galería con fecha automática

#### Registrar gasto de materiales
1. Entra al proyecto
2. Pestaña "Materiales" → clic en "Nuevo gasto"
3. Ingresa descripción y monto
4. Opcionalmente fotografía el comprobante
5. Guarda → confirmación. El residente no puede ver el listado de gastos.

---

## Navegación de la app

```
/ ──────────── Login con Google
/dashboard ─── Dashboard según rol
/proyectos ─── Lista de proyectos
  /proyectos/{id} ──────── Detalle del proyecto
    /proyectos/{id}/personal ─ Trabajadores asignados
    /proyectos/{id}/documentos Planos y archivos
    /proyectos/{id}/fotos ──── Galería de avance
    /proyectos/{id}/finanzas ─ Panel financiero (solo Ing.)
    /proyectos/{id}/materiales Gastos de materiales
/personal ──── Lista global de trabajadores
  /personal/{id} ──── Perfil del trabajador
    /personal/{id}/horarios ─── Calendario de asistencia
    /personal/{id}/cobros ───── Historial de cortes de pago
/asistencia ── Registro rápido de asistencia (acceso directo desde dashboard)
```

---

## Diseño mobile-first

Las pantallas clave para el residente (registro de asistencia, agregar trabajador, subir foto) están diseñadas para funcionar con una mano en celular:

- Botones grandes en la parte inferior de la pantalla
- Formularios de una sola columna
- Autocompletado en todos los campos de búsqueda
- La cámara del celular se abre directamente al subir fotos
- Confirmaciones visuales claras después de cada acción

El ingeniero en escritorio tiene una vista más amplia con tablas, gráficas y exportación de reportes.

---

## Notificaciones

El sistema envía notificaciones por email (no push) en los siguientes casos:

| Evento | Destinatario |
|---|---|
| Proyecto a 7 días de su fecha estimada de fin | Ingeniero |
| Proyecto a 1 día de su fecha estimada de fin | Ingeniero |
| Proyecto con fecha estimada vencida y aún activo | Ingeniero (diario) |

Las notificaciones se envían desde una tarea programada que corre cada día a las 8:00 AM hora Ecuador.