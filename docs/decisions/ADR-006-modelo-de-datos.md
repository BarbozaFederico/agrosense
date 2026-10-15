# ADR-006: Detalle del modelo de datos y de la validación

**Estado:** Aceptado (14/10/2026). Completa [ADR-003](ADR-003-decisiones-modelado-inicial.md). El modelo completo está en [`modelo-datos.md`](../modelo-datos.md).

## Contexto

Antes de escribir los `$jsonSchema` hacía falta definir los campos de cada colección y algunas decisiones de diseño que las ADR anteriores no cubrían. Para cada una se compararon dos opciones.

## Decisiones

| # | Tema | Elegida | Descartada | Motivo |
|---|---|---|---|---|
| 1 | Identificadores de fincas, parcelas y nodos | **Códigos legibles** (`F-SR`, `P-SR-1`, `N-SR-1-A`) | `ObjectId` automático | Se leen en lecturas y alertas sin `$lookup`; más fácil de depurar y explicar. Hay que garantizar a mano que sean únicos |
| 2 | Etapas de la variedad | **Array embebido** en `variedades` | Colección `etapas_fenologicas` | Se leen siempre juntas y son pocas: es el caso típico de embeber |
| 3 | Alerta abierta | **`estado: "abierta"` y `fin: null`** | Sin campo `fin` hasta cerrar | Buscar activas es simple y el esquema siempre tiene los mismos campos |
| 4 | Parámetros configurables | **Colección `configuracion`** (un documento) | Repartidos entre colecciones y código | Un solo lugar, se cambian sin tocar código |
| 5 | Etapa actual de la parcela | **Se calcula siempre** (observación o Q9) | Campo `etapa_actual` | Un solo origen de verdad; funciona con el selector de fecha |
| 6 | Índice de riesgo | **Se guarda en la alerta de helada al cerrar** | Solo calculado con Q10 | El historial no cambia si cambian los cortes; Q10 sigue como cálculo por noche |
| 7 | Agua de cada riego | **`lamina_mm` y `litros`** | Solo litros | Los mm conectan con las fuentes; los litros alimentan Q7 |
| 8 | Nombres de los valores medidos | **Con unidad** (`temperatura_c`, `humedad_suelo_pct`, `humedad_aire_pct`) | Sin unidad | La unidad nunca queda en duda |
| 9 | Acción ante un documento inválido | **`validationAction: "error"`** | `"warn"` | La base nunca guarda datos mal formados y se puede demostrar |
| 10 | Campos no definidos | **Esquema cerrado** (`additionalProperties: false`) | Esquema abierto | Un error de tipeo falla en lugar de guardarse |
| 11 | `estado` de un nodo | **Administrativo** (`activo`, `mantenimiento`, `baja`) | Estado de conexión guardado | Si un nodo dejó de reportar se calcula con Q5 y la fecha elegida |

## Consecuencias

- Se agrega la colección de configuración **`configuracion`** al modelo (total: 8 colecciones de dominio y 2 de configuración).
- `lecturas.meta` incluye también `fuente`.
- Los esquemas cerrados obligan a actualizar `db/schemas/` antes de agregar cualquier campo.
- El simulador calcula `litros` al insertar cada riego, con la superficie de la parcela.
