# Visión del proyecto

> Monitoreo de sensores en viñedos (temperatura, humedad, alerta de heladas y riego) sobre una base de datos documental MongoDB.

**Estado:** v0.2
**Contexto académico:** Diseño de Bases de Datos II, Universidad de Mendoza, 2026 (proyecto "Implementación práctica de una solución basada en el motor documental MongoDB"). Entrega: miércoles 28 de octubre de 2026.

---

## 1. Resumen

Este proyecto diseña e implementa una base de datos MongoDB que almacena y consulta las lecturas de sensores instalados en parcelas de viñedo de varias fincas. Con esos datos permite:

- Conocer el estado de las parcelas (temperatura, humedad de suelo y de aire).
- Detectar riesgo de helada por parcela, no por oasis.
- Registrar y consultar los eventos de riego.
- Resolver consultas geoespaciales (qué nodos y parcelas están cerca de un punto o dentro de un área afectada).
- Mostrar todo en un dashboard web de escritorio, que forma parte de la demo.

El foco es la **base de datos**: modelado documental, carga de datos, consultas avanzadas, índices con medición de rendimiento y política de resguardo.

## 2. Objetivo del MVP

El MVP tiene dos objetivos:

1. **Objetivo del problema.** Responder, con datos de sensores por parcela: *¿qué parcelas están en riesgo de helada, desde cuándo, y ya se regaron?*
2. **Objetivo académico.** Demostrar que el equipo sabe modelar, implementar y operar una base MongoDB. El caso de monitoreo de viñedos es el escenario donde se aplica.

El MVP **no resuelve el problema real del viñatero**, porque los datos son simulados. Resuelve y demuestra la capa de datos que haría falta para resolverlo.

## 3. Problema

Las heladas tardías son un riesgo central para la vitivinicultura de Mendoza, y la información para gestionarlas está repartida y llega tarde. Algunos datos del contexto relevado:

| Dato | Valor | Fuente y fecha |
|---|---|---|
| Superficie de vid en Mendoza | 140.682 ha en 14.371 viñedos; 17.903 ha menos que en 2016 | INV, Informe Anual de Superficie, al 31/12/2025 |
| Pérdidas por helada frente a granizo en el Oasis Sur | 76,3% heladas y 23,7% granizo, sobre 136.809 ha con pérdida denunciadas desde 2016-17 | Ministerio de Producción de Mendoza, citado por Mendoza24, 10/9/2026 |
| Visibilidad del daño por helada | Se ve recién entre 30 y 45 días después del evento | Ministerio de Economía de Mendoza, citado por Unidiversidad |
| Helada severa reciente | Mínima de −8,3 °C en Monte Comán | Prensa (Minuto Ya), 7/9/2026 |

Tres problemas de datos se desprenden del contexto relevado:

1. **Datos dispersos.** La información climática, de riego y de daños está repartida entre organismos, bodegas y gremios, y no se integra a nivel de finca y parcela.
2. **Cobertura desigual.** Según una ficha de proyecto de SAGyP/Fondagro, la zona Este no tenía estaciones meteorológicas de contingencias climáticas del Gobierno provincial.
3. **Cifras tardías y contradictorias.** Las estimaciones de daño cambian con el tiempo y entre fuentes, y no existe una serie histórica compartida.

> **Nota sobre las fuentes.** Las cifras provienen de un informe de búsqueda amplio (ver [`investigacion/`](investigacion/)) que combina datos de organismos y de prensa. Las de prensa deben verificarse en la fuente primaria (INV, DGI, Boletín Oficial) antes de usarse fuera de este documento.

## 4. Propuesta

Una base MongoDB que modele fincas, parcelas, nodos de sensores, lecturas, alertas, riegos y eventos climáticos, con estas decisiones técnicas:

- **Lecturas como serie temporal** (sujeto a la decisión [ADR-001](decisions/ADR-001-series-temporales.md)).
- **Datos geoespaciales** (GeoJSON y `2dsphere`) para ubicar fincas, parcelas y nodos.
- **Agregaciones** para calcular horas bajo cero, promedios por hora y litros regados.
- **Umbrales parametrizables.** El riesgo de helada depende del estado fenológico de la parcela, por lo que no se usa un único valor fijo.

## 5. Usuarios y casos de uso

| Usuario | Pregunta típica |
|---|---|
| Productor o encargado de finca | ¿Qué parcelas tuvieron riesgo de helada anoche? ¿Cuándo se regó por última vez? |
| Técnico agrónomo | ¿Cuántas horas estuvo cada parcela por debajo de su umbral? |
| Administrador del sistema | ¿Hay nodos sin reportar? ¿El backup se puede restaurar? |

## 6. Alcance

### Incluido en el MVP

- 3 fincas ficticias en 3 departamentos de Mendoza, con 6 parcelas y 12 nodos simulados.
- 3 variables: temperatura, humedad de suelo y humedad de aire.
- 2 tipos de alerta: helada y riego.
- Simulador de datos con escenarios de helada distribuidos entre las fincas.
- 8 consultas avanzadas, índices con medición de rendimiento y política de backup con restauración probada.
- **Dashboard web de escritorio** (Streamlit) con 4 pantallas, tema oscuro y una noche de helada precargada. Es parte obligatoria de la demo.

### Opcional (primero que se recorta si falta tiempo)

- Simulación de la noche **en vivo**, paso a paso, desde el dashboard.

### Fuera de alcance (trabajo futuro)

Siniestros y tasaciones, seguros, contratistas, cosechas, costos de labores, hidrología, integración con estaciones reales, versión móvil, alerta temprana y pronóstico.

## 7. Datos

Los datos del proyecto son **sintéticos**: los genera un simulador y se inspiran en eventos reales, pero no son datos oficiales ni de fincas reales.

## 8. Tecnologías

MongoDB Community Server, `mongosh`, MongoDB Compass, Python con `pymongo`, Streamlit con Plotly, `mongodump` y `mongorestore`. Detalle en [`architecture.md`](architecture.md).

## 9. Documentos relacionados

[`requisitos.md`](requisitos.md) · [`roadmap.md`](roadmap.md) · [`modelo-datos.md`](modelo-datos.md) · [`ux/pantallas.md`](ux/pantallas.md) · [`equipo.md`](equipo.md)
