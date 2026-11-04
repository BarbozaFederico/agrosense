# Rendimiento

**Estado:** medido (4/11/2026). Requisito RNF-01: mediciones antes y después de aplicar índices. Qué índices se crean y por qué: [ADR-022](decisions/ADR-022-simplificar-indices.md) y [ADR-015](decisions/ADR-015-indices-de-rendimiento.md).

## Qué se mide

Un **índice** es una estructura auxiliar que permite a MongoDB encontrar documentos sin leer toda la colección. Para ver si sirve se compara una sola cifra, con y sin el índice: los **documentos examinados**, que es el campo `totalDocsExamined` de `explain("executionStats")`. Es la cantidad de documentos que MongoDB tuvo que leer para armar la respuesta.

En `lecturas` (una serie temporal) cuenta grupos de lecturas ("buckets"), no lecturas sueltas.

## Resultado

Medido el 4/11/2026 en la base `agrosense_tests` (mismos datos que `agrosense`: 727.980 lecturas), MongoDB 9.0.2.

| Índice | Consulta | Documentos examinados sin índice | Documentos examinados con índice | Reducción |
|---|---|---|---|---|
| `nodos { ubicacion: 2dsphere }` | Q3 | no funciona | 4 | - |
| `parcelas { geometria: 2dsphere }` | Q4 | 6 | 2 | 67% |
| `lecturas { meta.nodo_id: 1, ts: -1 }` | Q5 | 365 | 32 | 91% |
| `riegos { parcela_id: 1, inicio: 1 }` | Q7 | 563 | 33 | 94% |

- **Q3:** sin el índice `2dsphere`, `$geoNear` y `$near` fallan ("error enumerating plans"). Es un índice necesario, no una optimización.
- **Q4:** con 6 parcelas la diferencia es chica; devuelve lo mismo con y sin el índice.
- **Q5:** busca la última lectura de un nodo. El índice automático de la serie temporal (`meta_1_ts_1`) no sirve para esta búsqueda por `meta.nodo_id` y `ts`.
- **Q7:** sin el índice lee los 563 riegos; con él, solo los 33 de la parcela.

La mejora se ve en documentos examinados y no en milisegundos, porque las colecciones son chicas. El índice importa cuando la colección crece.

## Cómo repetirlo a mano en `mongosh`

Abrir `mongosh` y usar `use agrosense_tests`. Cada comando muestra los documentos examinados en `executionStats.totalDocsExamined` (en `lecturas`, por ser serie temporal, está en `stages[0].$cursor.executionStats.totalDocsExamined`).

**Con índice**, por ejemplo para `riegos`:

```js
db.riegos.find({ parcela_id: "P-SR-1" }).explain("executionStats")
```

**Sin índice, sin borrarlo:** agregar `.hint({ $natural: 1 })` antes de `.explain(...)`, que obliga a leer la colección entera:

```js
db.riegos.find({ parcela_id: "P-SR-1" }).hint({ $natural: 1 }).explain("executionStats")
```

Los otros tres, en el mismo formato (el comando "sin índice" es el mismo con `.hint({ $natural: 1 })`):

```js
// Q3: sin índice no funciona (db.nodos.dropIndex("ubicacion_2dsphere") y repetir para verlo)
db.nodos.find({ ubicacion: { $near: { $geometry: { type: "Point", coordinates: [-68.330881, -34.61] } } } }).limit(4).explain("executionStats")

// Q4
const area = db.eventos_climaticos.find().sort({ inicio: -1 }).limit(1).next().area
db.parcelas.find({ geometria: { $geoIntersects: { $geometry: area } } }).explain("executionStats")

// Q5
db.lecturas.find({ "meta.nodo_id": "N-SR-1-A" }).sort({ ts: -1 }).limit(1).explain("executionStats")
```

## Cómo reproducirlo con el script

```bash
python -m db.indexes.medir_indices    # imprime la tabla de arriba y estos comandos (usa agrosense_tests)
python -m db.indexes.probar_indices   # 20 casos: los índices existen, se usan y no cambian ninguna respuesta
python -m db.indexes.crear_indices    # crea los 4 índices en la base de AGROSENSE_BD
```

`medir_indices` borra y crea índices, por eso trabaja siempre sobre `agrosense_tests` y no toca `agrosense`.
