# Requisitos

**Estado:** v0.2
Contexto y alcance en [`vision.md`](vision.md).

---

## 1. Alcance del MVP

3 fincas ficticias en 3 departamentos de Mendoza, 6 parcelas (2 por finca), 12 nodos (2 por parcela) y 3 variables (temperatura, humedad de suelo, humedad de aire), con alertas de helada y de riego, y un dashboard de 4 pantallas.

## 2. Volumen de datos

| Concepto | Cálculo | Resultado |
|---|---|---|
| Lecturas por nodo por día | 1 cada 5 minutos | 288 |
| Lecturas por día (12 nodos) | 12 × 288 | 3.456 |
| Historia simulada | 30 días | unas 103.680 lecturas |
| Escenario realista (referencia) | 50 nodos, 1 año | unas 5,3 millones de lecturas |

El escenario realista justifica la serie temporal, los índices y una política de retención. Las pruebas de rendimiento usan como mínimo 100.000 lecturas.

## 3. Requisitos funcionales

| ID | Requisito | Prioridad |
|---|---|---|
| RF-01 | Registrar fincas y parcelas con su departamento, geometría (GeoJSON), variedad y estado fenológico | Obligatorio |
| RF-02 | Registrar nodos de sensores con ubicación, parcela asociada y estado | Obligatorio |
| RF-03 | Almacenar lecturas de temperatura, humedad de suelo y humedad de aire con marca de tiempo | Obligatorio |
| RF-04 | Generar alertas de helada cuando la temperatura baja del umbral configurado para el estado fenológico de la parcela | Obligatorio |
| RF-05 | Registrar eventos de riego (parcela, inicio, fin, litros, origen manual o automático) | Importante |
| RF-06 | Detectar nodos que dejaron de reportar | Importante |
| RF-07 | Consultar nodos y parcelas por cercanía a un punto o por intersección con un área | Importante |
| RF-08 | Registrar eventos climáticos con su polígono afectado | Importante |
| RF-09 | Generar datos sintéticos (30 días, 12 nodos) con escenarios normales y de helada distribuidos entre las fincas y las semanas | Obligatorio |
| RF-10 | Validar la estructura de los documentos con `$jsonSchema` | Importante |
| RF-11 | Dashboard web de escritorio con 4 pantallas: resumen de finca, detalle de parcela, alertas y estado de nodos | Obligatorio |
| RF-12 | El dashboard usa tema oscuro, muestra la etiqueta "datos simulados" y un panel "Ver consulta" en cada pantalla | Obligatorio |
| RF-13 | El seed incluye una **noche de helada precargada** visible en el dashboard | Obligatorio |
| RF-14 | Botón "Simular noche de helada" que reproduce la noche paso a paso (unos 30 segundos), insertando lecturas en MongoDB y ejecutando la regla de alerta en cada paso. Cada noche varía con valores aleatorios acotados y una semilla opcional | **Opcional** (se recorta primero) |
| RF-15 | Botón "Reiniciar demo" que borra lo generado por la simulación en vivo (identificado con `escenario_id`) | **Opcional** (depende de RF-14) |

## 4. Requisitos no funcionales

| ID | Requisito | Verificación |
|---|---|---|
| RNF-01 | Las consultas principales se miden con `explain("executionStats")` antes y después de aplicar índices | `docs/performance.md` |
| RNF-02 | Existe una política de backup documentada (frecuencia, retención) con script reproducible | `docs/backup-restore.md` |
| RNF-03 | La restauración de un backup se prueba y se documenta | Prueba registrada |
| RNF-04 | Existen al menos dos roles de usuario con permisos distintos (por ejemplo, lectura y administración) | Evidencia en el repo |
| RNF-05 | El proyecto se puede reconstruir desde el repositorio (esquemas, índices, seeds, simulador, dashboard) | README con pasos |
| RNF-06 | Las decisiones de diseño relevantes quedan registradas | `docs/decisions/` |
| RNF-07 | El repositorio es público: no contiene credenciales, cadenas de conexión con contraseña ni backups con datos | Revisión en cada pull request |
| RNF-08 | La demo funciona sin conexión a internet | Prueba con el wifi apagado |

## 5. Reglas de negocio

- **Umbral de helada por estado fenológico.** Cada parcela tiene un estado (reposo, brotación, floración, etc.) y cada estado tiene un umbral de temperatura. Los valores son configurables y deben validarse con criterio agronómico antes de usarse.

| Estado fenológico | Umbral de alerta |
|---|---|
| Brotación | Valor de trabajo: −2 °C (sin aval oficial verificado) |
| Floración | Ejemplo de trabajo: −1,5 °C (a validar) |
| Otros estados | A definir |

  Referencia del informe IDR + DACC 2021 (nomenclatura de frutales): −1,1 °C en corola visible y −0,6 °C en plena flor y fruto cuajado.

- **Nodo sin reportar.** Un nodo se considera inactivo si no envía lecturas durante un tiempo configurable (valor inicial: 30 minutos).
- **Alerta de helada.** Se abre cuando se supera el umbral y se cierra cuando la temperatura se recupera, guardando inicio, fin y mínima registrada.

## 6. Consultas que el sistema debe responder

| ID | Pregunta | Técnica principal | Requisito |
|---|---|---|---|
| Q1 | ¿Cuántas horas estuvo cada parcela por debajo de 0 °C en una noche? | `$group`, `$setWindowFields` | RF-03, RF-04 |
| Q2 | ¿Qué parcelas tuvieron una mínima por debajo del umbral de su estado fenológico? | `$lookup` lecturas → parcelas | RF-01, RF-04 |
| Q3 | ¿Qué nodos están más cerca de un punto dado? | `$geoNear` | RF-07 |
| Q4 | ¿Qué parcelas quedan dentro del polígono de un evento climático? | `$geoIntersects` | RF-07, RF-08 |
| Q5 | ¿Qué nodos no reportaron en los últimos 30 minutos? | `$group` + `$match` | RF-06 |
| Q6 | ¿Cuál es la humedad de suelo promedio por hora de una parcela en las últimas 24 horas? | Agregación sobre lecturas | RF-03 |
| Q7 | ¿Cuántos litros se regaron por parcela en la semana? | `$group` | RF-05 |
| Q8 | ¿Cuántos eventos de helada hubo por departamento y por semana? | `$group` + `$lookup` (alertas → parcelas → fincas) | RF-04, RF-08 |

## 7. Colecciones candidatas (modelo preliminar)

| Colección | Contenido |
|---|---|
| `fincas` | Nombre, departamento, ubicación, geometría |
| `parcelas` | Finca, variedad, estado fenológico, geometría |
| `nodos` | Parcela, ubicación (Point), estado, sensores |
| `lecturas` | `ts`, `meta` (nodo, parcela), temperatura, humedades, `fuente`, `escenario_id` |
| `alertas` | Tipo, parcela, inicio, fin, valor mínimo, estado, `escenario_id` |
| `riegos` | Parcela, inicio, fin, litros, origen |
| `eventos_climaticos` | Tipo, inicio, fin, polígono afectado, mínima |

El diseño detallado va en [`modelo-datos.md`](modelo-datos.md).

## 8. Criterios de aceptación del MVP

- [ ] Las 7 colecciones existen con validación de esquema.
- [ ] El simulador carga unas 100.000 lecturas o más, con noches de helada en las 3 fincas.
- [ ] Las consultas Q1 a Q8 están en `db/queries/` y devuelven resultados correctos sobre los datos simulados.
- [ ] Hay mediciones antes y después de índices para al menos 3 consultas.
- [ ] El backup se genera con un script y la restauración fue probada.
- [ ] Existen al menos 2 roles de usuario.
- [ ] El dashboard muestra las 4 pantallas con la noche precargada, con tema oscuro, y funciona sin internet.
- [ ] El README permite reconstruir el proyecto desde cero.

## 9. Trabajo futuro

Siniestros y tasaciones, seguros, contratistas, cosechas, costos de labores, hidrología, integración con estaciones reales, versión móvil, alerta temprana y pronóstico, y alertas por change streams (requiere replica set).

## 10. Trazabilidad con el calendario

| Sprint | Requisitos |
|---|---|
| A | Documentación base, entorno, RF-01, RF-02, RF-10, modelo de datos, simulador base (RF-09), wireframes |
| B | RF-03 a RF-08, consultas Q1 a Q8, RNF-01, seed con la noche precargada (RF-13), inicio del dashboard |
| C | RF-11, RF-12, RNF-02, RNF-03, RNF-04, RNF-08; RF-14 y RF-15 solo si hay tiempo |
| Cierre | Criterios de aceptación, RNF-05, RNF-07 |
