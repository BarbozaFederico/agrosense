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
- No inventes datos ni cifras. Si algo no está verificado, marcalo como "a validar".
- **Repo público:** nunca subas credenciales, cadenas de conexión con contraseña, `.env`, backups ni datos personales.

## 3. Documentos del repo

Ver `README.md` para el índice. Los más importantes: `docs/vision.md`, `docs/requisitos.md`, `docs/roadmap.md`, `docs/architecture.md`, `docs/ux/pantallas.md`, `docs/equipo.md`.

Pendientes de copiar por el equipo a `docs/investigacion/`: `contexto-problema.md` y `fuentes-de-datos.md` (informes de contexto y de fuentes de datos). Si faltan, pedíselos antes de inventar su contenido.

## 4. Alcance del MVP

- **3 fincas ficticias en 3 departamentos de Mendoza, 6 parcelas (2 por finca), 12 nodos (2 por parcela)**, 3 variables (temperatura, humedad de suelo, humedad de aire), 2 tipos de alerta (helada y riego).
- Colecciones: `fincas`, `parcelas`, `nodos`, `lecturas`, `alertas`, `riegos`, `eventos_climaticos`.
- Historia simulada: 30 días, 1 lectura cada 5 minutos por nodo, unas 103.680 lecturas.
- **Dashboard web de escritorio con Streamlit: obligatorio.** 4 pantallas, tema oscuro, noche de helada precargada.
- **Opcional (primero que se recorta):** simulación de la noche en vivo desde el dashboard (RF-14 y RF-15).
- **Fuera de alcance:** siniestros, seguros, contratistas, cosechas, costos, hidrología, estaciones reales, versión móvil, alerta temprana y pronóstico, Docker y Atlas.

## 5. Decisiones técnicas acordadas

| Tema | Decisión |
|---|---|
| Motor | MongoDB Community Server (verificar la versión instalada antes de usar funciones nuevas) |
| Consola y GUI | `mongosh` y MongoDB Compass |
| Lecturas | Serie temporal (`timeField: ts`, `metaField: meta`) **si el docente lo confirma**; si no, colección común con índice compuesto. Ver ADR-001 |
| Geoespacial | GeoJSON + índices `2dsphere` |
| Validación | `$jsonSchema` en todas las colecciones |
| Simulador | Python + `pymongo`, en `simulator/`, con funciones importables |
| Backup | `mongodump` y `mongorestore`, scripts en `scripts/` |
| Interfaz | Streamlit + Plotly, web de escritorio; toda consulta en `dashboard/data.py`. Ver ADR-002 |
| Móvil | Fuera de alcance |
| Licencia | MIT |

Precaución: probar temprano cómo se combinan índices geoespaciales y series temporales en la versión instalada. Si no se pueden combinar, `eventos_climaticos` va como colección común.

## 6. Reglas de dominio

- **Datos sintéticos.** Nodos y lecturas son simulados. Los documentos llevan `fuente` (por ejemplo, `simulado`) y, si fueron generados por una simulación en vivo, `escenario_id`.
- **Umbral de helada por estado fenológico, configurable.** Cada parcela tiene `fenologia`; los umbrales viven en datos de configuración, no en el código. Valores de partida (a validar con criterio agronómico):
  - Informe IDR + DACC 2021 (nomenclatura de frutales): −1,1 °C en corola visible y −0,6 °C en plena flor y fruto cuajado.
  - Brotación: sin umbral oficial verificado; **valor de trabajo** −2 °C, marcado como supuesto.
  - Floración: ejemplo de trabajo −1,5 °C, a validar.
- **Nodo inactivo:** sin lecturas durante un tiempo configurable (inicial: 30 minutos).
- **Alerta de helada:** se abre al superar el umbral y se cierra al recuperarse, guardando inicio, fin y mínima.

## 7. Consultas que el modelo debe resolver

| ID | Pregunta | Técnica |
|---|---|---|
| Q1 | Horas bajo 0 °C por parcela en una noche | `$group`, `$setWindowFields` |
| Q2 | Parcelas con mínima bajo el umbral de su estado fenológico | `$lookup` |
| Q3 | Nodos más cercanos a un punto | `$geoNear` |
| Q4 | Parcelas dentro del polígono de un evento climático | `$geoIntersects` |
| Q5 | Nodos sin reportar en los últimos 30 minutos | `$group` + `$match` |
| Q6 | Humedad de suelo promedio por hora (últimas 24 h) | agregación |
| Q7 | Litros regados por parcela y semana | `$group` |
| Q8 | Eventos de helada por departamento y semana | `$group` + `$lookup` |

Cada consulta va en `db/queries/qN_nombre.js`, con un comentario inicial que indique la pregunta y el requisito asociado.

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
│   ├── performance.md
│   ├── backup-restore.md
│   ├── git-workflow.md
│   ├── equipo.md
│   ├── investigacion/
│   ├── ux/                    # pantallas.md, usuarios-y-flujos.md, wireframes/
│   ├── decisions/             # ADR-001, ADR-002
│   └── sprints/
├── db/
│   ├── schemas/
│   ├── indexes/
│   ├── seeds/
│   └── queries/
├── simulator/
├── dashboard/                 # data.py, app.py, requirements.txt
└── scripts/
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
| B | 13/10 a 19/10 | Carga de datos, Q1 a Q8, índices con medición, noche precargada, inicio del dashboard |
| C | 20/10 a 26/10 | Dashboard completo, backup con restauración, roles, demo sin internet |
| Cierre | 27/10 y 28/10 | Congelar, ensayar la demo, tag `v1.0.0`, entrega |

**Prioridades (lo que se sacrifica primero va al final):** 1) núcleo de la base de datos, 2) dashboard con 4 pantallas y noche precargada, 3) estilo visual oscuro y pulido, 4) simulación en vivo.

## 11. Interfaz (UI/UX)

Detalle completo en `docs/ux/pantallas.md`.

- Dashboard web de **escritorio** con Streamlit + Plotly, tema oscuro, para la demo en la notebook. Obligatorio.
- Estructura:

```
dashboard/
├── app.py            # pantallas (solo presentación)
├── data.py           # una función por consulta, con pymongo
└── requirements.txt  # versiones fijas
```

Reglas:

- Toda consulta a MongoDB vive en `data.py`; `app.py` solo las llama.
- Cada pantalla tiene un panel "Ver consulta" y la etiqueta visible **"datos simulados"**.
- Cachear la conexión (`st.cache_resource`) y las consultas pesadas (`st.cache_data`).
- Layout de escritorio (`layout="wide"`).
- Mapa **sin mapa base**: polígonos de parcelas en Plotly (longitud y latitud). Sin dependencias de internet; probar con el wifi apagado.
- Verificar las versiones instaladas de Streamlit y Plotly antes de escribir código y fijarlas en `requirements.txt`.
- Probar cada pantalla con datos del seed y correr la app antes de dar algo por terminado.
- Pantallas: resumen de finca (con selector de finca), detalle de parcela, alertas, estado de nodos.
- **Simulación en vivo (opcional):** reproduce la noche paso a paso (unos 30 segundos), inserta lecturas en MongoDB y ejecuta la regla de alerta en cada paso; la alerta debe salir de la base. Variable con valores aleatorios acotados y semilla opcional; datos marcados con `escenario_id` y botón "Reiniciar demo". Verificar el bucle con la versión instalada de Streamlit. Es lo primero que se recorta.

## 12. Definition of Done por tarea

- [ ] Hace lo que pide el issue y está dentro del alcance.
- [ ] Probado (consulta ejecutada, resultado verificado o script corrido).
- [ ] Documentación actualizada (`docs/`, comentario o ADR).
- [ ] Commit con mensaje convencional y PR enlazado al issue.
- [ ] Revisado por la otra persona del equipo.
- [ ] Quien lo hizo entiende el cambio y puede explicarlo.
- [ ] Sin credenciales ni datos sensibles (el repo es público).

## 13. Pendientes conocidos

- Confirmar con el docente si las series temporales entran en el alcance (ADR-001).
- Copiar los informes a `docs/investigacion/`, quitando datos de contacto personales.
- Verificar si el lunes 12/10 es feriado.
- Confirmar los departamentos de las 3 fincas ficticias y el reparto entre integrantes.
- Respuesta de la DACC a un pedido de series horarias (no bloquea nada: todo es simulado).
