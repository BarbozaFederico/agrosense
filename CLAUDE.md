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

Investigación en `docs/investigacion/`: contexto, fuentes de datos, dos informes del Malbec y `verificacion-fuentes.md` (prevalece sobre los informes). Decisiones en `docs/decisions/` (ADR-001 a ADR-005).

## 4. Alcance del MVP

- **3 fincas ficticias en 3 departamentos de Mendoza, 6 parcelas (2 por finca), 12 nodos (2 por parcela)**, 3 variables (temperatura, humedad de suelo, humedad de aire), 2 tipos de alerta (helada y riego).
- Variedad: **Malbec** en las 6 parcelas; una "variedad simulada X" es opcional al final (ADR-004).
- Colecciones: `fincas`, `parcelas`, `nodos`, `lecturas`, `alertas`, `riegos`, `eventos_climaticos`, `observaciones_fenologicas` y la colección de configuración `variedades` (ADR-003 y ADR-004).
- Temporada simulada: 1/9/2026 a 31/3/2027, 1 lectura cada 5 minutos por nodo, unas 732.700 lecturas; 6 a 8 noches de helada entre septiembre y noviembre.
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
| Validación | `$jsonSchema` en todas las colecciones |
| Simulador | Python + `pymongo`, en `simulator/`, con funciones importables |
| Backup | `mongodump` y `mongorestore`, scripts en `scripts/` |
| Interfaz | Streamlit + Plotly, web de escritorio; toda consulta en `dashboard/data.py`. Ver ADR-002 |
| Móvil | Fuera de alcance |
| Licencia | MIT |

Precaución: probar temprano cómo se combinan índices geoespaciales y series temporales en la versión instalada. Si no se pueden combinar, `eventos_climaticos` va como colección común.

## 6. Reglas de dominio

- **Datos sintéticos.** Nodos y lecturas son simulados. Los documentos llevan `fuente` (por ejemplo, `simulado`) y, si fueron generados por una simulación en vivo, `escenario_id`.
- **Umbral de helada por etapa BBCH, configurable** (colección `variedades`, ADR-005). Se compara con la **temperatura estimada en el brote** = sensor − Δ (Δ = 2 °C, supuesto configurable). Valores del Malbec: yema dormida −10,6 °C; yema hinchada −6,1 °C; brotación −3,9 °C; primera hoja −2,8 °C; 2 a 5 hojas −2,2 °C; racimos visibles −1,2 °C; floración y cuaje 0 °C. Los valores IDR + DACC (−1,1 y −0,6 °C) son de **frutales** y no se usan.
- **Nodo inactivo:** sin lecturas durante un tiempo configurable (inicial: 30 minutos).
- **Alerta de helada:** se abre al superar el umbral y se cierra al recuperarse, guardando inicio, fin y mínima.
- **Etapa fenológica:** se guarda en escala BBCH. Se estima por grados-día (Q9) y se corrige con observaciones manuales; si hay observación, manda la observación.
- **Índice de riesgo de helada:** nivel base por el margen entre la mínima del brote y el umbral (bajo > 2 °C, medio 0 a 2 °C, alto ≤ 0 °C); sube un nivel por 2 h o más cerca del umbral, por aire seco (< 60 %) o por suelo seco. No es un porcentaje de daño (ADR-005).
- **Riego y suelo por finca:** San Rafael surco y suelo franco; San Martín surco y franco arenoso; Tupungato goteo y pedregoso (ADR-005).

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
| Q9 | Etapa fenológica estimada por grados-día acumulados | `$setWindowFields` (suma acumulada) |
| Q10 | Índice de riesgo de helada por parcela y noche | `$group` + `$lookup` |

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
│   ├── decisions/             # ADR-001 a ADR-005
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
- Selector de **fecha de referencia** en la barra lateral: es el "ahora" de Q5 y Q6, que lo reciben como parámetro (ADR-004).
- Observaciones fenológicas: solo precargadas en el seed; el dashboard es de solo lectura.
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

- Respuesta de la DACC a un pedido de series horarias (no bloquea nada: todo es simulado).
