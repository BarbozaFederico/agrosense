# Modelo de datos

**Estado:** esqueleto. Es el entregable central del Sprint A y se trabaja entre los dos integrantes.

## 1. Consultas que guían el modelo

Ver Q1 a Q10 en [`requisitos.md`](requisitos.md). El modelo es adecuado si las responde de forma simple y eficiente.

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
| `variedades` | Nombre, `ficticia`, y por etapa BBCH: umbral de helada y grados-día (valores en ADR-005); *resto a definir* | Configuración. Ver [ADR-004](decisions/ADR-004-temporada-malbec.md) |
| `observaciones_fenologicas` | *A definir* | Etapa BBCH observada a mano |

## 3. Relaciones y decisiones de modelado

Regla de partida: embeber lo que se lee junto y referenciar lo que crece sin límite.

Decisiones tomadas (detalle en [ADR-003](decisions/ADR-003-decisiones-modelado-inicial.md)):

- Los umbrales de helada y los grados-día por etapa viven en la colección de configuración `variedades` (ADR-004 reemplaza a `umbrales_fenologia`); la parcela guarda su variedad.
- La etapa vigente sale de la última observación manual o, si no hay, de la estimación por grados-día (Q9).
- Cada finca guarda su sistema de riego y su tipo de suelo; Δ (sensor − brote) y los cortes del índice de riesgo son parámetros de configuración ([ADR-005](decisions/ADR-005-parametros-simulacion.md)).
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
