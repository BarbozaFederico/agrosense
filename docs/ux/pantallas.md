# Pantallas y comportamiento del dashboard

**Estado:** v0.3 (21/10/2026). La primera pantalla está construida: "Resumen de la mañana" ([ADR-018](../decisions/ADR-018-resumen-de-la-manana.md)). Las otras tres están pendientes.
Contexto: [`vision.md`](../vision.md), [`requisitos.md`](../requisitos.md) y [ADR-002](../decisions/ADR-002-interfaz-streamlit.md).

---

## 1. Decisiones

| Tema | Decisión |
|---|---|
| Objetivo | Demo vistosa del sistema completo. **Parte obligatoria de la entrega** |
| Plataforma | Web de escritorio, en local. Móvil fuera de alcance |
| Tecnología | Streamlit + Plotly + pymongo |
| Pantallas | Resumen de la mañana (hecha), detalle de parcela, alertas, estado de nodos (pendientes) |
| Estilo | Tema oscuro, mundo "Boletín agrometeorológico" (ADR-018): grafito, tinta cálida y color solo para el estado |
| Noche de helada | **Precargada** en el seed (obligatoria) |
| Simulación en vivo | Opcional; **es lo primero que se recorta** si falta tiempo |
| Mapa | Un mapa chico por finca, con polígonos esquemáticos de fincas ficticias, sin mapa base |
| Fincas | 3, con un selector de finca en la barra lateral ("Todas las fincas" por defecto) |
| Fecha de referencia | Selector en la barra lateral: la mañana de la noche que se muestra. El "ahora" de las consultas es el cierre de esa noche, 12:00 hora de Argentina (ADR-004 y ADR-018) |
| Observaciones fenológicas | Solo lectura, precargadas en el seed |

## 2. Elementos comunes

- Barra lateral con la navegación entre las 4 pantallas (las pendientes figuran "en construcción"), el **selector de finca**, el **selector de fecha** y un botón por cada mañana con alerta de helada.
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

### 3.2 Detalle de parcela (pendiente)

| Elemento | Detalle |
|---|---|
| Selector | Elegir parcela |
| Curva de temperatura | La noche, con línea de umbral |
| Humedad de suelo | Serie de las últimas 24 horas |
| Riegos | Últimos eventos |
| Consultas | Q1, Q6, Q7 |

### 3.3 Alertas (pendiente)

| Elemento | Detalle |
|---|---|
| Activas | Parcela, mínima registrada, inicio |
| Historial | Alertas cerradas, con inicio, fin y mínima |
| Resumen | Eventos de helada por departamento y semana |
| Consultas | Q1, Q2, Q8 |

### 3.4 Estado de nodos (pendiente)

| Elemento | Detalle |
|---|---|
| Lista | Nodo, parcela, último reporte y estado |
| Inactivos | Resaltados (sin reportar hace más de 30 minutos) |
| Consultas | Q5 |

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
