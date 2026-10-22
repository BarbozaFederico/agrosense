# ADR-019: Segunda pantalla del dashboard, "Detalle de parcela", y navegación entre pantallas

**Estado:** Aceptado (22/10/2026). Requisitos RF-11 y RF-12. Continúa [ADR-018](ADR-018-resumen-de-la-manana.md) (mismo mundo visual, mismas reglas de datos) y reemplaza el apartado 3.2 de [`ux/pantallas.md`](../ux/pantallas.md). Los roles y la autenticación siguen reservados para el ADR-017.

## Contexto

Con "Resumen de la mañana" hecha, la siguiente pantalla de `pantallas.md` es "Detalle de parcela". La usa el técnico agrónomo, o el encargado que viene desde una fila del resumen, para entender **por qué saltó la alerta**: cuándo y cuánto bajó la temperatura del brote contra su umbral, cuánto duró y qué pasó con el suelo y el riego. Se acordó con el equipo el foco, la forma de llegar a la pantalla y qué dibuja la curva (filas 1 a 3).

## Decisiones

| # | Tema | Decisión | Descartadas |
|---|---|---|---|
| 1 | Foco | **Por qué saltó la alerta.** Arriba una frase con lo que pasó (mínima del brote, margen contra el umbral, alerta, riesgo y si se regó); en el centro la curva de la noche; abajo, como contexto, la humedad de suelo y los riegos | Tres paneles del mismo peso (no dice qué mirar primero) |
| 2 | Cómo se llega y se navega | **Clic en la fila del resumen** (el nombre de la parcela es un enlace a `detalle?parcela=...&fecha=...`) **y selector de parcela** en la barra lateral. La app pasa a `st.navigation`: `app.py` arma el menú y el estilo, y cada pantalla vive en `dashboard/paginas/` (`resumen.py`, `detalle.py`). El menú lo dibuja `lateral.py` con `st.page_link` y las pantallas pendientes marcadas "en construcción" | Un solo archivo con un radio para cambiar de pantalla (`app.py` crecería con las 4 pantallas y no habría camino directo desde la tabla) |
| 3 | La fecha viaja en la URL | El enlace de la tabla es un ancla HTML (`target="_self"`) que recarga la página y abre una sesión nueva, que pierde `st.session_state`. Por eso `?fecha=AAAA-MM-DD` y `?parcela=P-SR-1` se leen al arrancar y se escriben de vuelta al cambiar el selector. Una fecha mal escrita o fuera de la temporada vuelve a la noche precargada, y una parcela que no existe, a la de peor estado de la noche | Guardar la fecha solo en la sesión (se pierde con el enlace) |
| 4 | Curva de la noche | **Brote + los dos sensores**, de las 18:00 a las 12:00. Línea gruesa: temperatura estimada en el brote (nodo más frío de cada instante − Δ, con Δ de `configuracion.delta_brote_c`); líneas finas con raya distinta (continua y punteada) para cada sensor; línea de umbral de la etapa; el tramo bajo el umbral se repinta en rojo; franja con el horario de la alerta. Una lectura que falta más de 10 minutos corta la línea (un nodo reporta cada 5), así un corte de reporte no se ve como una recta | Solo el brote (esconde si un nodo falló o discrepa) |
| 5 | Etapa sin umbral | Igual que en el resumen (ADR-018, decisión 4): la parcela no se evalúa, la curva se dibuja sin línea de umbral y la frase lo explica | Usar el último umbral conocido |
| 6 | Humedad y riego | Humedad de suelo promedio por hora de las últimas 24 horas (Q6, con el "ahora" en el cierre de la noche, 12:00) y el umbral de riego del suelo de la finca (ADR-011). Los riegos recientes (hasta 8, antes del cierre de la noche) con inicio, duración, lámina, litros y origen, y una línea con los litros de las últimas 4 semanas (Q7). Las cifras de la noche (mínimas, umbral, horas bajo 0 °C con Q1 y riesgo con Q10) van en una fila de texto, sin tarjetas | Tarjetas con una cifra grande por indicador |
| 7 | Gráficos fijos | Los gráficos (`dashboard/graficos.py`) no se pueden mover: sin arrastre, zoom ni doble clic, con el rango de los ejes calculado una vez. El detalle se lee con el cursor encima (una sola caja con todas las series de ese momento) | Dejar el zoom (en el mapa del resumen deformaba el dibujo; ver ADR-018, decisión 10) |
| 8 | Consultas | Se reutilizan Q1, Q6, Q7, Q9 y Q10 tal cual. Se agrega `db/queries/detalle_parcela.py` con dos consultas de apoyo que **no son Q11**: `curva_de_la_noche` (temperatura por nodo, ordenada por hora) y `riegos_recientes`. Mismo patrón que `resumen_manana.py`: `pipeline_xxx` para el texto de `mongosh` y la función que la ejecuta | Armar la curva desde Q1 (solo da el total de horas bajo cero) |
| 9 | Dónde viven los textos | Las funciones que arman textos y HTML (`dashboard/piezas.py`) y el formato (`dashboard/formato.py`) no usan Streamlit ni MongoDB: reciben lo que arma `data.py` y se prueban solas. Las páginas quedan en presentar. Todo texto que viene de la base pasa por `html.escape` | Funciones dentro de cada página (no se podrían importar sin abrir la pantalla) |

## Consecuencias

- **Faltan 2 pantallas** (alertas y estado de nodos). Cuando existan, se agregan a la lista de `app.py` y a `lateral.PANTALLAS_HECHAS`.
- Al ir al detalle desde el resumen la página se **recarga completa** (un instante). Es el precio de que el enlace sea una fila de la tabla y no un botón de Streamlit.
- La curva usa las lecturas crudas de la noche (216 por nodo): unas 430 por parcela, sin agregar. Es poco, y la consulta usa el índice de la serie temporal (ADR-015).
- La frase "Se regó durante la noche" mira si el último riego empezó dentro de la ventana de 18:00 a 12:00 (la misma regla de ADR-018, decisión 5, **supuesto adoptado**).
- Pruebas: `python -m dashboard.probar_detalle` (53 casos: datos, textos, gráficos y consultas de apoyo) y `python -m dashboard.probar_pantallas` (23 casos de punta a punta con `streamlit.testing`: abre las dos pantallas con las 6 parcelas, parámetros mal escritos, bordes de la temporada y los controles). Verificado en el navegador a 1440 px de ancho. Falta la prueba con el wifi apagado y en pantallas angostas.
