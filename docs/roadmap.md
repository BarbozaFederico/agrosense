# Hoja de ruta

**Entrega:** miércoles 28 de octubre de 2026. Equipo de dos personas. Duración total: unas tres semanas.

## Calendario

| Sprint | Fechas | Qué se hace | Entregable |
|---|---|---|---|
| **A** | mar 6/10 a lun 12/10 | Repo y documentación base, MongoDB instalado, modelado y validaciones, wireframes, simulador base | `modelo-datos.md`, esquemas, seed de fincas, parcelas y nodos, wireframes |
| **B** | mar 13/10 a lun 19/10 | Carga de la temporada simulada (unas 732.700 lecturas), consultas Q1 a Q10, índices con medición, noche precargada, inicio del dashboard | Q1 a Q10 en `db/queries/`, `performance.md`, dashboard con datos del seed |
| **C** | mar 20/10 a lun 26/10 | Dashboard completo (4 pantallas, tema oscuro), backup con restauración probada, roles, demo sin internet | Dashboard, `backup-restore.md`, roles |
| **Cierre** | mar 27/10 y mié 28/10 | Congelar el código, ensayar la demo, tag `v1.0.0`, entrega | Entrega final |

> El lunes 12/10 es feriado: el Sprint A tiene un día hábil menos.

## Prioridades (lo que se sacrifica primero va al final)

1. Núcleo de la base: modelo, carga, Q1 a Q10 (incluye etapa por grados-día e índice de riesgo), índices con medición, backup con restauración.
2. Dashboard con las 4 pantallas y la noche precargada.
3. Estilo visual oscuro y pulido.
4. Variedad simulada X (RF-20).
5. Simulación en vivo (RF-14 y RF-15). **Es lo primero que se recorta.**

## Reparto

El reparto es por funcionalidad completa, de la base al dashboard. Detalle en [`equipo.md`](equipo.md).

## Issues iniciales del Sprint A

| # | Tipo | Tarea | Responsable |
|---|---|---|---|
| 1 | docs | Copiar los informes de investigación a `docs/investigacion/` (quitando datos de contacto personales) | Integrante 1 |
| 2 | chore | Instalar MongoDB, `mongosh` y Compass; verificar la versión | Ambos |
| 3 | spike | CRUD básico en `mongosh` y notas de lo aprendido | Ambos |
| 4 | spike | Probar series temporales en la versión instalada (borrado e índices geoespaciales), según [ADR-001](decisions/ADR-001-series-temporales.md) | Integrante 1 |
| 5 | docs | `modelo-datos.md`: colecciones, embeber o referenciar, diagrama | Ambos |
| 6 | feat | Validaciones `$jsonSchema` de `nodos`, `lecturas` y `alertas` | Integrante 1 |
| 7 | feat | Validaciones `$jsonSchema` de `fincas`, `parcelas`, `eventos_climaticos` y `riegos` | Integrante 2 |
| 8 | feat | Simulador base: temporada 1/9/2026 a 31/3/2027, 12 nodos, funciones importables | Integrante 1 |
| 9 | feat | Seed de 3 fincas, 6 parcelas y 12 nodos con geometrías | Integrante 2 |
| 10 | docs | Wireframes de las 4 pantallas (2 por persona) | Ambos |
| 11 | chore | Crear labels, milestones y board de GitHub | Integrante 1 |
| 12 | docs | Completar `README.md` con los pasos de ejecución | Integrante 2 |

## Qué quedó fuera por el plazo

Alerta temprana y pronóstico, Docker, Atlas, datos reales de la DACC y de ERA5-Land, y versión móvil.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Plazo corto | Prioridades explícitas; la simulación en vivo se recorta primero |
| Dashboard obligatorio compite con el núcleo | El dashboard arranca con datos del seed en el Sprint B, sin esperar al cierre del núcleo |
| La demo falla en vivo | Noche precargada y prueba previa sin internet |
