# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Sin publicar]

### Agregado
- Estructura inicial del repositorio y documentación base.
- Informes de investigación en `docs/investigacion/`: contexto del problema, fuentes de datos, dos informes de parámetros del Malbec y `verificacion-fuentes.md`, con los datos confirmados en las fuentes originales (SMN, INV, WSU, FAUBA, FDF, Morábito, Zapata 2017).
- ADR-003: decisiones iniciales de modelado (alertas con referencias, contenido de `lecturas.meta`, alerta de riego por humedad de suelo).
- ADR-004: temporada de Malbec, etapa fenológica BBCH estimada por grados-día y corregida con observaciones, índice de riesgo de helada, selector de fecha de referencia.
- ADR-005: temperatura estimada en el brote, umbrales de helada de vid por etapa, índice de riesgo con agravantes, riego y suelo por finca.
- Consultas Q9 (etapa por grados-día) y Q10 (índice de riesgo), y requisitos RF-16 a RF-20.
- `install.sh` y `requirements.txt` para crear el entorno de Python (`pymongo`, `streamlit`, `plotly`, versiones fijas).
- Spike de series temporales en MongoDB 9.0.2: scripts en `scripts/spike-adr001/` y conclusiones en `docs/spikes/`.
- Secciones "Cómo se probó" y "Conclusión" en la plantilla de spike.
- Modelo de datos v1.0 (`docs/modelo-datos.md`): campos, tipos, relaciones, índices propuestos y ejemplos de las 10 colecciones, con la colección de configuración `configuracion`. ADR-006 con las decisiones de detalle (IDs legibles, etapas embebidas, validación estricta, entre otras).
- ADR-007: `lecturas` (serie temporal) no admite validador en MongoDB 9.0.2; se protege con validación en el simulador y con una consulta de auditoría.
- ADR-008: los esquemas, la creación de colecciones, la validación previa y la auditoría se escriben en Python (`pymongo`).
- Paquete `db`: esquemas `$jsonSchema` de las 10 colecciones (`db/schemas/`), conexión configurable con `AGROSENSE_URI` y `AGROSENSE_BD`, creación de colecciones repetible sin perder datos, validación de lecturas sin guardar (`$documents` + `$jsonSchema`), auditoría de lecturas y prueba de 62 casos. Documentado en `docs/esquemas-validacion.md`.
- Spike de esquemas de validación (4 pruebas): esquema cerrado, validador en series temporales, auditoría con `$nor` y validación desde Python.
- ADR-009: límite de temperatura "sospechosa" por departamento (`configuracion.sospechoso_minimo_c`: San Rafael −4,5 °C y San Martín −2,8 °C, récord de septiembre del SMN; Tupungato `null`, resuelto después en ADR-012) y noche extrema declarada en `configuracion.noche_extrema` (San Rafael, primera semana de octubre, piso −6,3 °C supuesto). El límite es techo de generación del simulador y aviso de auditoría; no rechaza ni excluye lecturas.
- Auditoría de lecturas con tres conteos (mal formadas, sospechosas esperadas e inesperadas) que aprueba con dos ceros y termina con código 1 si falla; `configuracion.verificar_coherencia()` con las reglas que el esquema no puede expresar; `db/departamentos.py`. La prueba pasó a 62 casos.
- Seed base (`db/seeds/`, `python -m db.seeds.cargar`): 3 fincas, 6 parcelas, 12 nodos con geometrías ficticias, la variedad Malbec con 13 etapas BBCH continuas, la configuración y el evento de la noche extrema. Repetible, valida antes de escribir y comprueba la geografía. ADR-010 y `docs/seed.md`.
- Umbrales de riego calculados con la Tabla 19 de la FAO-56 (franco 19,2 %, franco arenoso 17,6 %, pedregoso 7,8 %). ADR-011.
- ADR-012: cierre de supuestos. `CLAUDE.md` define dos marcas, "con fuente" y "supuesto adoptado", y desaparece "a validar". Tupungato pasa a −5,6 °C como límite de temperatura sospechosa.
- Simulador de la temporada (`simulator/`, `python -m simulator.generar`): 727.980 lecturas, 10 alertas de helada (5 noches × 2 parcelas), 25 de riego, 563 riegos y 42 observaciones fenológicas, con la auditoría en 0 y 0. Pruebas de 51 casos (`python -m simulator.probar_simulador`). ADR-013 y `docs/simulador.md`.
- `numpy==2.5.4` en `requirements.txt`.
- Consultas Q1 a Q10 en Python con `pymongo` (`db/queries/q1_horas_bajo_cero.py` a `q10_riesgo_de_helada.py`): cada una con `pipeline()`, `consultar()` y consola con `--mongosh`; piezas comunes en `db/queries/comun.py`. Explicadas etapa por etapa, con sus resultados reales, en `docs/consultas.md`. ADR-014.
- `db/indexes/crear_indices.py`: índices `2dsphere` de `nodos.ubicacion` (Q3 no funciona sin él), `parcelas.geometria` y `eventos_climaticos.area`.
- Índices de rendimiento (`db/indexes/crear_indices.py`): `lecturas {meta.nodo_id, ts}` (Q5: 5.053 → 433 documentos examinados), `riegos {parcela_id, inicio}` (Q7: 563 → 33), `alertas {tipo, inicio}` (Q8) y `observaciones_fenologicas {parcela_id, fecha}` (Q9). `medir_indices.py` mide las 10 consultas antes y después con el perfilador de MongoDB (plan, documentos y claves examinados, tiempo), con un experimento sobre el índice automático de `lecturas` y el tamaño de cada índice; `probar_indices.py` (19 casos) comprueba que se usan y que no cambian ninguna respuesta. Resultados en `docs/performance.md`. ADR-015.
- `db.queries.probar_consultas`: 43 casos que comparan cada consulta con un cálculo independiente, y el texto de `mongosh` de Q1, Q4 y Q7 con el resultado de Python.
- Pasos para ejecutar el proyecto en el README y estado actual en `CLAUDE.md`.

### Cambiado
- Regla permanente en `CLAUDE.md`: `CLAUDE.md`, `README.md` y `CHANGELOG.md` se actualizan en el mismo cambio.
- Umbrales de riego: los valores anteriores (21 y 13,5 %) no salían de la FAO-56 y se reemplazaron (ADR-011).
- San Rafael brota ~30/9 con la regla de Q9, no ~1/10 (ADR-013).
- Índices propuestos en `docs/modelo-datos.md` corregidos con las mediciones: `alertas {tipo, inicio}` en lugar de `{parcela_id, inicio}` y `{estado, tipo}` (ninguna consulta filtra por `estado`), y se agrega el de `lecturas` para Q5 (ADR-015). El criterio de aceptación de mediciones queda cumplido.
- Q5 documentaba que usaba el índice automático de la serie temporal; no era cierto (examinaba 5.053 documentos). Corregido en `q5_nodos_sin_reportar.py`.
- Las consultas Q1 a Q10 pasan de `mongosh` a Python (ADR-014, reemplaza una frase de ADR-008); `dashboard/data.py` las llama en lugar de reescribirlas (ajuste a ADR-002). La helada (Q2 y Q10) usa la etapa estimada y no la observada, igual que las alertas (excepción a ADR-004).
- Alcance: de 30 días sin variedad definida a una temporada de Malbec (1/9/2026 a 31/3/2027, unas 732.700 lecturas).
- Umbrales de helada: valores de vid por etapa BBCH en lugar de los de frutales (IDR + DACC).
- `lecturas` como serie temporal, confirmada como decisión firme (ADR-001).
- `eventos_climaticos` como colección común, porque el índice `2dsphere` de las series temporales solo acepta puntos.
- Q3 (nodos más cercanos) se resuelve con `$geoNear` sobre la colección `nodos`.
- `escenario_id` va dentro de `lecturas.meta`, para que "Reiniciar demo" pueda borrar las lecturas de la simulación en vivo.
- `CLAUDE.md` actualizado con las decisiones de las ADR y del spike.
- Los scripts de los spikes pasaron de `mongosh` a Python, con resultados idénticos.
- `eventos_climaticos.tipo` solo admite `"helada"`: el granizo queda fuera del modelo porque ningún sensor del MVP lo mide (ADR-006, decisión 12).

### Corregido
- Ejemplo de `variedades` en `modelo-datos.md`: la etapa "Floración y cuaje" lleva 260 grados-día desde la brotación (Zapata 2017), no 230.
- Mínimas récord de septiembre del SMN (San Rafael −4,5 °C y San Martín −2,8 °C) y altura de la estación San Martín (653 m), que venían mal de una fuente secundaria.
- Fin de línea LF en los scripts `.sh` (`.gitattributes`), para que funcionen al clonar en Windows.
