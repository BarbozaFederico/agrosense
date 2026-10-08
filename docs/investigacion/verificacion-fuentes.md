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
