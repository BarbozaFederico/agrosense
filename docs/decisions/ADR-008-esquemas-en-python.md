# ADR-008: Esquemas de validación escritos en Python

**Estado:** Aceptado (16/10/2026). Implementa la validación de [ADR-006](ADR-006-modelo-de-datos.md) y [ADR-007](ADR-007-validacion-lecturas.md).

## Contexto

Los `$jsonSchema` se escribieron primero en JavaScript, para `mongosh`. El ADR-007 exige que el **simulador, escrito en Python**, valide las lecturas antes de insertarlas, así que el esquema de `lecturas` también hacía falta en Python. Con los esquemas en JavaScript habría dos copias que podrían desincronizarse.

Para MongoDB el lenguaje no cambia nada: el `$jsonSchema` es un documento que el **servidor** guarda y aplica. `mongosh` y `pymongo` solo son dos formas de enviar la misma orden.

## Decisión

Los esquemas, la creación de las colecciones, la validación previa de lecturas y la auditoría se escriben en **Python** (`pymongo`), dentro del paquete `db`:

- `db/schemas/*.py`: un esquema por colección, como diccionario de Python.
- `db/schemas/validar.py`: el simulador valida con el mismo esquema usando `$documents` + `$jsonSchema`, sin guardar ([spike de esquemas, prueba 4](../spikes/spike-esquemas-validacion.md)).
- `db/queries/auditoria_lecturas.py`: la auditoría del ADR-007.

Las consultas Q1 a Q10 seguían en `mongosh` (`db/queries/qN_nombre.js`) cuando se escribió este ADR. **Reemplazado por [ADR-014](ADR-014-consultas-en-python.md) (20/10/2026): también van en Python con `pymongo`** (`db/queries/qN_nombre.py`).

## Alternativas

| Opción | Ventaja | Desventaja |
|---|---|---|
| A. Esquemas en JavaScript (`mongosh`) | Herramienta nativa de MongoDB, igual que en clase | El simulador necesita su propia copia del esquema de `lecturas`. En `mongosh`, la lógica separada en archivos tiene que cargarse con `load()`: con `require()` los comandos no esperan su resultado |
| **B. Esquemas en Python (elegida)** | Una sola fuente: el simulador importa los mismos esquemas. Todo el código de la aplicación en un lenguaje | La auditoría también pasa a Python |
| C. Esquemas en archivos `.json` | Neutral entre lenguajes | JSON no admite comentarios ni reutilizar piezas: se pierden las explicaciones y se repite código |

## Consecuencias

- Los scripts se ejecutan desde la raíz con `python -m`, por ejemplo `python -m db.schemas.crear_colecciones`, para que funcionen los `import` del paquete `db`.
- La conexión se configura con las variables `AGROSENSE_URI` y `AGROSENSE_BD` (`db/conexion.py`); no se escriben datos de conexión en el código.
- En el esquema de `lecturas`, `_id` ya no es obligatorio: las lecturas se validan antes de insertarse, cuando todavía no tienen `_id`.
- Los archivos `.js` de los esquemas se eliminaron. Los scripts de los spikes (`scripts/spike-adr001/` y `scripts/spike-esquemas/`) también se pasaron a Python: al correrlos dieron resultados idénticos a los de `mongosh`, porque las reglas las aplica el servidor.
