# Modelo de datos

**Estado:** esqueleto. Es el entregable central del Sprint A y se trabaja entre los dos integrantes.

## 1. Consultas que guían el modelo

Ver Q1 a Q8 en [`requisitos.md`](requisitos.md). El modelo es adecuado si las responde de forma simple y eficiente.

## 2. Colecciones

| Colección | Campos principales | Notas |
|---|---|---|
| `fincas` | *A definir* | |
| `parcelas` | *A definir* | |
| `nodos` | *A definir* | |
| `lecturas` | `ts`, `meta` (`nodo_id`, `parcela_id`, `finca_id`), resto *a definir* | Ver [ADR-001](decisions/ADR-001-series-temporales.md) |
| `alertas` | *A definir* | |
| `riegos` | *A definir* | |
| `eventos_climaticos` | *A definir* | |
| `umbrales_fenologia` | `estado`, `umbral_helada_c`, `fuente_umbral` | Configuración. Ver [ADR-003](decisions/ADR-003-decisiones-modelado-inicial.md) |

## 3. Relaciones y decisiones de modelado

Regla de partida: embeber lo que se lee junto y referenciar lo que crece sin límite.

Decisiones tomadas (detalle en [ADR-003](decisions/ADR-003-decisiones-modelado-inicial.md)):

- Los umbrales de helada viven en la colección de configuración `umbrales_fenologia`; la parcela guarda solo su `fenologia`.
- `alertas` guarda solo referencias (`parcela_id`); el departamento se obtiene con `$lookup` alertas → parcelas → fincas (Q8).
- `lecturas.meta` incluye `nodo_id`, `parcela_id` y `finca_id`, para filtrar por parcela o finca sin `$lookup`.
- La alerta de riego se dispara cuando la humedad de suelo baja de un umbral configurable (supuesto del proyecto).

*A completar:* el resto de las relaciones.

## 4. Diagrama

*A completar* (diagrama de colecciones y relaciones).

## 5. Validaciones

*A completar:* esquemas `$jsonSchema` en `db/schemas/`.

## 6. Índices

*A completar:* índices en `db/indexes/`, con la consulta que justifica cada uno.

## 7. Ejemplos de documentos

*A completar.*
