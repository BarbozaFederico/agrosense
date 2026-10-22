# CLAUDE.md — agrosense

Contexto para trabajar en este repositorio con Claude Code. Leer completo antes de actuar.

## 1. Qué es este proyecto

**agrosense** es un proyecto de la materia *Diseño de Bases de Datos II* (Universidad de Mendoza, 2026), desarrollado por un **equipo de dos personas**. Implementa una base de datos **MongoDB** para monitorear sensores en viñedos: temperatura, humedad de suelo y de aire, alerta de heladas y riego, con un dashboard web.

- Repo: https://github.com/BarbozaFederico/agrosense (**público**).
- Entrega: **miércoles 28 de octubre de 2026**.
- El foco es la **base de datos**. La materia evalúa: requisitos, modelado documental, implementación, carga de datos, consultas avanzadas, índices con medición de rendimiento y política de resguardo (backup).
- La evaluación es **individual**: cada integrante debe poder explicar y defender cada decisión y cada línea.

## 2. Cómo trabajar con el equipo (importante)

- Son estudiantes de 3er año y **están aprendiendo MongoDB** (conocen la teoría, no la práctica). Explicá brevemente el porqué de cada comando o decisión antes de ejecutarlo.
- Pasos chicos y verificables. Un cambio, una explicación, un commit.
- No agregues funcionalidades fuera del alcance (sección 4) sin consultarlo.
- Antes de decisiones de diseño relevantes (qué embeber, qué referenciar, qué índices), presentá 2 opciones con ventajas y desventajas y esperá la elección. Registrá la decisión en `docs/decisions/`.
- No asumas el sistema operativo ni cómo se instaló MongoDB: verificalo (`mongosh --version`, `mongosh --eval "db.version()"`).
- Idioma: **español** para documentación, comentarios, commits y explicaciones. Identificadores y nombres de colecciones y campos en español, `snake_case`, sin tildes ni eñes (`viñedo` → `vinedo`).
- No inventes datos ni cifras. Todo dato lleva una de dos marcas: **con fuente** (con la cita) o **supuesto adoptado** (decisión del equipo por falta de datos o de tiempo, registrada en un ADR; ver ADR-012). No dejes datos "a validar": si no hay fuente, se propone una opción y se adopta.
- **Repo público:** nunca subas credenciales, cadenas de conexión con contraseña, `.env`, backups ni datos personales.
- **Mantené la documentación al día, siempre, en el mismo cambio** (regla permanente): `CLAUDE.md` (tabla de ADR, estructura del repo, entorno, reglas de dominio y estado actual), `README.md` (índice de ADR y "Cómo ejecutarlo") y `CHANGELOG.md`. Si agregás un ADR, un módulo, un comando o un dato de configuración, actualizá esos archivos antes de pedir el commit. Si ves que alguno quedó atrasado, avisalo y corregilo.

## 3. Documentos del repo

Ver `README.md` para el índice. Los más importantes: `docs/vision.md`, `docs/requisitos.md`, `docs/roadmap.md`, `docs/architecture.md`, `docs/ux/pantallas.md`, `docs/equipo.md`.

Investigación en `docs/investigacion/`: contexto, fuentes de datos, dos informes del Malbec y `verificacion-fuentes.md` (prevalece sobre los informes). Decisiones en `docs/decisions/` (ADR-001 a ADR-016 y ADR-018 a ADR-021; el ADR-017, roles y autenticación, está reservado). Consultas explicadas en `docs/consultas.md`, mediciones de índices en `docs/performance.md` y backup en `docs/backup-restore.md`.

## 4. Alcance del MVP

- **3 fincas ficticias en 3 departamentos de Mendoza, 6 parcelas (2 por finca), 12 nodos (2 por parcela)**, 3 variables (temperatura, humedad de suelo, humedad de aire), 2 tipos de alerta (helada y riego).
- Variedad: **Malbec** en las 6 parcelas; una "variedad simulada X" es opcional al final (ADR-004).
- Colecciones: `fincas`, `parcelas`, `nodos`, `lecturas`, `alertas`, `riegos`, `eventos_climaticos`, `observaciones_fenologicas` y las colecciones de configuración `variedades` y `configuracion` (ADR-003, ADR-004 y ADR-006). Campos, tipos y relaciones en `docs/modelo-datos.md`.
- Temporada simulada: 1/9/2026 a 31/3/2027, 1 lectura cada 5 minutos por nodo, 727.980 lecturas (12 × 61.056 = 732.672, menos los cortes de reporte y un nodo en mantenimiento); 8 noches de helada entre septiembre y octubre (San Rafael 3, San Martín 2, Tupungato 3), 5 con alerta.
- **Dashboard web de escritorio con Streamlit: obligatorio.** 4 pantallas, tema oscuro, noche de helada precargada.
- **Opcional (primero que se recorta):** simulación de la noche en vivo desde el dashboard (RF-14 y RF-15).
- **Fuera de alcance:** siniestros, seguros, contratistas, cosechas, costos, hidrología, estaciones reales, versión móvil, alerta temprana y pronóstico climático, Docker y Atlas. Descartados en ADR-004: variable de altura y daño en porcentaje por etapa.

## 5. Decisiones técnicas acordadas

| Tema | Decisión |
|---|---|
| Motor | MongoDB Community Server (verificar la versión instalada antes de usar funciones nuevas) |
| Consola y GUI | `mongosh` y MongoDB Compass |
| Lecturas | Serie temporal (`timeField: ts`, `metaField: meta`). Decisión firme, ver ADR-001 |
| Geoespacial | GeoJSON + índices `2dsphere` |
| Validación | `$jsonSchema` en las colecciones comunes (esquema cerrado, con `_id` declarado). `lecturas` se valida en el simulador y con una consulta de auditoría. Esquemas en Python (`db/schemas/`). Ver ADR-007, ADR-008 y `docs/esquemas-validacion.md` |
| Simulador | Python + `pymongo`, en `simulator/`, con funciones importables |
| Backup | `mongodump` y `mongorestore` (Database Tools), con scripts de Python en `scripts/backup_restore/` (`backup`, `restaurar`, `probar_respaldo`). Un archivo `.archive.gz` por backup con su manifiesto (sha256 y resumen de cada colección), siempre fuera del repo; política de 7 diarios y 4 semanales (supuesto adoptado); se restaura en una base aparte. Ver ADR-016 y `docs/backup-restore.md` |
| Consultas | Q1 a Q10 en Python con `pymongo` (`db/queries/qN_nombre.py`); cada una puede mostrar su versión de `mongosh` con `--mongosh`. Ver ADR-014 y `docs/consultas.md` |
| Índices | 3 `2dsphere` (Q3 y Q4) y 4 de rendimiento medidos con el perfilador (Q5, Q7, Q8 y Q9), en `db/indexes/`; `lecturas` conserva el automático de la serie temporal. Ver ADR-015 y `docs/performance.md` |
| Interfaz | Streamlit + Plotly, web de escritorio; las consultas viven en `db/queries/` y `dashboard/data.py` las llama y cachea. Ver ADR-002 y ADR-014 |
| Móvil | Fuera de alcance |
| Licencia | MIT |

Verificado en MongoDB 9.0.2 ([spike del 14/10/2026](docs/spikes/spike-adr001-series-temporales.md) y spike de esquemas del 15/10/2026):

- En series temporales **se puede borrar con cualquier filtro**, pero **solo se actualizan campos de `meta`** (con `updateMany`). Las lecturas no se corrigen: se borran y se vuelven a insertar.
- Las series temporales **no admiten validador** (`$jsonSchema`), ni al crearlas ni con `collMod`; el mismo esquema sí funciona como filtro de búsqueda ([spike de esquemas del 15/10/2026](docs/spikes/spike-esquemas-validacion.md)).
- El índice `2dsphere` en series temporales **solo acepta puntos**. Por eso `eventos_climaticos` (polígonos) es una **colección común**, y la ubicación vive en `nodos` y `parcelas` (colecciones comunes), no en cada lectura.

### Decisiones registradas (ADR)

| ADR | Decisión |
|---|---|
| ADR-001 | `lecturas` es una colección de series temporales (`timeField: ts`, `metaField: meta`); verificado con el spike del 14/10/2026 |
| ADR-002 | Dashboard con Streamlit + Plotly; `dashboard/data.py` llama a las consultas de `db/queries` (ajustado por ADR-014) |
| ADR-003 | `alertas` guarda solo referencias (`parcela_id`): el departamento se obtiene con `$lookup` alertas → parcelas → fincas (Q8). `lecturas.meta` lleva `nodo_id`, `parcela_id` y `finca_id`. La alerta de riego se dispara por umbral de humedad de suelo |
| ADR-004 | Malbec, temporada 1/9/2026 a 31/3/2027, etapa BBCH combinada (grados-día + observaciones), índice de riesgo, riego mixto, selector de fecha de referencia, observaciones solo en el seed |
| ADR-005 | Temperatura del brote (sensor − 2 °C), umbrales de vid por etapa, índice de riesgo con agravantes, riego y suelo por finca |
| ADR-006 | IDs legibles (`F-SR`, `P-SR-1`, `N-SR-1-A`), etapas embebidas en `variedades`, colección `configuracion`, alerta abierta con `fin: null`, etapa calculada (no guardada), riesgo guardado al cerrar la alerta, riegos en mm y litros, campos con unidad (`temperatura_c`), validación estricta (`error` y esquema cerrado) |
| ADR-007 | `lecturas` no admite validador: se valida en el simulador y con una consulta de auditoría (`$nor` + `$jsonSchema`) |
| ADR-008 | Esquemas, creación de colecciones, validación previa (`$documents` + `$jsonSchema`) y auditoría en Python (`pymongo`), paquete `db`. Las consultas Q1 a Q10 también van en Python desde ADR-014 |
| ADR-009 | Límite de temperatura "sospechosa" por departamento (techo de generación del simulador y aviso de auditoría, sin rechazar ni excluir), noche extrema declarada en `configuracion.noche_extrema` (solo San Rafael, primera semana de octubre, piso −6,3 °C supuesto), y auditoría de dos ceros (mal formadas e inesperadas) |
| ADR-010 | Seed base en `db/seeds/`: cargador único repetible, geometrías ficticias (rectángulos de 2 ha), etapas BBCH continuas de 0 a 99 con corte a la mitad entre yema dormida e hinchada |
| ADR-011 | Umbrales de riego con la FAO-56 (`θFC − p × (θFC − θWP)`, p = 0,45, punto medio de la Tabla 19): franco 19,2 %, franco arenoso 17,6 %, pedregoso 7,8 % (loamy sand con 30 % de gravas, supuesto) |
| ADR-012 | Cierre de supuestos: dos marcas, **con fuente** y **supuesto adoptado** (desaparece "a validar"); Tupungato −5,6 °C; parámetros del simulador |
| ADR-013 | Diseño del simulador: noche extrema de ~7 h bajo cero, calendario de heladas según la etapa, 10 alertas de helada (5 noches × 2 parcelas), cierres con 1 h de histéresis, regla de grados-día de Q9 |
| ADR-014 | Consultas Q1 a Q10 en Python con `pymongo` (no en `mongosh`); una noche va de las 18:00 a las 12:00 hora de Argentina; semana de lunes a domingo; la helada (Q2 y Q10) usa la etapa estimada, no la observada; índices `2dsphere` de `nodos`, `parcelas` y `eventos_climaticos` |
| ADR-015 | Índices de rendimiento: `lecturas {meta.nodo_id, ts}` (Q5: 5.053 → 433 documentos examinados), `riegos {parcela_id, inicio}` (Q7), `alertas {tipo, inicio}` (Q8) y `observaciones_fenologicas {parcela_id, fecha}` (Q9); se miden las 10 consultas con el perfilador (la mejora está en documentos examinados, no en tiempo) y `meta_1_ts_1` se deja |
| ADR-016 | Backup con `mongodump --archive --gzip` de la base `agrosense` y restauración con `mongorestore` a una base aparte, en `scripts/backup_restore/` (Python); manifiesto con sha256; respaldos fuera del repo; política de 7 diarios y 4 semanales (supuesto adoptado); la serie temporal `lecturas` se restaura bien (727.980 lecturas) |
| ADR-018 | Primera pantalla del dashboard, "Resumen de la mañana": frase de estado, tabla de la noche con barra de tiempo (18:00 a 12:00), mundo "Boletín agrometeorológico" (grafito, color solo para el estado), "ya se regó" = último riego (supuesto adoptado), "ahora" = 12:00 de la mañana elegida, consultas de apoyo en `db/queries/resumen_manana.py` |

### Entorno

- MongoDB Server 9.0 instalado como servicio de Windows. `mongosh` y MongoDB Database Tools se instalan aparte y deben estar en el PATH.
- Los scripts de `db/` se corren desde la raíz con `python -m`, por ejemplo `python -m db.schemas.crear_colecciones`. La base se elige con `AGROSENSE_BD` (por defecto `agrosense`; las pruebas usan `agrosense_tests`).
- Dependencias de Python en `requirements.txt` (raíz, versiones fijas). `install.sh` crea `.venv` e instala todo: en PowerShell se ejecuta con `bash install.sh`.
- Para reconstruir los datos: `python -m db.seeds.cargar` (fincas, parcelas, nodos y configuración) y después `python -m simulator.generar` (la temporada, ~25 s). Índices (después de `simulator.generar`; Q3 no funciona sin los geoespaciales): `python -m db.indexes.crear_indices`. Mediciones antes y después: `python -m db.indexes.medir_indices` (usa `agrosense_tests`). Consultas: `python -m db.queries.q9_etapa_por_grados_dia --fecha 2026-10-05` (cada `qN_nombre` acepta `--help` y `--mongosh`). Pruebas: `python -m db.schemas.probar_esquemas`, `python -m simulator.probar_simulador`, `python -m db.queries.probar_consultas` y `python -m db.indexes.probar_indices` (usan `agrosense_tests`). Ver `docs/simulador.md`, `docs/consultas.md` y `docs/performance.md`. Dashboard: `python -m streamlit run dashboard/app.py` (con la base cargada; abre `http://localhost:8501`) y `python -m dashboard.probar_datos` (37 casos), `python -m dashboard.probar_detalle` (53), `python -m dashboard.probar_alertas` (44), `python -m dashboard.probar_nodos` (31) y `python -m dashboard.probar_pantallas` (46, de punta a punta con `streamlit.testing`); las de consultas leen `agrosense_tests`.
- Backup y restauración (requieren MongoDB Database Tools: `winget install MongoDB.DatabaseTools`; el instalador no los agrega al PATH y los scripts los encuentran solos, o con `AGROSENSE_HERRAMIENTAS`): `python -m scripts.backup_restore.backup` (copia en `~/agrosense-backups` o `AGROSENSE_BACKUP_DIR`, nunca dentro del repo, y rota), `python -m scripts.backup_restore.restaurar --comparar-con agrosense` (al último backup en `agrosense_restaurada` y lo verifica) y `python -m scripts.backup_restore.probar_respaldo` (19 casos sobre `agrosense_tests`). Ver `docs/backup-restore.md`.

## 6. Reglas de dominio

- **Datos sintéticos.** Nodos y lecturas son simulados. Los documentos llevan `fuente` (por ejemplo, `simulado`) y, si fueron generados por una simulación en vivo, `escenario_id`. En `lecturas`, `escenario_id` va **dentro de `meta`** (junto con `nodo_id`, `parcela_id` y `finca_id`), para que "Reiniciar demo" pueda borrar con `deleteMany({ "meta.escenario_id": ... })`.
- **Umbral de helada por etapa BBCH, configurable** (colección `variedades`, ADR-005). Se compara con la **temperatura estimada en el brote** = sensor − Δ (Δ = 2 °C, supuesto configurable). Valores del Malbec: yema dormida −10,6 °C; yema hinchada −6,1 °C; brotación −3,9 °C; primera hoja −2,8 °C; 2 a 5 hojas −2,2 °C; racimos visibles −1,2 °C; floración y cuaje 0 °C. Los valores IDR + DACC (−1,1 y −0,6 °C) son de **frutales** y no se usan.
- **Nodo inactivo:** sin lecturas durante un tiempo configurable (inicial: 30 minutos).
- **Temperatura sospechosa** (ADR-009): una lectura de `temperatura_c` estrictamente más fría que `configuracion.sospechoso_minimo_c` de su departamento (San Rafael −4,5 °C y San Martín −2,8 °C, récord de septiembre del SMN; Tupungato −5,6 °C, supuesto adoptado calculado con La Consulta, ADR-012). No se rechaza ni se excluye de las consultas ni de las alertas: es el techo de generación del simulador (que falla con un mensaje claro si algún límite es `None`) y un aviso de la auditoría.
- **Noche extrema** (ADR-009): la única noche que puede superar ese límite, declarada en `configuracion.noche_extrema` (`finca_id`, `inicio`, `fin`, `minimo_c`): San Rafael, 5/10/2026 de 03:00 a 08:00 hora de Argentina, piso −6,3 °C en el sensor (supuesto adoptado, ADR-012). Es la noche de helada precargada (RF-13).
- **Alerta de helada:** se abre al superar el umbral y se cierra al recuperarse, guardando inicio, fin y mínima.
- **Etapa fenológica:** se guarda en escala BBCH (numérica, permite consultas por rango); Baggiolini solo se muestra como equivalencia en el dashboard. Se estima por grados-día (Q9: base 10 °C, (Tmáx + Tmín)/2, tope de 32 °C, desde el 1/9; 260 grados-día de brotación a floración y 712 de floración a envero, Zapata 2017) y se corrige con observaciones manuales; si hay observación, manda la observación (ADR-004). La regla exacta (promedio de los 2 nodos, día local, grados-día hasta el día anterior) está en `docs/simulador.md` y Q9 tiene que usarla igual.
- **Índice de riesgo de helada:** nivel base por el margen entre la mínima del brote y el umbral (bajo > 2 °C, medio 0 a 2 °C, alto ≤ 0 °C); sube un nivel por 2 h o más cerca del umbral, por aire seco (< 60 %) o por suelo seco. No es un porcentaje de daño (ADR-005).
- **Riego y suelo por finca:** San Rafael surco y suelo franco; San Martín surco y franco arenoso; Tupungato goteo y pedregoso (ADR-005).
- **Riego simulado mixto:** turnos fijos más riegos extra cuando se abre la alerta de riego. Surco: 76 mm brutos cada 7 días; goteo: 1,5 a 3,5 mm por día según el mes (ADR-004 y ADR-005).
- **Alerta de riego:** se abre cuando la humedad de suelo baja del umbral del suelo de la finca en ese período (por ejemplo, franco 19,2 %). Los umbrales se calculan con la FAO-56: `θFC − p × (θFC − θWP)` con p = 0,45 (Tablas 19 y 22). Franco 19,2 %, franco arenoso 17,6 % y pedregoso 7,8 % (supuesto adoptado), iguales en los 4 períodos (ADR-011).

## 7. Consultas que el modelo debe resolver

| ID | Pregunta | Técnica |
|---|---|---|
| Q1 | Horas bajo 0 °C por parcela en una noche | `$group`, `$setWindowFields` |
| Q2 | Parcelas con mínima bajo el umbral de su estado fenológico | `$lookup` |
| Q3 | Nodos más cercanos a un punto | `$geoNear` sobre `nodos` (colección común) |
| Q4 | Parcelas dentro del polígono de un evento climático | `$geoIntersects` |
| Q5 | Nodos sin reportar en los últimos 30 minutos | `$group` + `$match` |
| Q6 | Humedad de suelo promedio por hora (últimas 24 h) | agregación |
| Q7 | Litros regados por parcela y semana | `$group` |
| Q8 | Eventos de helada por departamento y semana | `$group` + `$lookup` |
| Q9 | Etapa fenológica estimada por grados-día acumulados | `$setWindowFields` (suma acumulada) |
| Q10 | Índice de riesgo de helada por parcela y noche | `$group` + `$lookup` |

Cada consulta va en `db/queries/qN_nombre.py` (Python con `pymongo`, ADR-014), con un docstring inicial que indique la pregunta, el requisito y la técnica. Todas tienen la misma forma: `pipeline(...)` (la lista de etapas), `consultar(bd, ...)` (la ejecuta; la usa el dashboard) y `main()` (la consola, con `--mongosh` para ver la versión de `mongosh`). Explicación etapa por etapa y resultados reales en `docs/consultas.md`.

## 8. Estructura del repositorio

```
agrosense/
├── README.md
├── CLAUDE.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
├── .gitignore
├── .github/
│   ├── ISSUE_TEMPLATE/        # feature.md, bug.md, spike.md
│   └── PULL_REQUEST_TEMPLATE.md
├── docs/
│   ├── vision.md
│   ├── requisitos.md
│   ├── roadmap.md
│   ├── architecture.md
│   ├── modelo-datos.md
│   ├── simulador.md
│   ├── seed.md
│   ├── consultas.md
│   ├── performance.md
│   ├── backup-restore.md
│   ├── git-workflow.md
│   ├── equipo.md
│   ├── investigacion/
│   ├── ux/                    # pantallas.md, usuarios-y-flujos.md, wireframes/
│   ├── decisions/             # ADR-001 a ADR-016
│   └── sprints/
├── db/                        # paquete de Python (python -m db.…)
│   ├── conexion.py            # AGROSENSE_URI y AGROSENSE_BD
│   ├── departamentos.py       # "San Martín" → san_martin
│   ├── schemas/               # un esquema por colección, crear, validar y probar (ADR-008)
│   ├── indexes/               # crear_indices.py (3 geoespaciales y 4 de rendimiento), medir_indices.py, probar_indices.py (ADR-014 y ADR-015)
│   ├── seeds/                 # cargador y datos fijos (python -m db.seeds.cargar), ADR-010
│   └── queries/               # q1 a q10 (python -m db.queries.qN_nombre), comun.py, auditoría y probar_consultas.py
├── simulator/                 # temporada simulada (python -m simulator.generar), ADR-013
├── dashboard/                 # app.py (menú), paginas/ (resumen.py, detalle.py, alertas.py y nodos.py), data.py, lateral.py, piezas.py, piezas_alertas.py, piezas_nodos.py, formato.py, mapa.py, graficos.py, estilo.py y probar_*.py (ADR-018 a ADR-021)
├── .streamlit/                # config.toml: tema oscuro
├── PRODUCT.md                 # contexto de producto para el diseño de la interfaz
├── scripts/                   # spikes en spike-*/
│   └── backup_restore/        # backup.py, restaurar.py, comun.py, probar_respaldo.py (ADR-016)
├── requirements.txt           # dependencias de Python (versiones fijas)
├── install.sh                 # crea .venv e instala requirements.txt
└── .gitattributes             # los .sh con fin de línea LF
```

## 9. Flujo de Git

- Rama principal `main`. Trabajo en ramas con prefijo: `docs/...`, `feat/...`, `perf/...`, `chore/...`, `fix/...`.
- Commits en español, Conventional Commits: `docs(requisitos): agrega consultas principales (#3)`.
- Cada tarea: **issue → rama → commits → pull request → revisión de la otra persona → merge**, con `Closes #N` en el PR.
- Un milestone por sprint. Issues de máximo 3 a 4 horas, con responsable asignado.
- Cada persona usa su propia cuenta de GitHub, para que el aporte individual quede registrado.
- No hacer `push --force` ni reescribir historia sin pedirlo. Detalle en `docs/git-workflow.md`.

## 10. Calendario

| Sprint | Fechas | Foco |
|---|---|---|
| A | 6/10 a 12/10 | Repo, documentación, modelado, validaciones, wireframes, simulador base |
| B | 13/10 a 19/10 | Carga de datos, Q1 a Q10, índices con medición, noche precargada, inicio del dashboard |
| C | 20/10 a 26/10 | Dashboard completo, backup con restauración, roles, demo sin internet |
| Cierre | 27/10 y 28/10 | Congelar, ensayar la demo, tag `v1.0.0`, entrega |

**Prioridades (lo que se sacrifica primero va al final):** 1) núcleo de la base de datos (incluye Q9 y Q10), 2) dashboard con 4 pantallas y noche precargada, 3) estilo visual oscuro y pulido, 4) variedad simulada X, 5) simulación en vivo.

## 11. Interfaz (UI/UX)

Detalle completo en `docs/ux/pantallas.md`.

- Dashboard web de **escritorio** con Streamlit + Plotly, tema oscuro, para la demo en la notebook. Obligatorio.
- Estructura:

```
dashboard/
├── app.py            # menú y estilo (st.navigation)
├── paginas/          # una pantalla por archivo (solo presentación)
├── data.py           # llama a las consultas de db/queries y las cachea (ADR-014)
└── piezas.py, piezas_alertas.py, piezas_nodos.py, formato.py, mapa.py, graficos.py, lateral.py, estilo.py   # textos, figuras y barra lateral
```

Reglas:

- Las consultas a MongoDB viven en `db/queries/` (ADR-014); `data.py` las importa y les agrega el caché, y las páginas solo llaman a `data.py`. El panel "Ver consulta" muestra `comun.texto_mongosh(...)`.
- Cada pantalla tiene un panel "Ver consulta" y la etiqueta visible **"datos simulados"**.
- Cachear la conexión (`st.cache_resource`) y las consultas pesadas (`st.cache_data`).
- Layout de escritorio (`layout="wide"`).
- Mapa **sin mapa base**: polígonos de parcelas en Plotly (longitud y latitud). Sin dependencias de internet; probar con el wifi apagado.
- Verificar las versiones instaladas de Streamlit y Plotly antes de escribir código y fijarlas en el `requirements.txt` de la raíz.
- Probar cada pantalla con datos del seed y correr la app antes de dar algo por terminado.
- Pantallas: resumen de finca (con selector de finca), detalle de parcela, alertas, estado de nodos.
- Selector de **fecha de referencia** en la barra lateral: es el "ahora" de Q5 y Q6, que lo reciben como parámetro (ADR-004).
- Observaciones fenológicas: solo precargadas en el seed; el dashboard es de solo lectura.
- **Simulación en vivo (opcional):** reproduce la noche paso a paso (unos 30 segundos), inserta lecturas en MongoDB y ejecuta la regla de alerta en cada paso; la alerta debe salir de la base. Variable con valores aleatorios acotados y semilla opcional; datos marcados con `escenario_id` y botón "Reiniciar demo". Verificar el bucle con la versión instalada de Streamlit. Es lo primero que se recorta.

## 12. Definition of Done por tarea

- [ ] Hace lo que pide el issue y está dentro del alcance.
- [ ] Probado (consulta ejecutada, resultado verificado o script corrido).
- [ ] Documentación actualizada (`docs/`, comentario o ADR) y también `CLAUDE.md`, `README.md` y `CHANGELOG.md` (regla de la sección 2).
- [ ] Commit con mensaje convencional y PR enlazado al issue.
- [ ] Revisado por la otra persona del equipo.
- [ ] Quien lo hizo entiende el cambio y puede explicarlo.
- [ ] Sin credenciales ni datos sensibles (el repo es público).

## 13. Estado actual y pendientes

**Hecho (21/10/2026):** documentación y ADR-001 a ADR-016 y ADR-018 a ADR-021; esquemas `$jsonSchema` de las 10 colecciones con 62 pruebas; seed base; umbrales de riego; simulador de la temporada (727.980 lecturas, alertas, riegos y observaciones, con 51 pruebas); base `agrosense` cargada y auditada; consultas Q1 a Q10 en Python (43 pruebas contra cálculos independientes) y los 3 índices geoespaciales; 4 índices de rendimiento medidos antes y después en las 10 consultas (`docs/performance.md`, 19 pruebas); backup y restauración con `mongodump`/`mongorestore` probados sobre la base real (727.980 lecturas restauradas igual, 19 pruebas, `docs/backup-restore.md`); dashboard con las 4 pantallas: "Resumen de la mañana" (ADR-018), "Detalle de parcela" (ADR-019), "Alertas" (ADR-020) y "Estado de nodos" (ADR-021), con navegación entre ellas y 211 pruebas (datos, mapa, textos, gráficos y pantallas de punta a punta); falta probarlas con el wifi apagado.

**Falta:** probar el dashboard con el wifi apagado y en pantallas angostas; roles y autenticación (acordado en la entrevista del 21/10/2026, en un PR aparte, ADR-017: cuatro usuarios `admin` con rol `root`, `dashboard` con `read`, `simulador` con `readWrite` y `dbAdmin` sobre `agrosense` y `agrosense_tests`, y `respaldo` con `backup` y `restore`; autenticación activada en la instancia real; claves en un `.env` ignorado por git); opcionales (variedad simulada X, simulación en vivo).

**Pendientes conocidos:**
- Respuesta de la DACC a un pedido de series horarias (no bloquea nada: todo es simulado).
