# Usuarios y flujos

**Estado:** esqueleto, se completa en el Sprint A.

## Usuarios

| Usuario | Qué necesita |
|---|---|
| Productor o encargado de finca | Saber qué parcelas están en riesgo, desde cuándo y si ya se regó |
| Técnico agrónomo | Ver cuántas horas estuvo cada parcela bajo su umbral |
| Administrador del sistema | Detectar nodos caídos y verificar los backups |

## Criterios de UX

| Criterio | Implicancia de diseño |
|---|---|
| Lectura rápida | Estado por parcela con semáforo, sin tablas largas |
| Alerta accionable | Qué parcela, qué temperatura, desde cuándo y si ya se regó |
| Poca fatiga de alertas | Una alerta por evento, que se cierra sola al recuperarse |
| Confianza en el dato | "Último dato hace X min" y nodos inactivos marcados |
| Lenguaje del productor | "Parcela", "helada", "riego"; nada de "documento" ni "colección" |
| Escritorio primero | Varios paneles a la vez: mapa, curva y alertas |
| Demo sencilla | Arranca con un comando y no depende de internet |

## Flujos

1. **Revisar la mañana** (hecho, [ADR-018](../decisions/ADR-018-resumen-de-la-manana.md)): el encargado abre "Resumen de la mañana", lee la frase de estado, mira en la tabla qué parcelas se helaron, desde cuándo y si se regaron, y ubica la parcela en el mapa.
2. **Investigar una alerta** (hecho, [ADR-019](../decisions/ADR-019-detalle-de-parcela.md)): desde la tabla del resumen, un clic en la parcela abre su detalle con la misma noche; ahí se ve la curva contra el umbral, cuánto duró y qué pasó con el suelo y el riego.
3. **Revisar las alertas** (hecho, [ADR-020](../decisions/ADR-020-alertas.md)): desde la barra lateral, la pantalla "Alertas" muestra las de la noche elegida, el historial y las heladas por semana; un clic en la parcela abre su detalle.
4. **Verificar los nodos** (hecho, [ADR-021](../decisions/ADR-021-estado-de-nodos.md)): desde la barra lateral, "Estado de nodos" dice cuántos reportan, cuáles no y desde cuándo, y un clic en la parcela abre su detalle.

## Wireframes

Se hacen con **Excalidraw** (gratuito, desde el navegador). Por cada pantalla se guardan en `wireframes/` el archivo editable `.excalidraw` y su exportación `.png`:

| Pantalla | Archivos |
|---|---|
| Resumen de finca | `resumen-finca.excalidraw`, `resumen-finca.png` |
| Detalle de parcela | `detalle-parcela.excalidraw`, `detalle-parcela.png` |
| Alertas | `alertas.excalidraw`, `alertas.png` |
| Estado de nodos | `estado-nodos.excalidraw`, `estado-nodos.png` |

Los elementos de cada pantalla están en [`pantallas.md`](pantallas.md). *A crear en el Sprint A.*
