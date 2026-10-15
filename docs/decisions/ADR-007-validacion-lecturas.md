# ADR-007: Validación de `lecturas` (serie temporal)

**Estado:** Aceptado (15/10/2026). Ajusta la decisión 9 de [ADR-006](ADR-006-modelo-de-datos.md) para `lecturas`. Evidencia en el [spike de esquemas](../spikes/spike-esquemas-validacion.md).

## Contexto

El ADR-006 decidió validar todas las colecciones con `$jsonSchema` (`validationAction: "error"`, esquema cerrado). El spike del 15/10/2026 mostró que en MongoDB 9.0.2 una **serie temporal no admite validador**: ni al crearla ("'timeseries' is not allowed with 'validator'") ni después con `collMod`. `lecturas` es una serie temporal (ADR-001) y es la colección más grande (unas 732.700 lecturas), así que quedaría sin protección.

El mismo spike mostró que el `$jsonSchema` **sí funciona como filtro de búsqueda** en series temporales: `find({ $nor: [{ $jsonSchema: esquema }] })` devuelve exactamente las lecturas mal formadas, y `deleteMany` con ese filtro las borra.

## Decisión

Proteger `lecturas` en dos niveles (opción C):

1. **Validación en el simulador (al insertar):** el código Python revisa cada lectura antes de insertarla y rechaza las que no cumplen el esquema.
2. **Consulta de auditoría (después de cargar):** una consulta con `$nor` + `$jsonSchema` cuenta, y si hace falta borra, las lecturas que no cumplen el esquema. El resultado esperado es 0.

El resto de las colecciones (comunes) sigue con validador en la base, como decidió el ADR-006.

## Alternativas

| Opción | Ventaja | Desventaja |
|---|---|---|
| A. Solo validar en el simulador | Simple; frena el error antes de que entre | Si algo se inserta por otra vía (por ejemplo, a mano en `mongosh`), nadie lo detecta |
| B. Solo auditoría | Usa el mismo esquema de la base | Los datos malos entran y se detectan después |
| **C. A y B juntas (elegida)** | Doble control; la auditoría demuestra en la defensa que los datos cargados cumplen el esquema | Hay que mantener la regla en dos lugares (Python y el esquema) |
| D. Volver a una colección común | Validación en la base, como el resto | Contradice el ADR-001 y pierde las ventajas de la serie temporal |

## Consecuencias

- El `$jsonSchema` de `lecturas` se escribe igual que los demás (en `db/schemas/`), pero **no se instala como validador**: se usa en la consulta de auditoría.
- El simulador tiene que validar las lecturas antes de insertarlas. Los campos y tipos que revisa son los de `modelo-datos.md` (sección 3.4).
- La auditoría se corre después de cada carga; su resultado (0 lecturas mal formadas) se documenta como evidencia.
- En todos los esquemas cerrados hay que declarar `_id` en `properties`, porque si no se rechazan todos los documentos (spike de esquemas, prueba 1).
- El script que crea las colecciones tiene que detenerse ante cualquier error: si `createCollection` falla, el primer insert crea una colección común sin validación y el error queda oculto.
