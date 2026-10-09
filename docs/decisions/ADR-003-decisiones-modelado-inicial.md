# ADR-003: Decisiones iniciales de modelado

**Estado:** Aceptado (8/10/2026).

## Contexto

Antes de escribir `modelo-datos.md` y los esquemas, el equipo eligió entre dos opciones para cuatro puntos del modelo.

## Decisiones

### 1. Umbrales de helada en una colección de configuración

> **Reemplazada por [ADR-004](ADR-004-temporada-malbec.md):** la colección pasa a llamarse `variedades` y guarda umbrales y grados-día por etapa BBCH.

| Opción | Ventaja | Desventaja |
|---|---|---|
| **Colección `umbrales_fenologia` (elegida)** | El valor se cambia en un solo lugar; Q2 hace un `$lookup` claro | Agrega una colección de configuración al modelo |
| Umbral embebido en cada parcela | Q2 sin `$lookup` extra | El mismo valor se repite en las parcelas y hay que actualizarlo en todas |

### 2. Alertas solo con referencias

| Opción | Ventaja | Desventaja |
|---|---|---|
| **`parcela_id` y `$lookup` alertas → parcelas → fincas (elegida)** | Sin datos duplicados; muestra `$lookup` encadenado en Q8 | Consulta más pesada |
| Copia de `finca_id` y `departamento` en la alerta | Q8 con un `$group` directo | Dato duplicado que hay que justificar |

### 3. Contenido de `lecturas.meta`

| Opción | Ventaja | Desventaja |
|---|---|---|
| **`nodo_id`, `parcela_id`, `finca_id` (elegida)** | Q1, Q6 y el dashboard filtran por parcela o finca sin `$lookup` | Si un nodo cambia de parcela, las lecturas viejas conservan la parcela anterior (históricamente correcto) |
| Solo `nodo_id` | Mínimo, sin duplicación | Casi toda consulta por parcela necesita `$lookup` a `nodos` sobre unas 100.000 lecturas |

### 4. Disparo de la alerta de riego

| Opción | Ventaja | Desventaja |
|---|---|---|
| **Umbral de humedad de suelo configurable (elegida)** | Usa la variable medida por los sensores | No hay umbral oficial: es un supuesto del proyecto, a validar |
| Días sin evento en `riegos` | No depende de sensores | Ignora la humedad medida |

## Consecuencias

- El modelo queda con 7 colecciones de dominio más `umbrales_fenologia`.
- Q8 es la consulta que demuestra `$lookup` encadenado; conviene medir su rendimiento en `performance.md`.
- El valor del umbral de humedad de suelo debe documentarse como supuesto.
