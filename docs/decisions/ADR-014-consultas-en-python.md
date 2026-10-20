# ADR-014: Consultas Q1 a Q10 en Python y reglas comunes

**Estado:** Aceptado (20/10/2026). Reemplaza la frase de [ADR-008](ADR-008-esquemas-en-python.md) "Las consultas Q1 a Q10 siguen en `mongosh`". Detalle de cada consulta en [`consultas.md`](../consultas.md).

## Contexto

`CLAUDE.md` y ADR-008 dejaban Q1 a Q10 como scripts de `mongosh` (`db/queries/qN_nombre.js`). El resto del proyecto (esquemas, seed, simulador, auditoría) ya está en Python con `pymongo`, y el dashboard también lo va a estar. Además, había que decidir varias reglas que las consultas comparten.

## Decisiones

| # | Tema | Decisión | Descartadas |
|---|---|---|---|
| 1 | Lenguaje | **Python con `pymongo`**: un módulo por consulta (`db/queries/qN_nombre.py`) con `pipeline()`, `consultar(bd, ...)` y `main()` | Scripts de `mongosh` (dos lenguajes; el dashboard tendría que reescribirlas) |
| 2 | Práctica con `mongosh` | Cada consulta imprime su versión de `mongosh` con `--mongosh` (`comun.texto_mongosh`), y la prueba comprueba que Q1, Q4 y Q7 den lo mismo en `mongosh` | Escribir las consultas dos veces a mano (se desincronizan) |
| 3 | Una noche | De las 18:00 del día anterior a las 12:00 de la mañana `D`, hora de Argentina | Día calendario (partiría la helada a la medianoche) |
| 4 | "Ahora" | Parámetro; por defecto `2026-10-05T09:30Z` (ADR-012). Q6 usa las 24 horas completas anteriores a la hora en curso | Ventana de 24 h exactas (daría 25 filas con dos extremos incompletos) |
| 5 | Semana | Lunes a domingo, hora de Argentina | Semana ISO en UTC |
| 6 | Temperatura de una parcela | La del nodo más frío en cada instante; brote = esa temperatura − Δ | Promedio de los nodos (no coincidiría con las alertas) |
| 7 | Etapa para helada | **Estimada** por grados-día en Q2 y Q10, como las alertas guardadas. Q9 informa también la observada y la efectiva (la observada si existe). **Excepción a ADR-004** | Etapa efectiva en Q2 y Q10: las observaciones son mensuales y la etapa quedaría congelada hasta 30 días; Q10 contradiría a las alertas (San Martín el 29/9 daría "bajo" con una alerta "alto") |
| 8 | Humedad del aire en Q10 | Promedio de 22:00 a 08:00 (hora local) | Toda la ventana: incluye la mañana, con aire seco, y subía a "medio" noches sin frío |
| 9 | Horas bajo cero (Q1) | `$setWindowFields` con `$integral` de un indicador; cada lectura bajo cero aporta 5 minutos | Contar lecturas en Python (saca la lógica de la base) |
| 10 | Eventos de helada (Q8) | Una alerta de helada es un evento; se informan también las parcelas afectadas | Contar noches distintas (pierde cuántas parcelas) |
| 11 | Índices | Solo `2dsphere` en `nodos.ubicacion` (Q3 no funciona sin él), `parcelas.geometria` y `eventos_climaticos.area`, con `db/indexes/crear_indices.py`. Los de rendimiento quedan para medir antes y después | Crear todos los índices ya (no habría "antes" para medir, RNF-01) |
| 12 | Dashboard | `dashboard/data.py` importa `consultar()` de `db/queries` y les agrega `st.cache_data`; el panel "Ver consulta" muestra `texto_mongosh`. Ajusta ADR-002 | Reescribir cada consulta en `data.py` |

## Consecuencias

- Q2 y Q10 llaman primero a Q9 (6 filas) y usan su resultado como umbral en la segunda tubería, con `$getField` sobre un diccionario. Por eso su texto de `mongosh` incluye esos valores ya resueltos.
- **Limitación de Q10 (regla de ADR-005 al pie de la letra):** una noche muy cálida y muy seca puede subir a "medio" por "aire seco" aunque no haya frío. El dashboard puede mostrarlo solo para noches con frío o con alerta.
- Si el clima del simulador cambia, cambian las etapas; `probar_consultas.py` compara Q9 con el escenario del simulador y lo detecta.
- `CLAUDE.md` (sección 7), `architecture.md` y las notas de ADR-002 y ADR-008 quedan corregidos.
