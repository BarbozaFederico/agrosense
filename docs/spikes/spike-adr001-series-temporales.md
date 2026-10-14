# Spike ADR-001: series temporales en MongoDB 9.0

**Fecha:** 14/10/2026 · **Versión probada:** MongoDB Server 9.0.2, `mongosh` 2.13.0 · **ADR:** [ADR-001](../decisions/ADR-001-series-temporales.md)

## Pregunta a responder

¿Funcionan las colecciones de series temporales para `lecturas` en la versión instalada? En particular:

1. ¿Se pueden crear e insertar datos?
2. ¿Qué se puede actualizar y borrar? (Importa para RF-15, "Reiniciar demo").
3. ¿Se combinan con los índices geoespaciales `2dsphere`? (Importa para Q3 y Q4).

## Cómo se probó

Tres scripts de `mongosh` en [`scripts/spike-adr001/`](../../scripts/spike-adr001/). Usan una base de **prueba** llamada `spike_agrosense`, que borran y vuelven a crear en cada ejecución, con datos inventados.

```bash
mongosh --file scripts/spike-adr001/01_crear_serie_temporal.js
```

```bash
mongosh --file scripts/spike-adr001/02_actualizar_y_borrar.js
```

```bash
mongosh --file scripts/spike-adr001/03_indice_2dsphere.js
```

## Resultados

### Prueba 1: crear la colección e insertar

✅ **Funciona.** La colección se crea con tipo `timeseries` y acepta las 6 lecturas de prueba.

- MongoDB agrega solo dos opciones: `bucketMaxSpanSeconds: 86400` (agrupa las lecturas en "baldes" de hasta un día) y `fixedBucketing: true`.
- Crea automáticamente un índice sobre `meta` y `ts` (`meta_1_ts_1`), que sirve para las consultas por nodo o parcela y rango de fechas.
- MongoDB guarda los campos en otro orden: es normal en series temporales y no afecta a las consultas.

### Prueba 2: actualizar y borrar

| Caso | Resultado | Explicación |
|---|---|---|
| 1. Cambiar la temperatura de una lectura con `updateOne` | ❌ | No se permite `updateOne` en series temporales |
| 1b. Lo mismo con `updateMany`, filtrando por `ts` | ❌ | Para actualizar, el filtro solo puede usar campos de `meta` |
| 1c. Lo mismo con `updateMany`, filtrando solo por `meta` | ❌ | Solo se pueden modificar campos de `meta`, no los valores medidos |
| 2. Cambiar `meta.parcela_id` de todo un nodo | ✅ | Actualizar campos de `meta` con `updateMany` sí se permite |
| 3. Borrar por `meta.escenario_id` | ✅ | Borró las 2 lecturas de la "simulación en vivo" |
| 4. Borrar por rango de fechas (`ts`) | ✅ | Borró 2 lecturas |
| 5. Borrar por un valor medido (`temperatura < -1`) | ✅ | Borró 2 lecturas |
| 6. Borrar una sola lectura (`deleteOne`) | ✅ | Borró 1 lectura |
| 7. Borrar todo (`deleteMany({})`) | ✅ | Borró las 5 lecturas |

**En resumen:** en MongoDB 9.0 **borrar se puede con cualquier filtro**, pero **actualizar está muy limitado**: solo con `updateMany` y solo campos de `meta`.

### Prueba 3: índices geoespaciales

| Caso | Resultado | Explicación |
|---|---|---|
| 1. Índice `2dsphere` sobre un **polígono** en una serie temporal | ❌ | "Time-series collections '2dsphere' indexes only support point data": solo acepta puntos |
| 1b. Índice `2dsphere` sobre un **punto** en una serie temporal | ✅ | Se crea sin problema |
| 2. Índice `2dsphere` sobre un punto dentro de `meta` | ✅ | Se crea sin problema |
| 3. Índice `2dsphere` sobre un polígono en una colección **común** | ✅ | Funciona normal |
| 4. `$geoIntersects` en colección común | ✅ | Encontró el polígono |
| 5. `$geoIntersects` en la serie temporal (sin índice) | ✅ | Encontró el polígono, pero recorriendo todos los documentos: no puede usar índice |
| 6. `$geoNear` en la serie temporal (índice en `meta.ubicacion`) | ⚠️ | Devuelve los nodos, pero **el campo de distancia sale vacío** (`null`) |
| 7. `$geoNear` en colección común | ✅ | Devuelve los nodos ordenados y la distancia en metros (0 y 159.737 m) |

## Conclusiones

1. **Se confirma el ADR-001:** `lecturas` va como serie temporal. Se crea, inserta y consulta sin problemas en MongoDB 9.0.2.
2. **"Reiniciar demo" (RF-15) se puede hacer.** Borrar con `deleteMany({ "meta.escenario_id": ... })` funciona. Por eso, **`escenario_id` va dentro de `meta`**, junto con `nodo_id`, `parcela_id` y `finca_id`.
3. **Las lecturas no se corrigen, se reemplazan.** Como no se pueden actualizar los valores medidos, si una lectura sale mal se borra y se vuelve a insertar. Para un registro de sensores es razonable: una medición no se edita.
4. **`eventos_climaticos` va como colección común.** Sus áreas afectadas son polígonos, y las series temporales solo aceptan puntos en índices `2dsphere`. Así lo preveía `CLAUDE.md` (sección 5).
5. **Q3 (nodos más cercanos) se hace sobre la colección `nodos`, no sobre `lecturas`.** `nodos` es una colección común: `$geoNear` funciona y devuelve la distancia. En la serie temporal la distancia sale vacía.
6. **La ubicación no se guarda en cada lectura.** Vive en `nodos` (y la geometría en `parcelas`), que son colecciones comunes con índice `2dsphere`. Si hace falta cruzar lecturas con ubicación, se usa `$lookup` desde `lecturas` a `nodos` por `meta.nodo_id`.

## Qué cambia en el proyecto

| Tema | Decisión |
|---|---|
| `lecturas.meta` | `nodo_id`, `parcela_id`, `finca_id` y, solo en simulaciones en vivo, `escenario_id` |
| `eventos_climaticos` | Colección común, con `2dsphere` sobre el polígono |
| Q3 | `$geoNear` sobre `nodos` |
| Q4 | `$geoIntersects` sobre `parcelas` y `eventos_climaticos` (colecciones comunes) |
| Corrección de lecturas | Borrar y volver a insertar |

## Pendiente

- No se verificó si el campo de distancia vacío del caso 6 es una limitación documentada de MongoDB o un detalle de cómo se escribió la consulta. No afecta al proyecto, porque Q3 se hace sobre `nodos`.
