# Spike de esquemas: validación cerrada en series temporales y colecciones comunes

**Fecha:** 15/10/2026 · **Versión probada:** MongoDB Server 9.0.2, `mongosh` 2.13.0 · **ADR:** [ADR-006](../decisions/ADR-006-modelo-de-datos.md) (decisiones 9 y 10)

## Pregunta a responder

El ADR-006 decidió una validación estricta: `validationAction: "error"` y esquema cerrado (`additionalProperties: false`). Antes de escribir los diez `$jsonSchema`, hay que saber:

1. ¿Funciona un esquema cerrado en una **serie temporal** (`lecturas`)?
2. ¿Qué pasa con el `_id`, que MongoDB agrega solo, si el esquema está cerrado?
3. ¿El cierre funciona también dentro de un subdocumento (`meta`)?

## Cómo se probó

Tres scripts de `mongosh` en [`scripts/spike-esquemas/`](../../scripts/spike-esquemas/). Usan la base de **prueba** `agrosense_tests`, que se borra al empezar, con datos inventados.

```bash
mongosh --file scripts/spike-esquemas/01_additional_properties.js
```

```bash
mongosh --file scripts/spike-esquemas/02_validador_serie_temporal.js
```

```bash
mongosh --file scripts/spike-esquemas/03_auditoria_serie_temporal.js
```

Cada script crea colecciones con el esquema de una lectura (sección 3.4 de [`modelo-datos.md`](../modelo-datos.md)) e intenta insertar siete documentos:

| # | Documento | Qué debería pasar |
|---|---|---|
| 1 | Válido | Entrar |
| 2 | Con un campo de más (`viento_kmh`) | Rechazarse |
| 3 | Con un error de tipeo (`temperatua_c`) | Rechazarse |
| 4 | Con un campo de más dentro de `meta` (`color`) | Rechazarse |
| 5 | Con un tipo equivocado (temperatura como texto) | Rechazarse |
| 6 | Sin un campo obligatorio (`humedad_aire_pct`) | Rechazarse |
| 7 | De simulación en vivo, con `escenario_id` en `meta` | Entrar |

## Resultados

### Prueba 1: crear la colección con el validador incluido

| Colección | Resultado al crear |
|---|---|
| Serie temporal con validador | ❌ "'timeseries' is not allowed with 'validator'" |
| Colección común con validador | ✅ |

**Cuidado con un efecto engañoso:** como la serie temporal no se creó, el primer `insertOne` creó **automáticamente una colección común sin validación**. Por eso en esas colecciones entraron los siete documentos, incluidos los inválidos. MongoDB crea la colección sola si no existe, así que un error al crearla puede pasar desapercibido.

Resultados en las colecciones comunes:

| Caso | Común **sin** `_id` en el esquema | Común **con** `_id` en el esquema |
|---|---|---|
| 1. Válido | ❌ Rechazado | ✅ Entra |
| 2. Campo de más | ❌ Rechazado | ❌ Rechazado |
| 3. Error de tipeo | ❌ Rechazado | ❌ Rechazado |
| 4. Campo de más en `meta` | ❌ Rechazado | ❌ Rechazado |
| 5. Tipo equivocado | ❌ Rechazado | ❌ Rechazado |
| 6. Falta un campo | ❌ Rechazado | ❌ Rechazado |
| 7. Con `escenario_id` | ❌ Rechazado | ✅ Entra |

**Explicación:** con el esquema cerrado, si `_id` no está declarado, MongoDB lo considera un "campo de más" y rechaza **todos** los documentos, incluso los válidos. Declarando `_id`, el esquema hace exactamente lo esperado: entran los válidos y se rechazan los cinco inválidos.

### Prueba 2: crear la serie temporal y agregar el validador después (`collMod`)

| Paso | Resultado |
|---|---|
| Crear la serie temporal sin validador | ✅ |
| Agregar el validador con `collMod` | ❌ "option not supported on a time-series collection: validator" |
| Insertar los siete documentos | ✅ Entran todos, también los inválidos |
| `insertMany` de 3 documentos con 1 inválido | ✅ Entran los 3 |

**Explicación:** en MongoDB 9.0.2, una serie temporal **no admite validador de ninguna forma**: ni al crearla ni después. Cualquier documento entra.

### Prueba 3: usar el `$jsonSchema` como filtro de búsqueda (auditoría)

Se cargaron los siete documentos en una serie temporal sin validador y se buscó con el mismo esquema.

| Caso | Consulta | Resultado |
|---|---|---|
| 1. Lecturas que **cumplen** el esquema | `find({ $jsonSchema: esquema })` | ✅ Devuelve exactamente los casos 1 y 7 (los válidos) |
| 2. Lecturas que **no cumplen** (auditoría) | `find({ $nor: [{ $jsonSchema: esquema }] })` | ✅ Devuelve exactamente los casos 2 a 6 (los inválidos) |
| 3. Contar las mal formadas | `aggregate([{ $match: { $nor: [...] } }, { $count: ... }])` | ✅ `mal_formadas: 5` |
| 4. Auditoría por nodo y rango de fechas | `countDocuments({ "meta.nodo_id": ..., ts: {...}, $nor: [...] })` | ✅ 5 |
| 5. Borrar las mal formadas | `deleteMany({ $nor: [{ $jsonSchema: esquema }] })` | ✅ Borra 5 y quedan solo las 2 válidas |

**Explicación:** aunque la serie temporal no acepta el esquema como **regla de entrada**, sí lo acepta como **filtro de búsqueda**. `$nor` significa "que no cumpla": devuelve todo lo que no respeta el esquema. Detecta los cinco tipos de error, incluidos el campo de más dentro de `meta` y el error de tipeo. Y como en series temporales se puede borrar con cualquier filtro (spike del 14/10/2026), las lecturas mal formadas también se pueden eliminar.

## Conclusiones

1. **En las colecciones comunes el esquema cerrado funciona**, como decidió el ADR-006: rechaza campos de más, errores de tipeo, tipos equivocados y campos faltantes, también dentro de subdocumentos como `meta`.
2. **Con esquema cerrado hay que declarar `_id`** en `properties` (`bsonType: "string"` en fincas, parcelas y nodos; `"objectId"` en el resto). Si no, la colección rechaza todo.
3. **`lecturas` no puede validarse con `$jsonSchema`** en MongoDB 9.0.2, porque es una serie temporal. La decisión del ADR-006 de validar **todas** las colecciones no se puede cumplir para `lecturas`.
4. **El esquema sí sirve como auditoría en `lecturas`:** el mismo `$jsonSchema`, usado como filtro con `$nor`, encuentra (y permite borrar) exactamente las lecturas mal formadas. Así un solo esquema sirve para las dos cosas: regla de entrada en las colecciones comunes y control posterior en la serie temporal.
5. **Siempre hay que verificar que la colección se creó bien** antes de insertar. Si `createCollection` falla, el primer insert crea una colección común sin validación y el error queda oculto. El script de creación tiene que detenerse ante cualquier error.

## Decisión

Se eligió la **opción C** (validar en el simulador y auditar después). Registrada en [ADR-007](../decisions/ADR-007-validacion-lecturas.md).

## Opciones evaluadas

Cómo se protege `lecturas`, que es la colección más grande (unas 732.700 lecturas). Opciones a evaluar:

| Opción | Cómo funciona |
|---|---|
| A. Validar en el simulador | El código Python revisa cada lectura antes de insertarla |
| B. Consulta de auditoría | El mismo `$jsonSchema` se usa como filtro de búsqueda (`find({ $nor: [{ $jsonSchema: ... }] })`) para encontrar lecturas mal formadas después de cargarlas. **Verificado en la prueba 3** |
| C. A y B juntas | Se valida al insertar y se audita después |
| D. Volver a una colección común | Contradice el ADR-001 y pierde las ventajas de las series temporales |

