# Pantallas y comportamiento del dashboard

**Estado:** v0.6 (22/10/2026). Hechas las 4 pantallas: "Resumen de la mañana" ([ADR-018](../decisions/ADR-018-resumen-de-la-manana.md)), "Detalle de parcela" ([ADR-019](../decisions/ADR-019-detalle-de-parcela.md)), "Alertas" ([ADR-020](../decisions/ADR-020-alertas.md)) y "Estado de nodos" ([ADR-021](../decisions/ADR-021-estado-de-nodos.md)).
Contexto: [`vision.md`](../vision.md), [`requisitos.md`](../requisitos.md) y [ADR-002](../decisions/ADR-002-interfaz-streamlit.md).

---

## 1. Decisiones

| Tema | Decisión |
|---|---|
| Objetivo | Demo vistosa del sistema completo. **Parte obligatoria de la entrega** |
| Plataforma | Web de escritorio, en local. Móvil fuera de alcance |
| Tecnología | Streamlit + Plotly + pymongo |
| Pantallas | Resumen de la mañana, detalle de parcela, alertas y estado de nodos (las 4, hechas) |
| Estilo | Tema oscuro, mundo "Boletín agrometeorológico" (ADR-018): grafito, tinta cálida y color solo para el estado |
| Noche de helada | **Precargada** en el seed (obligatoria) |
| Simulación en vivo | Opcional; **es lo primero que se recorta** si falta tiempo |
| Mapa | Un mapa chico por finca, con polígonos esquemáticos de fincas ficticias, sin mapa base |
| Fincas | 3, con un selector de finca en la barra lateral ("Todas las fincas" por defecto) |
| Fecha de referencia | Selector en la barra lateral: la mañana de la noche que se muestra. El "ahora" de las consultas es el cierre de esa noche, 12:00 hora de Argentina (ADR-004 y ADR-018) |
| Observaciones fenológicas | Solo lectura, precargadas en el seed |

## 2. Elementos comunes

- Barra lateral con la marca "agrosense" (grande, con una barra ámbar), la navegación entre las 4 pantallas (un botón por pantalla, con ícono y separados entre sí; la actual lleva borde ámbar y letra más gruesa), el selector de la pantalla (**finca** en el resumen, **parcela** en el detalle), el **selector de fecha** y un botón por cada mañana con alerta de helada. La fecha y la parcela viajan también en la URL (`?fecha=2026-10-05&parcela=P-SR-1`).
- Etiqueta visible **"datos simulados"**.
- Panel desplegable **"Ver consulta"** con las consultas de MongoDB que alimentan la pantalla, escritas para `mongosh`.
- Indicador "último dato" y cantidad de nodos que reportan.
- Semáforo con colores consistentes: normal (verde), atención (ámbar), helada (rojo), sin umbral (gris). **El estado nunca va solo en color**: cada uno lleva una forma (círculo, triángulo, rombo, guion) y una palabra.
- Tema oscuro: `.streamlit/config.toml` con `base = "dark"`, estilo propio en `dashboard/estilo.py` y gráficos Plotly con fondo transparente. Sin dependencias de internet.

## 3. Pantallas

### 3.1 Resumen de la mañana (hecha)

Para el encargado de finca que abre el panel después de una noche fría. Responde: qué se heló, cuánto bajó, desde cuándo y si ya se regó. La noche va de las 18:00 del día anterior a las 12:00 de la mañana elegida, hora de Argentina.

| Elemento | Detalle |
|---|---|
| Frase de estado | Una oración con la respuesta ("2 de 4 parcelas bajaron de su umbral de helada") y el detalle de la peor parcela y si se regó. A la derecha, nodos que reportan y hora del último dato |
| Tabla de la noche (protagonista) | Una fila por parcela, ordenada por gravedad: estado, parcela y finca, etapa, mínima en el brote contra umbral, **barra de tiempo** de 18:00 a 12:00 con la alerta en rojo, duración, riesgo (con agravantes) y riego |
| Mapa | Un mapa chico por finca (las de peor estado primero): parcelas coloreadas por estado y nodos como puntos (hueco si no reportan) |
| Ver consulta | Q10, alertas de helada, último riego y Q5 |
| Consultas | Q10, Q9 y Q5, más las de apoyo de `db/queries/resumen_manana.py` |
| Estados | Con helada, solo atención, sin helada, sin umbral en la etapa (no se evalúa), nodos sin reportar, sin lecturas en las últimas horas, alerta en curso al cierre |

### 3.2 Detalle de parcela (hecha)

Para el técnico agrónomo, o para quien llega desde una fila del resumen. Responde: ¿por qué saltó la alerta? Se entra con un clic en el nombre de la parcela de la tabla del resumen o eligiéndola en la barra lateral (arranca en la de peor estado de la noche).

| Elemento | Detalle |
|---|---|
| Frase de estado | Una oración con lo que pasó ("Cuartel 1 bajó a −8,3 °C en el brote, 4,4 °C bajo su umbral") y el detalle: horario y duración de la alerta, riesgo y si se regó. A la derecha, el estado con su forma y su palabra |
| Curva de la noche (protagonista) | De 18:00 a 12:00: temperatura del brote (línea gruesa), los 2 sensores (líneas finas con raya distinta), línea del umbral de la etapa, tramo bajo el umbral en rojo y franja de la alerta. Un corte de reporte se ve como corte. Fija: sin zoom ni arrastre |
| Cifras | Mínima en el brote, umbral, mínima del sensor, horas bajo 0 °C y riesgo, en una fila de texto |
| Humedad de suelo | Promedio por hora de las últimas 24 horas con el umbral de riego del suelo |
| Riegos recientes | Hasta 8, con inicio, duración, lámina, litros y origen; los de esta noche resaltados; litros de las últimas 4 semanas |
| Ver consulta | Curva, Q1, Q6, riegos, Q7, alertas y Q10 |
| Consultas | Q1, Q6, Q7, Q9 y Q10, más las de apoyo de `db/queries/detalle_parcela.py` |
| Estados | Con helada (con o sin alerta registrada), solo atención, sin helada, sin umbral en la etapa (la curva se dibuja sin línea de umbral), nodo en mantenimiento o sin lecturas (aviso), sin lecturas en la noche, sin riegos |

### 3.3 Alertas (hecha)

Para el encargado o el técnico después de ver el resumen. Responde: ¿qué alertas hubo en esta noche y cómo viene la temporada? Las "activas" son las de la noche elegida (de las 18:00 a las 12:00), abiertas o cerradas: en la base todas cierran antes del mediodía.

| Elemento | Detalle |
|---|---|
| Control de tipo | Todas, Helada o Riego: filtra la lista de la noche y el historial. El resumen semanal es siempre de helada. Hay además un filtro de finca en la barra lateral |
| Frase de estado | Una oración con cuántas alertas hubo y en qué finca ("2 alertas de helada esta noche, en Finca Los Álamos (San Rafael)"), y el detalle de la más fuerte. A la derecha, las alertas de la temporada hasta esa fecha |
| Alertas de la noche (protagonista) | Una fila por alerta, la más grave primero: tipo, parcela (enlace al detalle), etapa, valor extremo contra umbral (°C del brote o % de humedad de suelo), barra de tiempo de 18:00 a 12:00 (roja en helada, ámbar en riego), duración y riesgo |
| Historial de la temporada | Tabla ordenable con las alertas hasta el cierre de la noche elegida: tipo, parcela, etapa, inicio, fin, duración, valor extremo, umbral y estado |
| Heladas por departamento y semana | Tabla semana × departamento con la cantidad de alertas y la mínima del brote (Q8, toda la temporada); la semana elegida va resaltada |
| Ver consulta | Alertas de la noche, historial y Q8 |
| Consultas | Q8, más las de apoyo de `db/queries/alertas_pantalla.py` |
| Estados | Noche sin alertas, filtro sin resultados, alerta en curso al cierre, historial vacío (antes de la primera alerta), noche con solo riego |

### 3.4 Estado de nodos (hecha)

Para el administrador, el técnico o el encargado que duda de un dato. Responde: ¿están reportando todos los sensores, cuál no y desde cuándo? El "ahora" es el cierre de la noche elegida (12:00): casi siempre los 12 nodos reportan, y hay nodos sin reportar en 17 días de la temporada (3/12, 2/3 y del 17/3 en adelante).

| Elemento | Detalle |
|---|---|
| Frase de estado | "Los 12 nodos reportan." o "1 de 12 nodos sin reportar: N-TU-2-B.", con cuánto lleva sin datos y cuándo fue su último reporte. A la derecha, el último dato de la red |
| Tabla de nodos (protagonista) | Una fila por nodo: reporte (círculo verde o triángulo ámbar, con la palabra), nodo, parcela (enlace al detalle), último reporte, hace cuánto y estado del nodo. Los que no reportan van primero y resaltados |
| Dos estados | "Reporte" se calcula (más de 30 minutos sin lecturas = sin reportar). "Estado del nodo" es el del catálogo (activo, mantenimiento o baja). Si se contradicen, la celda lo aclara ("sigue reportando", "activo, pero no reporta") |
| Ver consulta | Último reporte de cada nodo y Q5 |
| Consultas | Q5, más la de apoyo de `db/queries/estado_nodos.py` |
| Estados | Todos reportan, uno o varios sin reportar, un nodo sin ninguna lectura, mantenimiento que sigue reportando, activo que dejó de reportar, filtro de finca (4 nodos por finca) |

## 4. Noche precargada (obligatoria)

El seed incluye una noche de helada con alertas en las fincas. El dashboard la muestra desde el primer arranque, sin depender de ninguna simulación. Es también el respaldo para la defensa.

## 5. Simulación en vivo (opcional)

Solo se implementa si los demás elementos están cerrados.

1. El botón **"Simular noche de helada"** genera lecturas en pasos de una hora simulada (de 20:00 a 08:00, unos 13 pasos de 2 a 3 segundos, unos 30 segundos en total).
2. En cada paso **inserta las lecturas en MongoDB** y **ejecuta la regla de alerta de helada**.
3. Actualiza el mapa, la curva y las alertas. La alerta debe aparecer porque la base reaccionó a los datos, no porque la pantalla la dibuje.
4. Cada ejecución varía dentro de rangos acotados (a definir) y acepta una **semilla** opcional para repetir la misma noche. Acotar el rango para que al menos una parcela entre en alerta, o aclararlo en pantalla.
5. Las lecturas y alertas generadas llevan `escenario_id`, y el botón **"Reiniciar demo"** las borra.

**Verificar antes de implementar** el comportamiento del bucle de reproducción con la versión instalada de Streamlit, incluyendo qué pasa si se toca otro control durante la reproducción.

## 6. Impacto en otros componentes

| Componente | Cambio |
|---|---|
| `dashboard/data.py` | Consultas de lectura. Si se implementa RF-14, también funciones de escritura |
| `simulator/` | Funciones importables (generar el paso de una noche), no solo un script |
| `docs/modelo-datos.md` | Campos `fuente` y `escenario_id` |
| Regla de alerta | Función invocable por paso (RF-04) |
