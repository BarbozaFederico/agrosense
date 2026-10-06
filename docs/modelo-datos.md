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
| `lecturas` | *A definir* | Ver [ADR-001](decisions/ADR-001-series-temporales.md) |
| `alertas` | *A definir* | |
| `riegos` | *A definir* | |
| `eventos_climaticos` | *A definir* | |

## 3. Relaciones y decisiones de modelado

*A completar:* qué se embebe y qué se referencia, con el motivo de cada decisión. Regla de partida: embeber lo que se lee junto y referenciar lo que crece sin límite.

## 4. Diagrama

*A completar* (diagrama de colecciones y relaciones).

## 5. Validaciones

*A completar:* esquemas `$jsonSchema` en `db/schemas/`.

## 6. Índices

*A completar:* índices en `db/indexes/`, con la consulta que justifica cada uno.

## 7. Ejemplos de documentos

*A completar.*
