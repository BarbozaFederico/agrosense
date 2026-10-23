# ADR-021: Cuarta pantalla del dashboard, "Estado de nodos"

**Estado:** Aceptado (22/10/2026). Requisitos RF-06, RF-11 y RF-12. Continúa [ADR-018](ADR-018-resumen-de-la-manana.md), [ADR-019](ADR-019-detalle-de-parcela.md) y [ADR-020](ADR-020-alertas.md) (mismo mundo visual, mismo "ahora" y misma navegación) y reemplaza el apartado 3.4 de [`ux/pantallas.md`](../ux/pantallas.md). Con esta pantalla quedan hechas las 4 del MVP. Los roles y la autenticación siguen reservados para el ADR-017.

## Contexto

La cuarta pantalla de `pantallas.md` es "Estado de nodos": qué sensores reportan, cuáles no y desde cuándo. Es la pantalla de "confianza en el dato" de los criterios de UX, y la usa el administrador, el técnico o el encargado que duda de un valor. Al diseñarla se midieron los datos antes de decidir: con el "ahora" de las otras pantallas (las 12:00 de la mañana elegida) los 12 nodos reportan en casi toda la temporada. Solo hay nodos sin reportar en 17 días: el 3/12 (N-SM-2-B, 10 h), el 2/3 (N-SM-1-B, 65 min) y del 17/3 en adelante (N-TU-2-B, que deja de reportar el 17/3 a las 02:55 UTC). Además, N-TU-2-B figura `mantenimiento` en el catálogo durante **toda** la temporada, pero reporta hasta el 17/3. Se acordó con el equipo el "ahora", cómo mostrar los dos estados y el alcance (filas 1 a 3).

## Decisiones

| # | Tema | Decisión | Descartadas |
|---|---|---|---|
| 1 | El "ahora" | **Las 12:00 de la mañana elegida**, igual que Resumen, Detalle y Alertas. Casi siempre dice "Los 12 nodos reportan", que es lo que muestra la base a esa hora. El subtítulo lo dice ("A las 12:00 del 5 de oct de 2026") | Un selector de hora en esta pantalla (muestra cortes como el del 12/11 de 13:55 a 20:00, pero suma un control y un "ahora" distinto del resto de la app) |
| 2 | Dos estados distintos | **"Reporte"** (calculado: reporta o sin reportar, con círculo verde o triángulo ámbar y la palabra) y **"Estado del nodo"** (administrativo del catálogo: activo, mantenimiento o baja). Cuando se contradicen, la celda lo aclara: "mantenimiento · sigue reportando" o "activo, pero no reporta". Un nodo no reporta si pasaron más de `configuracion.nodo_inactivo_min` (30) minutos desde su última lectura o si no tiene ninguna, la misma regla que Q5 | Un solo estado combinado (esconde que un nodo "en mantenimiento" sigue reportando) |
| 3 | Pantalla | Frase de estado ("Los 12 nodos reportan." o "1 de 12 nodos sin reportar: N-TU-2-B." con cuánto lleva sin datos y cuándo fue su último reporte), el último dato de la red, y una **tabla de los nodos**: los que no reportan primero (los sin lecturas, luego el de más tiempo) y resaltados en ámbar, el resto por nombre. Columnas: reporte, nodo, parcela (enlace al detalle), último reporte, hace cuánto y estado del nodo. El tiempo se escribe para leer rápido ("5 min", "12 h 05 min", "14 días 12 h") | Una tarjeta por nodo (12 tarjetas iguales no dicen cuál mirar) |
| 4 | Alcance | **Solo lo de `pantallas.md`**: lista, inactivos resaltados y Q5, con filtro de finca y fecha en la barra lateral. Sin historial de cortes, mapa, temperaturas ni edición | Sumar los cortes de reporte de la temporada (una ventana sobre las 728.000 lecturas: consulta nueva y más pruebas, fuera del alcance) |
| 5 | Consulta | Q5 devuelve solo los nodos que **no** reportan, y la pantalla necesita los 12 con su último reporte. Se agrega `db/queries/estado_nodos.py` (no es Q11), armada con las **primeras 3 etapas de Q5** (el `$lookup` a la última lectura y el cálculo de los minutos) y un `$project`, para que las dos no puedan discrepar. Una prueba compara, en 75 fechas de la temporada, los nodos que la pantalla marca sin reportar con los de Q5 | Copiar el `$lookup` de Q5 (dos versiones de la misma regla) |
| 6 | Dónde viven los textos | `dashboard/piezas_nodos.py` (sin Streamlit ni MongoDB) y `formato.py` (`duracion_larga` y `marca_reporte`). Todo texto que viene de la base pasa por `html.escape` | Funciones dentro de la página |

## Consecuencias

- **Las 4 pantallas del MVP están hechas.** `lateral.PANTALLAS_PENDIENTES` queda vacía y la barra lateral ya no muestra "en construcción". Se agregó una línea divisoria entre el menú y los selectores.
- Los cortes de reporte que ocurren fuera de las 12:00 (como el del 12/11) no se ven en esta pantalla. Es un límite conocido de la decisión 1, no un descuido.
- La lista no distingue un nodo sin reportar por un corte de uno dado de baja: para eso está la columna "Estado del nodo".
- Pruebas: `python -m dashboard.probar_nodos` (31 casos: formato, datos, textos y la coincidencia con Q5) y 10 casos nuevos de punta a punta en `python -m dashboard.probar_pantallas` (46 en total, entre ellos el 3/12, el 2/3 y el 31/3). Verificado en el navegador a 1440 px de ancho. Falta la prueba con el wifi apagado y en pantallas angostas.
