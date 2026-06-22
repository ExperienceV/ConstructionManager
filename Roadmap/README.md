# Sistema de administración de proyectos de construcción

## Documentos del proyecto

| Archivo | Contenido |
|---|---|
| `01-logica-negocio.md` | Reglas de negocio, roles, permisos y flujos |
| `02-modulos.md` | Cómo funciona cada módulo en detalle |
| `03-cliente.md` | Cómo se usa la app desde el cliente (web/móvil) |
| `04-base-de-datos.md` | Esquema completo de tablas y relaciones |
| `05-fase-1.md` | Fase 1: Base y autenticación |
| `06-fase-2.md` | Fase 2: Proyectos y personal |
| `07-fase-3.md` | Fase 3: Horarios y asistencia |
| `08-fase-4.md` | Fase 4: Cobros y materiales |
| `09-fase-5.md` | Fase 5: Reportes, notificaciones y despliegue |

## Stack tecnológico

- **Backend:** Python 3.12 + FastAPI
- **Base de datos:** PostgreSQL
- **ORM:** SQLAlchemy + Alembic (migraciones)
- **Autenticación:** Google OAuth2 vía `authlib`
- **Almacenamiento de archivos:** Cloudinary (planos, fotos, comprobantes)
- **Frontend inicial:** Jinja2 (templates del servidor)
- **Zona horaria:** America/Guayaquil (UTC-5) para todas las fechas automáticas
- **Despliegue:** Railway o Render

## Convenciones para los agentes

- Todos los IDs son `UUID v4`
- Fechas siempre en UTC en la BD; se muestran en hora Ecuador al cliente
- Nombres de tablas en `snake_case` plural
- Nombres de columnas en `snake_case`
- Rutas de la API con prefijo `/api/v1/`
- Respuestas de error siguen el formato `{"detail": "mensaje de error"}`
- Los archivos de código van en `app/` siguiendo la estructura de FastAPI modular


## EXTRA
- Cada fase completada o cambio realizado, debe agregarse una breve explicacion de lo
  desarrollado en UPDATES.md siguiendo la siguiente estructura:

 ---------------
  Titulo: (Correccion, Implementacion, Reescrito...)
  Descripcion: He realizado...
  Fecha: DD/MM/AA 
 ---------------

- No necesito sobreingenieria, necesito que todo funcione y que sea escalable a futuras actualizaciones.
- Solo trabaja con lo basico necesario, no intentes optimizar o implementar algo que no sea necesario para el funcionamiento del proyecto.
- No intentes implementar funcionalidades que no esten en los documentos, si necesitas implementar algo nuevo, primero pregunta y documentalo.