# Pantallas y comportamiento del dashboard

**Estado:** v0.2
Contexto: [`vision.md`](../vision.md), [`requisitos.md`](../requisitos.md) y [ADR-002](../decisions/ADR-002-interfaz-streamlit.md).

---

## 1. Decisiones

| Tema | Decisión |
|---|---|
| Objetivo | Demo vistosa del sistema completo. **Parte obligatoria de la entrega** |
| Plataforma | Web de escritorio, en local. Móvil fuera de alcance |
| Tecnología | Streamlit + Plotly + pymongo |
| Pantallas | Resumen de finca, detalle de parcela, alertas, estado de nodos |
| Estilo | Tema oscuro |
| Noche de helada | **Precargada** en el seed (obligatoria) |
| Simulación en vivo | Opcional; **es lo primero que se recorta** si falta tiempo |
| Mapa | Polígonos esquemáticos de fincas ficticias, sin mapa base |
| Fincas | 3, con un selector de finca en la barra lateral |
| Fecha de referencia | Selector de fecha en la barra lateral: define el "ahora" de las consultas (ADR-004) |
| Observaciones fenológicas | Solo lectura, precargadas en el seed |

## 2. Elementos comunes

- Barra lateral con la navegación entre las 4 pantallas, el **selector de finca** y el **selector de fecha de referencia**.
- Etiqueta visible **"datos simulados"**.
- Panel desplegable **"Ver consulta"** con la consulta de MongoDB que alimenta la pantalla.
- Indicador "último dato hace X min".
- Semáforo con colores consistentes: normal (verde), atención (ámbar), helada (rojo). Verificar el contraste sobre fondo oscuro.
- Tema oscuro: `.streamlit/config.toml` con `base = "dark"` y gráficos Plotly con plantilla oscura y fondo transparente.

## 3. Pantallas

### 3.1 Resumen de finca

| Elemento | Detalle |
|---|---|
| Resumen de las 3 fincas | Tarjetas con el estado general de cada una |
| Mapa | Polígonos de las parcelas de la finca elegida, coloreados por estado, con los nodos como puntos |
| Tarjetas por parcela | Mínima de la noche y estado |
| Alertas activas | Lista corta con parcela, mínima y desde cuándo |
| Consultas | Q2, Q3, Q4 |

### 3.2 Detalle de parcela

| Elemento | Detalle |
|---|---|
| Selector | Elegir parcela |
| Curva de temperatura | La noche, con línea de umbral |
| Humedad de suelo | Serie de las últimas 24 horas |
| Riegos | Últimos eventos |
| Consultas | Q1, Q6, Q7 |

### 3.3 Alertas

| Elemento | Detalle |
|---|---|
| Activas | Parcela, mínima registrada, inicio |
| Historial | Alertas cerradas, con inicio, fin y mínima |
| Resumen | Eventos de helada por departamento y semana |
| Consultas | Q1, Q2, Q8 |

### 3.4 Estado de nodos

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
