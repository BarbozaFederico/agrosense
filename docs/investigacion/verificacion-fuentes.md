# Verificación en fuentes originales

**Fecha:** 8/10/2026. Se leyeron completos los tres documentos que las investigaciones automáticas no pudieron abrir. Este documento **prevalece** sobre [`vid-malbec.md`](vid-malbec.md) y [`vid-malbec-complemento.md`](vid-malbec-complemento.md) donde haya diferencias.

| Documento | Referencia |
|---|---|
| SMN, *Estadísticas Climatológicas Normales 1991-2020* (2023) | https://repositorio.smn.gob.ar/handle/20.500.12160/2506 — San Martín (Mza): pp. 504-511; San Rafael Aero: pp. 512-518 |
| INV, *Informe de Variedades Malbec 2025* (datos 2024) | https://www.argentina.gob.ar/sites/default/files/2018/10/informe_malbec-2025-inv.pdf — pp. 4, 5, 7 y 8 |
| Proebsting, Brummund y Clore, *Critical Temperatures for Concord Grapes*, WSU EB1615 (1991) | https://rex.libraries.wsu.edu/esploro/outputs/report/Critical-Temperatures-for-Concord-Grapes/99900502301701842 |

## 1. Normales del SMN 1991-2020

### Confirmado

Las temperaturas máxima, mínima y media, la humedad relativa media, la lluvia y los días con lluvia (≥ 0,1 mm) de septiembre a marzo **coinciden** con las tablas de `vid-malbec.md` (sección 6d) para San Rafael Aero y San Martín.

### Corregido

**1) Mínima absoluta (el valor diario más bajo de la temperatura mínima, 1991-2020).** Los valores del primer informe venían de una copia secundaria y **no coinciden** con el SMN:

| Mes | San Rafael: informe → **SMN** | San Martín: informe → **SMN** |
|---|---|---|
| Sep | −6,9 → **−4,5 °C** | −5,2 → **−2,8 °C** |
| Oct | −2,4 → **−2,4 °C** | −1,9 → **−0,5 °C** |
| Nov | −0,3 → **−0,3 °C** | −0,3 → **−0,3 °C** |
| Dic | 1,5 → **3,5 °C** | 2,4 → **4,2 °C** |
| Ene | 4,3 → **6,0 °C** | 5,3 → **8,2 °C** |
| Feb | 4,8 → **5,5 °C** | 4,0 → **6,3 °C** |
| Mar | −2,7 → **0,8 °C** | −1,4 → **3,3 °C** |

**Consecuencia para el simulador:** en el abrigo meteorológico, las heladas de septiembre no deberían bajar de unos −4,5 °C en San Rafael ni de unos −2,8 °C en San Martín. La recomendación anterior ("mínimas entre −1 y −5 °C") se ajusta a esos topes. Recordar que el brote puede estar 1 a 3 °C más frío que el abrigo (`vid-malbec-complemento.md`, sección 3).

**2) Altura de la estación San Martín:** **653 m**, no unos 770 m. San Rafael Aero: 751 m.

### Nuevo (antes "no encontrado")

**Punto de rocío medio mensual (°C), medido:**

| Mes | San Rafael Aero | San Martín |
|---|---|---|
| Sep | 1,3 | 2,8 |
| Oct | 4,4 | 6,2 |
| Nov | 6,9 | 9,2 |
| Dic | 9,1 | 11,8 |
| Ene | 11,4 | 14,1 |
| Feb | 11,6 | 14,0 |
| Mar | 10,7 | 13,0 |

**Humedad relativa de día y de noche (%),** calculada con el punto de rocío medido y las temperaturas máxima y mínima medias (fórmula de Magnus). Reemplaza la tabla "g" de `vid-malbec.md`, que usaba un punto de rocío supuesto. Marca: **adaptado** (cálculo propio sobre datos con fuente).

| Mes | San Rafael: día / noche | San Martín: día / noche |
|---|---|---|
| Sep | 28 / 78 | 28 / 73 |
| Oct | 28 / 77 | 28 / 72 |
| Nov | 27 / 74 | 28 / 71 |
| Dic | 26 / 71 | 29 / 71 |
| Ene | 29 / 75 | 32 / 77 |
| Feb | 32 / 82 | 35 / 83 |
| Mar | 35 / 86 | 39 / 88 |

Tupungato no tiene estación del SMN: se mantiene la estación El Peral (DACC) y su humedad de día y de noche sigue como supuesto.

**Días con helada por mes (SMN):**

| Mes | San Rafael Aero | San Martín |
|---|---|---|
| Sep | 2,8 | 0,7 |
| Oct | 0,2 | 0,1 |
| Nov | 0,1 | < 0,1 |

**Temperatura de bulbo húmedo media (°C), Sep / Oct / Nov:** San Rafael 7,4 / 10,5 / 13,1; San Martín 8,9 / 12,2 / 15,0.

## 2. INV, Informe de Variedades Malbec 2025

### Confirmado (tabla "Mendoza - Superficie Malbec por departamento", p. 5)

| Departamento | Malbec (ha) | % del Malbec de Mendoza | Vid total (ha) | % de Malbec en el departamento |
|---|---|---|---|---|
| Tupungato | 5.042 | 12,6 | 10.587 | 47,6 |
| San Rafael | 2.191 | 5,5 | 11.478 | 19,1 |
| San Martín | 1.456 | 3,7 | 25.847 | 5,6 |

- Mendoza: 39.856 ha de Malbec (84,7 % del país); país: 47.064 ha (p. 4).
- La fila "San Martín" de 219 ha es del departamento homónimo de **San Juan** (p. 5): confirmado.

### Nuevo: producción y rendimiento 2024 (pp. 7-8)

| Departamento | Malbec cosechado (qq) | Rendimiento (kg/ha, cálculo propio) |
|---|---|---|
| Tupungato | 497.672 | ~9.870 |
| San Rafael | 108.413 | ~4.950 |
| San Martín | 212.383 | ~14.590 |
| Mendoza | 3.459.719 | ~8.680 |

1 quintal = 100 kg. El rendimiento es contexto: la cosecha está fuera del alcance del proyecto.

### No está en el informe

El sistema de conducción y la densidad de plantación **no aparecen**: siguen como supuestos.

## 3. WSU EB1615 (Concord)

### Confirmado

Los valores de la Tabla 4.8 de la FAO coinciden con el original (en °F; conversión a °C):

| Etapa | T10 | T90 |
|---|---|---|
| Primera hinchazón | 13 °F = −10,6 °C | −3 °F = −19,4 °C |
| Hinchazón completa | 21 °F = −6,1 °C | 10 °F = −12,2 °C |
| Brotación ("bud burst") | 25 °F = −3,9 °C | 16 °F = −8,9 °C |
| 1.ª hoja | 27 °F = −2,8 °C | 21 °F = −6,1 °C |
| 2.ª hoja | 28 °F = −2,2 °C | 22 °F = −5,6 °C |
| 3.ª hoja | 28 °F = −2,2 °C | 26 °F = −3,3 °C |
| 4.ª y 5.ª hoja | 28 °F = −2,2 °C | 27 °F = −2,8 °C |

### Aclaraciones del original que conviene citar

- T10 y T90 son las temperaturas que matan el 10 % y el 90 % de las **yemas primarias**.
- Los valores se midieron **en laboratorio**, no se contrastaron mucho con daño en el campo y corresponden a **una sola temporada**. El boletín los presenta como una guía.
- Es uva **Concord** (*V. labruscana*), no vinífera.

## Resumen: qué cambia en el modelo

| Dato | Antes | Ahora | Marca |
|---|---|---|---|
| Mínima absoluta de septiembre (abrigo) | San Rafael −6,9; San Martín −5,2 °C | **−4,5 y −2,8 °C** | con fuente (SMN) |
| Humedad de día y de noche | Supuesto | Calculada con el punto de rocío del SMN | adaptado |
| Altura de San Martín | ~770 m | **653 m** | con fuente (SMN) |
| Hectáreas de Malbec por departamento | Leídas en un buscador | Confirmadas | con fuente (INV) |
| Umbrales de Concord (EB1615) | Vía FAO | Confirmados en el original | con fuente |
| Conducción y densidad de plantación | Supuesto | Sigue como supuesto (no está en el INV) | supuesto |

---

# Segunda ronda de verificación (8/10/2026)

Se leyeron completos cuatro documentos que las investigaciones solo conocían por fragmentos.

| Documento | Referencia |
|---|---|
| INIA, FDF, Vinos de Chile y DMC, *Heladas: tipos, medidas de prevención y manejos posteriores al daño* (2016, proyecto PYT 2015-0305) | http://www.fdf.cl/biblioteca/publicaciones/2016/heladas.pdf |
| Morábito, J. A., *Desempeño del riego por superficie en el área de riego del río Mendoza*, tesis de Magister en Riego y Drenaje (UNCuyo, INA, INTA) | https://bdigital.uncu.edu.ar/objetos_digitales/4137/morabito.pdf |
| Zuccardi, *Guía del terroir del Valle de Uco* (edición 04/2024) | https://zuccardiwines.com/wp-content/uploads/2024/05/Zuccardi-Guia-Terroir-Valle-de-Uco-ESP.pdf |
| Fernández Long et al., *Heladas en la Argentina* (Portal de Heladas, FAUBA) | https://heladas.agro.uba.ar/mendoza_3.htm |

## 4. Umbral de helada en floración y cuaje (FDF / INIA, 2016)

**Confirmado en el original (p. 4, sección 1.2):**

- En la vid, **0 °C es la temperatura crítica desde el inicio de la floración hasta el fruto pequeño**.
- En brotación, la temperatura crítica **oscila entre −2 y −4 °C**.
- Las etapas más sensibles son las que van desde el botón floral hasta el fruto pequeño.

Es una guía técnica chilena (regiones de O'Higgins y Maule), no una medición de laboratorio: no da porcentajes de daño. Marca: **con fuente (vid general, Chile)**. Respalda usar 0 °C, o un valor cercano, como umbral de alerta para BBCH 60 a 71.

## 5. Riego por superficie en el río Mendoza (Morábito)

**Confirmado en el original** (resumen, pp. 2-3; Cuadro 8, p. 36). El estudio hizo 101 evaluaciones de campo.

| Dato | Valor |
|---|---|
| Eficiencia de aplicación media del área | **59 %**, calificación "Mala" |
| Eficiencia por método | Surcos sin desagüe 67 %; melgas sin desagüe 69 %; con desagüe 39 % |
| Eficiencia por cultivo | Frutales (incluye vid) 62 %; hortalizas 47 % |
| Eficiencia alcanzable | 61 % (manteniendo la salinidad actual), 71 % (90 % de la producción máxima), 79 % (optimizando el manejo) |
| Eficiencia potencial para la vid (Cuadro 34-a) | 63 % ± 6,3 |

**Láminas de riego por evento (Cuadro 8, mm):**

| Grupo | Lámina neta requerida (dn) | Lámina bruta (db) | Lámina infiltrada | Lámina almacenada |
|---|---|---|---|---|
| Surcos sin desagüe | — | **76** | 76 | 43 |
| Surcos con desagüe | — | **152** | 36 | 28 |
| Melgas sin desagüe | — | 117 | 113 | 66 |
| Cultivos frutícolas (vid, frutales, olivo) | 77 | 117 | 84 | 52 |
| Primavera | 54 | 136 | 78 | 42 |
| Verano | 86 | 103 | 81 | 53 |

**Para el simulador:** un riego por surco sin desagüe aplica unos 76 mm brutos (760.000 L/ha), de los que quedan almacenados unos 43 mm en la zona de raíces. Marca: **con fuente (Mendoza)**. El año de la tesis no figura en el texto extraído; la segunda investigación la fecha en 2003.

## 6. Suelos de Tupungato (Zuccardi, 2024)

**Confirmado en el original (pp. 6-12):**

- En Tupungato la altitud pasa de **900 a 1.800 m en 35 km**.
- Las zonas altas (Gualtallary, San Pablo) tienen **suelos pedregosos con importante carbonato de calcio** (caliche).
- Las texturas mapeadas en el Valle de Uco incluyen: franco arenoso y franco limoso de 80 a más de 150 cm de profundidad; arenosos de 80 a 100 cm; capas de arena de 40 a 70 cm sobre gravas arenosas; y pedregosos con capa de piedra calcárea.

Es una fuente de bodega (mapas propios), útil como descripción. Marca: **con fuente (secundaria)**. Para una parcela ficticia de Tupungato, "franco arenoso" o "pedregoso" son elecciones defendibles.

## 7. Fechas de heladas por estación (Portal de Heladas FAUBA)

**Confirmado en el original.** "Helada meteorológica": mínima ≤ 0 °C en abrigo. "Helada agrometeorológica": mínima ≤ 3 °C en abrigo, que se usa como aproximación de la helada a nivel del cultivo.

| Estación (período) | Umbral | Última helada media | Última helada con 20 % de probabilidad | Última helada más tardía | Días con helada por año | Mínima absoluta anual media |
|---|---|---|---|---|---|---|
| San Rafael Aero (1957-2012) | 0 °C | **16-sep** | 4-oct | 14-nov (2000) | 36 | −6,2 °C |
| San Rafael Aero (1957-2012) | 3 °C | 22-oct | 7-nov | 12-dic (1970) | 85 | −6,2 °C |
| San Martín, Mendoza (1956-2012) | 0 °C | **9-sep** | 22-sep | 4-nov (1992) | 27 | −5,3 °C |
| San Martín, Mendoza (1956-2012) | 3 °C | 2-oct | 26-oct | 4-dic (1971) | 68 | −5,3 °C |
| La Consulta INTA, Valle de Uco (1970-2011) | 0 °C | **1-oct** | 17-oct | 14-nov (1987) | 65 | −7,3 °C |
| La Consulta INTA, Valle de Uco (1970-2011) | 3 °C | 5-nov | 17-nov | 16-dic (2003) | 116 | −7,3 °C |
| Mendoza Aero (1960-2012), referencia | 3 °C | 17-sep | 3-oct | 4-nov (1992) | 63 | −4,6 °C |

La "mínima absoluta anual media" es el promedio, año por año, de la temperatura más baja del año (casi siempre en invierno), no la de septiembre.

**Qué significa para el simulador:**
- Las heladas de primavera son más tardías y frecuentes en el Valle de Uco (La Consulta, como referencia para Tupungato) que en San Rafael, y en San Rafael más que en San Martín.
- Concuerda con las 6 a 8 noches de helada entre septiembre y noviembre: casi todas en septiembre, alguna en octubre y, en Tupungato, posible hasta mediados de noviembre.
- La Consulta está en San Carlos (unos 940 m), no en Tupungato: es la estación con ficha de heladas más cercana del Valle de Uco. Marca para Tupungato: **adaptado**.

## Resumen de la segunda ronda

| Dato | Antes | Ahora | Marca |
|---|---|---|---|
| Umbral de helada en floración y cuaje (BBCH 60-71) | Fragmento | **0 °C**, confirmado en el original | con fuente (vid general, Chile) |
| Umbral en brotación | Concord y Pinot noir | Además, rango de campo de −2 a −4 °C | con fuente (vid general, Chile) |
| Lámina por riego por surco | Resumen | **76 mm** sin desagüe, 152 mm con desagüe | con fuente (Mendoza) |
| Eficiencia del riego | Resumen | 59 % media; 62 % en frutales; 63 % potencial en vid | con fuente (Mendoza) |
| Suelo de Tupungato | Fragmento | Franco arenoso o pedregoso calcáreo | con fuente (secundaria) |
| Última helada por departamento | Solo Mendoza Aero | San Rafael 16-sep; San Martín 9-sep; Valle de Uco (La Consulta) 1-oct | con fuente (FAUBA) |
