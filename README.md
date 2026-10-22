# 🍇 agrosense

> Monitoreo de sensores en viñedos (temperatura, humedad, alerta de heladas y riego) sobre una base de datos MongoDB.

![MongoDB](https://img.shields.io/badge/MongoDB-47A248?logo=mongodb&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Estado](https://img.shields.io/badge/estado-en%20desarrollo-orange)
![Licencia](https://img.shields.io/badge/licencia-MIT-blue)

**agrosense** es un proyecto académico de *Diseño de Bases de Datos II* (Universidad de Mendoza, 2026). Diseña e implementa una base de datos MongoDB que almacena las lecturas de sensores de varias fincas y permite detectar riesgo de helada por parcela, registrar el riego y consultar los datos desde un dashboard web.

> **Todos los datos del proyecto son sintéticos.** Los genera un simulador, se inspiran en eventos reales y no representan fincas reales ni datos oficiales.

## Qué resuelve

Las heladas tardías son un riesgo central para la vitivinicultura de Mendoza, y la información para gestionarlas está repartida y llega tarde. agrosense reúne en un solo lugar las lecturas por parcela y responde preguntas como: ¿qué parcelas estuvieron bajo el umbral de helada anoche, desde cuándo y cuántas horas, y se regó?

El foco del proyecto es la **capa de datos**: modelado documental, carga masiva, consultas avanzadas, índices medidos y política de resguardo. Más contexto en [`docs/vision.md`](docs/vision.md).

## Alcance del MVP

| Elemento | Valor |
|---|---|
| Fincas | 3, en 3 departamentos de Mendoza (ficticias) |
| Parcelas y nodos | 6 parcelas y 12 nodos simulados |
| Variables | Temperatura, humedad de suelo y humedad de aire |
| Alertas | Helada y riego |
| Variedad | Malbec (variedad simulada adicional, opcional) |
| Temporada simulada | 1/9/2026 a 31/3/2027 |
| Consultas avanzadas | 10 (Q1 a Q10) |
| Interfaz | Dashboard web de escritorio con 4 pantallas |

## Tecnologías

| Capa | Tecnología |
|---|---|
| Base de datos | MongoDB Community Server, `mongosh`, MongoDB Compass |
| Simulador y acceso a datos | Python y `pymongo` |
| Dashboard | Streamlit y Plotly (tema oscuro) |
| Resguardo | `mongodump` y `mongorestore` |
| Control de versiones | Git y GitHub |

## Estructura del repositorio

```
agrosense/
├── docs/          # documentación (visión, requisitos, modelo, UX, decisiones)
├── db/            # esquemas, índices, seeds y consultas
├── simulator/     # simulador de sensores (Python)
├── dashboard/     # dashboard Streamlit
├── scripts/       # backup y restauración (backup_restore/) y spikes
└── .github/       # plantillas de issues y pull requests
```

## Documentación

| Documento | Contenido |
|---|---|
| [`docs/vision.md`](docs/vision.md) | Problema, propuesta, alcance |
| [`docs/requisitos.md`](docs/requisitos.md) | Requisitos, reglas de negocio, consultas, criterios de aceptación |
| [`docs/roadmap.md`](docs/roadmap.md) | Calendario y sprints |
| [`docs/architecture.md`](docs/architecture.md) | Arquitectura y convenciones |
| [`docs/modelo-datos.md`](docs/modelo-datos.md) | Modelo de datos |
| [`docs/esquemas-validacion.md`](docs/esquemas-validacion.md) | Esquemas `$jsonSchema`: cómo se crean, se prueban y se auditan |
| [`docs/simulador.md`](docs/simulador.md) | Simulador: qué genera, parámetros, calendario de heladas y pruebas |
| [`docs/ux/pantallas.md`](docs/ux/pantallas.md) | Pantallas y comportamiento del dashboard |
| [`docs/performance.md`](docs/performance.md) | Índices: mediciones antes y después de las 10 consultas, costo y experimentos |
| [`docs/backup-restore.md`](docs/backup-restore.md) | Política de resguardo, procedimiento y prueba de restauración |
| [`docs/git-workflow.md`](docs/git-workflow.md) | Flujo de trabajo en Git |
| [`docs/equipo.md`](docs/equipo.md) | Equipo y reparto de tareas |
| [`docs/seed.md`](docs/seed.md) | Seed base: qué carga, cómo se usa y qué supuestos tiene |
| [`docs/consultas.md`](docs/consultas.md) | Consultas Q1 a Q10: qué responden, cómo se calculan etapa por etapa y su resultado real |
| [`docs/decisions/`](docs/decisions/) | Decisiones de diseño (ADR-001 a ADR-016 y ADR-018 a ADR-020) |
| [`docs/investigacion/`](docs/investigacion/) | Investigación de contexto y fuentes de datos |

## Hoja de ruta

| Sprint | Fechas | Foco |
|---|---|---|
| A | 6/10 a 12/10 | Repo, documentación, modelado, simulador base |
| B | 13/10 a 19/10 | Carga de datos, consultas Q1 a Q10, índices medidos |
| C | 20/10 a 26/10 | Dashboard, backup y roles |
| Cierre | 27/10 y 28/10 | Congelar, ensayar la demo, entrega |

Detalle en [`docs/roadmap.md`](docs/roadmap.md).

## Cómo ejecutarlo

Requisitos: MongoDB Server 9.0 en marcha, `mongosh` en el PATH y Python 3.10 o superior. Desde la raíz del repositorio (en PowerShell, `install.sh` se corre con `bash install.sh`):

```bash
bash install.sh                          # crea .venv e instala las dependencias
source .venv/Scripts/activate            # Git Bash en Windows (en Linux y macOS: .venv/bin/activate)

python -m db.schemas.crear_colecciones   # crea las 10 colecciones con sus validadores
python -m db.seeds.cargar                # fincas, parcelas, nodos, variedad y configuración
python -m simulator.generar              # la temporada simulada (~25 s) y su auditoría
python -m db.indexes.crear_indices       # 3 índices geoespaciales (Q3 no funciona sin ellos) y 4 de rendimiento
python -m db.indexes.medir_indices       # opcional: mediciones antes y después (usa agrosense_tests)
```

Consultas (cada una acepta `--help` y `--mongosh`, que muestra la misma consulta para `mongosh`):

```bash
python -m db.queries.q9_etapa_por_grados_dia --fecha 2026-10-05
python -m db.queries.q10_riesgo_de_helada --fecha 2026-09-21
python -m db.queries.q5_nodos_sin_reportar --ahora 2026-11-12T21:00:00Z
```

Las diez están en [`docs/consultas.md`](docs/consultas.md).

Backup y restauración (requieren MongoDB Database Tools: `winget install MongoDB.DatabaseTools`). Los respaldos se guardan fuera del repositorio, en `~/agrosense-backups` o en la carpeta de `AGROSENSE_BACKUP_DIR`:

```bash
python -m scripts.backup_restore.backup                           # copia de agrosense (7 diarios y 4 semanales) con su manifiesto
python -m scripts.backup_restore.restaurar --comparar-con agrosense   # restaura el último en agrosense_restaurada y lo verifica
```

Política, procedimiento y la prueba de restauración en [`docs/backup-restore.md`](docs/backup-restore.md).

Pruebas (usan la base `agrosense_tests`, no tocan `agrosense`):

```bash
python -m db.schemas.probar_esquemas     # 62 casos de los esquemas
python -m simulator.probar_simulador     # 51 casos del simulador (~1 min)
python -m db.queries.probar_consultas    # 43 casos de las consultas contra cálculos independientes (~30 s)
python -m db.indexes.probar_indices      # 19 casos: los índices existen, se usan y no cambian ninguna respuesta
python -m scripts.backup_restore.probar_respaldo        # 19 casos: backup, rotación, restauración y protecciones (unos segundos)
python -m dashboard.probar_datos         # 37 casos de los datos y del mapa de "Resumen de la mañana" (unos segundos)
python -m dashboard.probar_detalle       # 53 casos de "Detalle de parcela": datos, textos, gráficos y consultas de apoyo
python -m dashboard.probar_alertas       # 44 casos de "Alertas": datos, textos, filtros, historial, semanas y consultas de apoyo
python -m dashboard.probar_pantallas     # 36 casos de punta a punta: abre las tres pantallas, con las 6 parcelas, y prueba los controles
```

Dashboard (con la base cargada; se abre en `http://localhost:8501`). Hoy tiene tres pantallas, "Resumen de la mañana" ([ADR-018](docs/decisions/ADR-018-resumen-de-la-manana.md)), "Detalle de parcela" ([ADR-019](docs/decisions/ADR-019-detalle-de-parcela.md)) y "Alertas" ([ADR-020](docs/decisions/ADR-020-alertas.md)); la de estado de nodos está en construcción:

```bash
python -m streamlit run dashboard/app.py
```

La base se elige con la variable `AGROSENSE_BD` (por defecto `agrosense`). *Falta, y se agrega a medida que se completa:* una pantalla del dashboard y roles.

## Equipo

Ver [`docs/equipo.md`](docs/equipo.md).

## Licencia

[MIT](LICENSE).
