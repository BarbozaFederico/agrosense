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
├── scripts/       # backup y restauración
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
| [`docs/simulador.md`](docs/simulador.md) | Escenarios y parámetros del simulador |
| [`docs/ux/pantallas.md`](docs/ux/pantallas.md) | Pantallas y comportamiento del dashboard |
| [`docs/performance.md`](docs/performance.md) | Mediciones de índices |
| [`docs/backup-restore.md`](docs/backup-restore.md) | Política de resguardo |
| [`docs/git-workflow.md`](docs/git-workflow.md) | Flujo de trabajo en Git |
| [`docs/equipo.md`](docs/equipo.md) | Equipo y reparto de tareas |
| [`docs/decisions/`](docs/decisions/) | Decisiones de diseño (ADR-001 a ADR-005) |
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

*Se completa a medida que avanza el proyecto.* Pasos previstos: instalar MongoDB, crear el entorno de Python, cargar el seed y levantar el dashboard.

## Equipo

Ver [`docs/equipo.md`](docs/equipo.md).

## Licencia

[MIT](LICENSE).
