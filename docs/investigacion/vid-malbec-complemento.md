> **Documento de trabajo.** Segunda investigación (octubre de 2026), acotada a los datos que el primer informe ([`vid-malbec.md`](vid-malbec.md)) dejó como "supuesto", "adaptado" o "no encontrado". Su tabla final "Reemplazos para el modelo" indica qué valores del primer informe cambian. Los datos leídos en fragmentos, prensa o resúmenes deben confirmarse en la fuente primaria antes de la evaluación.

> **Verificado el 8/10/2026:** ver [`verificacion-fuentes.md`](verificacion-fuentes.md), que corrige las mínimas absolutas del SMN y la humedad de día y de noche, y confirma otros datos. Prevalece sobre este informe donde haya diferencias.

# Segunda investigación: datos faltantes para el simulador de sensores de viñedo (Malbec, Mendoza)

Conseguí con fuente casi todo lo que falta sobre heladas, el coeficiente de cultivo (Kc), la fracción "p", el riego por surco y las hectáreas de Malbec por departamento. Para el Malbec también conseguí dos datos muy útiles: los parámetros propios del modelo de resistencia al frío de WSU (Ferguson et al. 2014) y los grados-día de floración y envero del modelo GFV (Parker et al. 2013). Quedaron sin fuente directa los grados-día de cada etapa BBCH intermedia, la ETo mensual por zona, la capacidad de campo medida en Mendoza, el riego por departamento del CNA 2018, la humedad relativa de día y de noche, y la verificación de las normales del SMN: el PDF del SMN bloqueó la descarga automática.

## TL;DR

- **Heladas:** usá para el Malbec un umbral de daño en tejido verde de **−1,2 °C** (WSU: "Frost Cold Tolerance-Post Budbreak" de 29,8 °F para Malbec; es el Hc,min de Ferguson et al. 2014). Para la brotación usá la tabla de la uva Concord (FAO Tabla 4.8, de Proebsting): **10 % de daño a −3,9 °C y 90 % a −8,9 °C**. Para la vid vinífera, la referencia de 50 % es el Pinot noir (Gardea 1987): **−2,2 °C** en brotación.
- **Diferencia entre abrigo y brote:** en noches de helada calmas y despejadas, el brote a 0,8–1,2 m está **unos 1 a 3 °C más frío** que el abrigo. Ese número junta el gradiente vertical (de 0,17 a 0,36 °C cada 10 cm, Trought et al. 1999) y el enfriamiento por radiación de la yema (de 2 a 3 °C, mismo informe). La mínima ocurre **al amanecer**, y después de las primeras 2 horas tras la puesta del sol la temperatura baja **menos de 1 °C por hora** (FAO, Snyder y de Melo-Abreu 2005).
- **Agua y fenología:** la FAO-56 confirma para la vid de vino un **Kc de 0,30, 0,70 y 0,45** (Tabla 12) y una **p de 0,45** (Tabla 22). Un riego por surco en el río Mendoza aplica entre **76 y 152 mm brutos por riego**, con una **eficiencia media del 59 %** (Morábito, Mirábile y Salatino 2007, *Ingeniería del Agua*, 101 evaluaciones). Para el Malbec ("Cot"), el modelo GFV da **F* = 1306 °C·día en floración y 2658 °C·día en envero** (base 0 °C). Con esos valores se puede chequear que los 712 grados-día de Zapata son coherentes.

## Resumen inicial

**Qué se encontró (con fuente leída en el original):**
- Ferguson et al. 2014 (AJEV 65:59-71), texto completo: parámetros del Malbec y temperaturas letales por etapa (Tabla 2).
- Página de WSU sobre resistencia al frío: tolerancia del Malbec después de la brotación y umbrales en hinchazón de yema de otras variedades.
- Parker et al. 2013 (Agricultural and Forest Meteorology 180:249-264), texto completo: F* del Cot (Malbec).
- FAO-56, capítulos 6 y 8 en HTML: Tablas 12 y 22.
- Rodríguez et al. 1999 (UNCuyo/INTA): fechas fenológicas medias del Malbec en Chacras de Coria y superficie de 1995 por departamento.
- Morábito et al. (INA/UNCuyo): láminas y eficiencia del riego por surco.
- FAO, *Frost Protection* Vol. 1 (Tabla 4.8, capítulos 1, 2 y 7), y Trought et al. 1999 (Nueva Zelanda). Estos dos los leyó el subagente.

**Qué se encontró solo en resúmenes o fragmentos de búsqueda (no en el PDF completo):**
- INV, *Informe de Variedades Malbec 2025*: el PDF bloqueó la descarga automática. Las hectáreas salen del texto que muestra el buscador y coinciden con la nota del Diario San Rafael.
- Heladas en Mendoza Aero, del Portal de Heladas FAUBA.
- Zonificación de heladas del INTA Rama Caída, vía prensa.
- Proporción de parral y espaldero del INV, vía Diario de Cuyo.

**Qué NO se encontró:**
- Grados-día de BBCH 11, 15, 53, 57, 61, 69, 71, 75, 77-79 y 89 para el Malbec.
- Grados-día hasta la brotación para el Malbec.
- Fecha observada de envero en el Este.
- ETo mensual por zona.
- Capacidad de campo y punto de marchitez medidos en Mendoza.
- Riego por departamento del CNA 2018.
- Densidad de plantación y sistema de conducción del Malbec por departamento.
- Humedad relativa diurna y nocturna, y punto de rocío.
- Un índice de riesgo de helada publicado para la vid con cortes numéricos (incluido el IPH).
- La verificación de las normales del SMN 1991-2020: el repositorio del SMN bloqueó la lectura automática.

**Valores del primer informe que cambian:**
1. El umbral de daño en tejido verde pasa de "0 °C o −1 °C" a **−1,2 °C**, específico del Malbec.
2. La brotación deja de estar "sin dato": pasa a 10 % / 90 % = −3,9 / −8,9 °C (Concord) y 50 % = −2,2 °C (Pinot noir).
3. El brote ya no se modela a la misma temperatura que el abrigo: queda entre 1 y 3 °C más frío en noches de helada calmas.
4. Se fija p = 0,45 y Kc = 0,30 / 0,70 / 0,45.

## 1. Grados-día de las etapas intermedias

### 1a) Grados-día por código BBCH

**No encontré** grados-día publicados para el Malbec por código BBCH intermedio (11, 15, 53, 57, 61, 69, 71, 75, 77-79, 89).

Lo más cercano son los modelos chilenos de Ortega-Farías et al. (2002, Talca, Cabernet Sauvignon y Chardonnay; R² superior a 0,88; el Cabernet Sauvignon sumó 1558 grados-día en base 10 °C hasta la cosecha del 26/03/99) y de Verdugo-Vásquez, Gutiérrez-Gamboa, Valdés-Gómez y Acevedo-Opazo (2025, *Agrociencia Uruguay* 29, Valle del Maule, Cabernet Sauvignon; R² > 0,98 y desvío de 1,0 a 1,84 unidades fenológicas). Ambos relacionan la escala fenológica con los grados-día (base 10 °C) mediante la ecuación monomolecular de Mitscherlich. Solo leí los resúmenes: los coeficientes de la ecuación no estaban visibles.

**Propuesta para el modelo (marcada "supuesto"):** repartir los grados-día de forma lineal dentro de cada tramo que ya tiene fuente:
- Brotación (BBCH 09) a floración (BBCH 65): 260 grados-día (Zapata et al. 2017).
- Floración (BBCH 65) a envero (BBCH 81-83): 712 grados-día (Zapata et al. 2017).

| BBCH | Cómo se ve la planta | Regla propuesta | Marca |
|---|---|---|---|
| 11 | Primera hoja desplegada | Proporción del tramo 09→65 según el orden de la escala | supuesto |
| 15 | 5 hojas desplegadas | Ídem | supuesto |
| 53 | Racimos (inflorescencias) bien visibles | Ídem | supuesto |
| 57 | Flores separadas en el racimo | Ídem | supuesto |
| 61 / 65 / 69 | Inicio / plena / fin de floración | 65 = 260 grados-día desde la brotación | con fuente (solo 65) |
| 71 | Cuaje: aparecen las bayitas | Proporción del tramo 65→81 | supuesto |
| 75 | Bayas del tamaño de una arveja | Ídem | supuesto |
| 77-79 | Racimo que se cierra | Ídem | supuesto |
| 81-83 | Envero: la baya cambia de color | 712 grados-día desde la floración | con fuente |
| 89 | Baya madura para cosecha | Sin dato en base 10; ver GFV más abajo | no encontrado |

**Dato complementario (Malbec en otro lugar: Francia, varios sitios, sobre todo de clima templado):** Parker et al. 2013, Tablas 1 y 2, modelo GFV. Este modelo suma grados-día con base 0 °C desde el día 60 del año (el 1 de marzo en el hemisferio norte). Para el "Cot" (Malbec) da:
- **Floración: F* = 1306 °C·día** (4 sitios, 31 observaciones, error de 4,4 días, eficiencia EF de 0,74).
- **Envero: F* = 2658 °C·día** (2 sitios, 13 observaciones, error de 6,0 días, EF de 0,60).

**Adaptación a Mendoza:** el 1 de marzo del norte equivale al **1 de septiembre** del sur. El tramo de floración a envero da 2658 − 1306 = **1352 °C·día en base 0**. Para pasarlo a base 10 hay que restar 10 °C por cada día del tramo. Con un tramo de unos 64 días quedan unos 712 grados-día en base 10. Esa duración es compatible con una floración a mediados de noviembre y un envero a mediados de enero. Este chequeo es un cálculo mío, no está publicado.

### 1b) Desde cuándo empezar a contar los grados-día

- En Chile, el trabajo de Jorquera-Fontena y Orrego-Verdugo (*Agrociencia* 44(4):427-435, 2010, sur de Chile, cv. Gewürztraminer, escala BBCH) cuenta los grados-día **desde un biofix del 1 de septiembre** hasta la cosecha. El biofix es la fecha fija desde la que se empieza a sumar.
- El INIA de Chile (capítulo 8, "Grados día y fenología en vides") usa base 10 °C. Indica que la fecha de inicio depende de la zona agroclimática.
- El modelo GFV empieza el 1 de marzo en el norte, que equivale al 1 de septiembre en el sur (adaptado).
- **No encontré** cuántos grados-día necesita el Malbec hasta la brotación (BBCH 09). Como dato de referencia, Rodríguez et al. 1999 (UNCuyo/INTA, Chacras de Coria, Luján de Cuyo) dan la **brotación media del Malbec el 29 de septiembre**.
- **Recomendación:** empezar a contar el 1 de septiembre y fijar la brotación por observación, o con el modelo de Ferguson (ver 2c). No conviene usar grados-día para predecirla.

### 1c) Fechas observadas y validación del tramo de 712 grados-día

| Fuente | Lugar | Dato | Nivel |
|---|---|---|---|
| Rodríguez et al. 1999, *Revista FCA UNCuyo* XXXI(2), p. 85+ | Chacras de Coria (Luján) | Brotación 29/IX; floración 10/XI; maduración 5/III; amarilleo de hojas 4/V | Malbec Mendoza (PDF leído; el envero no aparece en la parte leída) |
| INTA EEA Mendoza (poda tardía, 2017-2020) | Luján de Cuyo, goteo | La poda tardía retrasó la brotación 11, 18 y 30 días; el retraso siguió hasta el envero, pero la cosecha no siempre se retrasó | Malbec Mendoza (resumen) |
| Trivento (prensa, 2025) | Mendoza | La vendimia 2025 empezó el 20/I y terminó el 8/IV | Malbec Mendoza (prensa, fuente débil) |
| La Celia (prensa, 2025) | Sur del Valle de Uco | La madurez de azúcares se adelantó 17 días respecto de 2024 y 14 días respecto del promedio 2019-2024 | Malbec Mendoza (prensa) |
| Altos Las Hormigas, reporte 2025 | Mendoza | Floración adelantada 2 semanas; cosecha desde el 2/II | Malbec Mendoza (reporte de bodega) |

**Envero en el Este de Mendoza:** no encontré ninguna fecha observada. Mi estimación es que cae entre fines de diciembre y enero. Es una estimación, no un dato. Se calcula así: floración cerca del 10/XI, más 712 grados-día a razón de 12 a 15 grados-día por día, según la temperatura media de diciembre y enero del SMN que ya tenés. Eso da entre 47 y 60 días, o sea, entre el 27/XII y el 9/I. Para el modelo: **dejá que el envero salga del cálculo de grados-día y no lo fijes a mano**.

### 1d) Modelos propios del Malbec

No encontré modelos de temperatura base del Malbec hechos por UNCuyo, el INTA o el INV. El único con parámetros publicados por variedad es el de Ferguson et al. 2014 (punto 2c). Ese modelo usa un umbral de frío de 10 °C para todas las variedades.

## 2. Temperaturas críticas de helada

### 2a) Brotación (BBCH 07-09)

**Sobre el documento original:** abrí la ficha del WSU EB1615 (Proebsting, Brummund y Clore, junio de 1991, 2 páginas, handle 2376/6755), pero no pude extraer el PDF. Los mismos valores, tomados de Proebsting et al. (1978), aparecen en dos documentos que sí leí completos:
- FAO, *Frost Protection* Vol. 1 (Snyder y de Melo-Abreu 2005), **Tabla 4.8**, con la nota "30 minutes at the indicated temperature is expected to cause 10 percent and 90 percent kill".
- Ferguson et al. 2014, **Tabla 2**.

| Etapa (cómo se ve) | Concord 10 % (°C) | Concord 90 % (°C) | Pinot noir 50 % (°C), Gardea 1987 | Fuente / Nivel |
|---|---|---|---|---|
| Primera hinchazón (la yema se agranda) | −10,6 | −19,4 | — | FAO T4.8 / vid general (V. labruscana) |
| Hinchazón avanzada / "woolly bud", BBCH 03-05 (yema algodonosa) | −6,1 | −12,2 | −3,4 | FAO T4.8 y Ferguson T2 / vid general y vid similar |
| Brotación, BBCH 07-09 (se ve la punta verde) | **−3,9** | **−8,9** | **−2,2** | ídem |
| Primera hoja, BBCH 11 | −2,8 | −6,1 | −2,0 | ídem |
| Segunda hoja, BBCH 12 | −2,2 | −5,6 | −1,7 | ídem |
| Tercera hoja, BBCH 13 | −2,2 | −3,3 | — | FAO T4.8 |
| Cuarta hoja, BBCH 14 | −2,2 | −2,8 | −1,2 | ídem |

Los valores de Concord para "hinchazón de yema" y "1 a 4 hojas" que ya tenías coinciden con esta tabla.

**Valor de 50 % para el modelo (adaptado):** usar el de Pinot noir, −2,2 °C en brotación. Ferguson et al. lo usan para todas las *V. vinifera*. La Concord (*V. labruscana*) es más resistente, así que sus valores de 90 % sobrestiman la resistencia del Malbec.

**Umbrales medidos en vinífera por WSU (Prosser, EE. UU., clima semiárido):**
- Cabernet Sauvignon en hinchazón: sin daño hasta 25 °F (−3,9 °C).
- Merlot en hinchazón: daño leve a 25 °F (−3,9 °C) y serio a 23 °F (−5,0 °C).
- Chardonnay en hinchazón y brotación: daño leve a 27 °F (−2,8 °C); yemas muy afectadas a 24 °F (−4,4 °C).

**Efecto de la humedad sobre la yema:** según Johnson y Howell (1981), citados por Trought et al. 1999 (Tabla 4), una yema mojada se daña a temperaturas más altas que una seca. Valores de 50 % de daño (T50) en Concord, mojada / seca:
- Hinchazón completa: −3,5 / −7,0 °C.
- Brotación: −3,0 / −6,0 °C.

### 2b) Racimos visibles (BBCH 53-57), floración (60-69) y cuaje (71)

**No encontré** tablas de 10 % y 90 % medidas en vid para estas etapas: la FAO Tabla 4.8 termina en la "cuarta hoja". Lo que sí hay:
- FAO Tabla 4.8 (Krewer 1988): "New growth" (crecimiento nuevo) a **−1,1 °C**, sin porcentaje de daño.
- FAO Tabla 4.4 (Whiteman 1957): temperatura de congelamiento de *V. vinifera*: fruto −2,7 °C, tallo −2,0 °C.
- Fundación para el Desarrollo Frutícola (Chile): para la vid, **0 °C es crítico** desde el inicio de la floración hasta el fruto. Solo leí un fragmento.
- Ferguson et al. 2014 y WSU: tejido verde del Malbec después de la brotación, **−1,2 °C** (29,8 °F).

**Para el modelo (adaptado):**
- BBCH 53-57: −1,2 °C.
- BBCH 60-71: entre 0 y −0,5 °C.

La FAO aconseja usar en el campo valores **algo más altos** que los de laboratorio, porque la yema y la flor están más frías que el aire del abrigo.

### 2c) Resistencia al frío del Malbec (Ferguson et al. 2014, Tabla 4; datos de Prosser, Washington, 46,3° N, clima semiárido continental)

| Parámetro | Malbec |
|---|---|
| Tth,endo / Tth,eco (umbral de temperatura en dormición profunda / dormición final) | 14,0 / 4,0 °C |
| ka,endo / kd,endo (velocidad de endurecimiento / desendurecimiento en dormición profunda) | 0,10 / 0,06 |
| ka,eco / kd,eco (ídem en dormición final) | 0,08 / 0,08 |
| Hc,initial (resistencia al inicio del otoño) | −11,5 °C |
| Hc,max (resistencia máxima en invierno) | −25,1 °C |
| Hc,min (resistencia mínima: tejido verde) | −1,2 °C |
| θ (exponente que acelera el desendurecimiento cerca de la brotación) | 7 |
| EDB (suma de frío que marca el fin de la dormición profunda) | −400 °C·día (umbral de frío de 10 °C) |
| Ajuste del modelo | n = 68; r² = 0,96; error (RMSE) = 1,9 °C |

**Cómo se usa:** el modelo corre con la temperatura media diaria. Predice la brotación el primer día en que Hc ≥ −2,2 °C. En Washington arranca el día 250 del año (7 de septiembre).

**Adaptado a Mendoza:** desplazá el calendario 6 meses, con inicio cerca del 7 de marzo. Como la temporada simulada empieza el 1 de septiembre, lo práctico es usar solo Hc,min = −1,2 °C como umbral de daño del tejido verde.

## 3. Diferencia entre el abrigo meteorológico y la altura de los brotes

| Dato | Valor | Fuente | Nivel |
|---|---|---|---|
| El brote está más frío que el aire en noches calmas | Yemas **2 a 3 °C** más frías que el aire; con viento de 3 a 4 km/h el efecto desaparece | Trought, Howell y Cherry 1999, *Practical Considerations for Reducing Frost Damage in Vineyards*, Lincoln University (Nueva Zelanda), sección 2 (es una estimación, no una serie medida) | vid general (Nueva Zelanda, templado) |
| Superficie de la planta frente al aire | **1 a 3 °C** más fría | Wine Australia, *Improved Frost Management in the Goulburn & Yarra Valleys* (cita a Trought) | vid general (Australia) |
| Abrigo frente a pasto, mínimas de septiembre | 2,4 a 5,1 °C (Marlborough 2,4; Cromwell 5,1); gradiente de **0,17 a 0,36 °C cada 10 cm** | Trought et al. 1999, Tabla 1 | vid general (Nueva Zelanda) |
| Inversión entre 1,3 m y 14 m | 1,4 a 4,1 °C; típica de 3 a 5 °C | Trought et al. 1999, Tabla 2 | vid general |
| Inversión entre 2 y 10 m | ≥1,5 °C en la mayoría de las noches de helada | FAO *Frost Protection* Vol. 1, cap. 2 | vid general |

**Adaptado:** de 1,5 m (abrigo) a 1,0 m (brote) hay 50 cm. Con el gradiente de 0,17 a 0,36 °C cada 10 cm, el brote estaría **entre 0,9 y 1,8 °C más frío** por la altura. Si la yema además pierde calor por radiación, la diferencia total sería de unos 1 a 3 °C. Este cálculo es mío.

**Para el simulador:** T_brote = T_abrigo − Δ.
- Δ = 2 °C en noches despejadas y con viento menor a 1 m/s.
- Δ = 0,5 °C con viento o cielo nublado.

Este valor de Δ es un supuesto basado en las fuentes de arriba. No encontré mediciones en viñedos de Mendoza.

## 4. Índice de riesgo de helada

**No encontré** el IPH (índice de peligrosidad de heladas) ni otro índice publicado para la vid con cortes numéricos. Esto es lo que sí tiene fuente para armarlo:
- Las temperaturas críticas por etapa (punto 2).
- La humedad: la yema mojada se daña a temperaturas más altas (Johnson y Howell 1981). El ministerio de agricultura de Ontario (OMAFRA, Canadá) señala que el punto de rocío, la temperatura de la superficie y las condiciones previas influyen en el daño.
- La duración: los valores de la FAO suponen 30 minutos de exposición.
- La FAO recomienda **activar la protección a temperaturas del aire más altas** que las de la tabla.

**Propuesta de índice (adaptado o supuesto, para defender como diseño propio):**

| Nivel | Condición, con T_brote = T_abrigo − Δ y Tc = temperatura crítica de la etapa |
|---|---|
| Bajo | T_brote > Tc + 2 °C |
| Medio | Tc < T_brote ≤ Tc + 2 °C, o punto de rocío < −2 °C con cielo despejado y calma |
| Alto | T_brote ≤ Tc durante ≥30 min (base de la Tabla 4.8 de la FAO), o T_brote ≤ Tc + 1 °C con yema mojada |

La humedad de suelo puede usarse como modificador menor: según la FAO, un suelo húmedo y descubierto guarda más calor, y una cubierta de pasto hace el aire entre 0 y 0,5 °C más frío.

## 5. Suelo y humedad de suelo

### 5a) Textura

| Zona | Textura descrita | Fuente | Calidad |
|---|---|---|---|
| Valle de Uco (Tupungato y vecinos) | Franco arenoso y franco limoso, de 80 a más de 150 cm de profundidad; pedregoso con capa calcárea | Zuccardi, *Guía del terroir del Valle de Uco* (2024) | bodega (mapas propios) |
| Valle de Uco, zonas altas | Pedregosos, poco fértiles, cantos rodados con arena gruesa y algo de limo, muy permeables | INV, informe regional Valle de Uco 2021 (vía Los Andes) | resumen de prensa |
| Este (La Paz, cerca de San Martín) | Franco arenoso | Vinecol (ficha comercial) | débil |
| San Rafael | No encontrado | — | — |

No pude acceder a cartas de suelo del INTA.

### 5b) Capacidad de campo y punto de marchitez

**No verificados en esta ronda.** La fuente estándar es la FAO-56, Tabla 19, en el capítulo 8: contiene los valores típicos por textura, pero no los extraje. **No uses valores sin antes leer esa tabla o la calculadora de Saxton y Rawls (2006).**

### 5c) Verificación en la FAO-56 (Allen et al. 1998; leído en el HTML oficial de fao.org, capítulos 6 y 8)

- **Tabla 12, uva de vino:** Kc ini = **0,30**; Kc mid = **0,70**; Kc end = **0,45**; altura de 1,5 a 2 m. Los valores corresponden a un clima subhúmedo (humedad relativa mínima cercana al 45 %, viento de 2 m/s). Uva de mesa o pasa: 0,30 / 0,85 / 0,45.
- **Tabla 22, uva de vino:** raíz máxima de **1,0 a 2,0 m**; **p = 0,45**, válida para una ET de unos 5 mm/día. Uva de mesa: 0,35.
- **Ajuste de p (FAO-56):** p = p_tabla + 0,04 × (5 − ETc).
- **Ajuste para Mendoza (adaptado):** como Mendoza es más seca (humedad relativa mínima menor al 45 %), la FAO-56 manda corregir el Kc mid y el Kc end con su ecuación 62. Hacé la corrección; no uses 0,70 sin ajustar.
- La UC Davis (curso de riego, Napa 2019) propone para la uva de vino con densidad media: 0,30 / 0,70 / 0,55.

### 5d) Humedad medida con sensores en Mendoza

No encontrada.

## 6. Riego

### 6a) Sistema de riego por departamento

**No encontré** datos del CNA 2018 por departamento. Lo que sí hay:
- Según José Morábito (INA), citado por Diario Uno (12/06/2011), solo cerca del 15 % de las hectáreas cultivadas de Mendoza usa riego presurizado, y "El 90% de la superficie cultivada con riego presurizado corresponde a la vid".
- Schilardi, Rearte, Martín y Morábito (INA, *Diagnóstico prospectivo del desempeño de métodos de riego en la provincia de Mendoza*) indican que los surcos o melgas "representan el 90% de la superficie bajo riego (INDEC, 2002)" y el goteo el 8 %; el dato es de toda la superficie regada, no solo de viñedos.
- Un relevamiento del Consejo Federal de Inversiones (CFI) señala que los viñedos nuevos se diseñan con espaldero y riego por goteo.

### 6b) Lámina y eficiencia del riego por surco

| Dato | Valor | Fuente | Nivel |
|---|---|---|---|
| Lámina bruta por riego, surco sin desagüe | 76 mm | Morábito et al., "Desempeño del riego por superficie en el área de riego del Río Mendoza" (INA/UNCuyo) | vid y otros cultivos, Mendoza |
| Lámina bruta por riego, surco con desagüe | 152 mm (infiltra solo 36 mm) | ídem | ídem |
| Lámina bruta media, surcos | 90 mm (tiempo medio de 144 min) | "Actualización de los parámetros característicos de riego…", *Agronomía y Ambiente* (FAUBA) | Mendoza |
| Eficiencia de aplicación media | **59 %** ("Mala"); alcanzable: 61 %, 71 % y 79 % | Morábito, Mirábile y Salatino 2007, *Ingeniería del Agua* 14:199-213 (101 evaluaciones); calificación "Mala" y 61 % alcanzable según la tesis de Morábito (2003, UNCuyo) | Mendoza |
| Infiltración básica | 4,34 a 6,23 mm/h | *Agronomía y Ambiente* | Mendoza |
| Goteo en Malbec, temporada completa | 700 mm de lámina bruta | De Lorenzi et al. (INA), Las Compuertas, Luján | Malbec Mendoza |

**Conversiones:**
- 90 mm = 900 m³/ha = 900.000 L/ha.
- Con 4.000 plantas/ha serían 225 L por planta y por riego. La densidad de 4.000 plantas/ha es un **supuesto**: no encontré la densidad real.

### 6c) ETo mensual

No encontrada en esta ronda.

## 7. Cultivo

### 7a) Conducción y densidad

| Dato | Valor | Fuente | Nivel |
|---|---|---|---|
| Proporción por sistema de conducción (superficie con vid) | Parral 45 %, espaldera alta 44 %, espaldera baja 11 % | INV, simulador de costos (vía Diario de Cuyo, 2016) | vid Mendoza |
| Parral en Mendoza a lo largo del tiempo | 55 % (1991) y 51 % (2004) | Richard-Jorba (CONICET), con datos del INV | vid Mendoza |
| Rendimiento de referencia | Parral cuyano 35.000 kg/ha; espaldero 18.000 kg/ha | Battistella (análisis de inversión, 2017) | vid Mendoza |
| Malbec por departamento y densidad (plantas/ha) | **No encontrado** | — | — |

Para un Malbec de calidad, el espaldero es lo más defendible, pero esto es una inferencia.

### 7b) Tamaño de viñedo y de cuartel

- Tamaño medio de viñedo: **15,3 ha en el Valle de Uco** y **9,8 ha en el promedio provincial** (INV 2021, vía Los Andes).
- INV, *Informe anual de superficie 2025*: San Martín tiene 25.417 ha y 2.755 viñedos; San Rafael, 10.739 ha y 2.065 viñedos; Tupungato, 667 viñedos.
- Cuenta mía: unas 9,2 ha por viñedo en San Martín y 5,2 ha en San Rafael.
- Tamaño de cuartel: no encontré un dato estadístico. Monteviejo (Valle de Uco) trabaja con parcelas de 1 a 3 ha.

## 8. Forma de las curvas diarias

### 8a) Curva de temperatura del día

- **Modelo:** Parton y Logan (1981, *Agricultural Meteorology* 23:205-216) usan una senoidal truncada durante el día y una exponencial durante la noche. Lo ajustaron para el aire a 150 cm en una pradera semiárida de Colorado.
- **Parámetros publicados en implementaciones del modelo:**
  - APSIM: A = 1,5 h (atraso de la máxima respecto del mediodía), B = 4 (velocidad de enfriamiento nocturno), C = 1 h (atraso de la mínima respecto del amanecer).
  - TrenchR (promedio de 5 sitios de Carolina del Norte, Wann et al. 1985): α = 2,59; β = 1,55; γ = 2,2.
- **Para un clima árido (adaptado):** máxima entre 1,5 y 2,5 h después del mediodía solar; mínima cerca del amanecer. No encontré parámetros calibrados en Mendoza.

### 8b) Enfriamiento en noches de helada (FAO *Frost Protection* Vol. 1, cap. 1, Fig. 1.4)

- Ejemplo en un nogal de California: la temperatura cayó unos 10 °C en la primera hora después de que la radiación neta se volvió negativa.
- Desde 2 horas después de la puesta del sol hasta el amanecer, bajó **menos de 1,0 °C por hora**.
- La mínima se da **al amanecer**.

### 8c) Humedad relativa y punto de rocío

No encontrados en esta ronda.

### 8d) Última helada

| Lugar | Dato | Fuente |
|---|---|---|
| Mendoza Aero, helada agrometeorológica (≤3 °C en abrigo), 1960-2012 | Última helada en promedio el **17/IX**; con 20 % de probabilidad el 3/X; la más tardía el 4/XI (1992); 63 días con helada al año | Portal de Heladas FAUBA (Fernández Long et al.) |
| San Rafael y General Alvear, 2010-2020 | Última helada entre mediados y fines de septiembre; en algunas zonas hasta comienzos o mediados de octubre | INTA Rama Caída, zonificación (vía Diario San Rafael) |
| Mendoza, período de vigilancia | 1/IX al 15/XI | Dirección de Contingencias Climáticas (vía prensa) |

Faltan las fichas de San Rafael Aero y San Martín del Portal FAUBA.

## 9. Verificaciones en la fuente original

- **SMN, normales 1991-2020:** el PDF existe en repositorio.smn.gob.ar (handle 20.500.12160/2506) e incluye San Rafael Aero y San Martín, pero bloqueó la lectura automática. **No verificado.**
- **INV, *Informe de Variedades Malbec 2025* (datos de 2024):** también bloqueó la descarga. Fragmento leído:

| Departamento | Malbec (ha) | % del Malbec provincial | Vid total del departamento (ha) | % de Malbec en el departamento |
|---|---|---|---|---|
| Tupungato | 5.042 | 12,6 | 10.587 | 47,6 |
| San Rafael | 2.191 | 5,5 | 11.478 | 19,1 |
| San Martín | 1.456 | 3,7 | 25.847 | 5,6 |

Mendoza tiene 39.856 ha de Malbec (84,7 % del país) y el país 47.064 ha. No pude ver si el informe trae sistema de conducción o densidad.

## Reemplazos para el modelo

| Dato | Valor anterior (supuesto) | Valor nuevo | Fuente (con página o tabla) | Nivel | Marca |
|---|---|---|---|---|---|
| Daño en tejido verde | 0 / −1 °C | −1,2 °C | Ferguson et al. 2014, Tabla 4; WSU (29,8 °F) | Malbec otro lugar (EE. UU.) | con fuente |
| Brotación, 10 % / 90 % | sin dato | −3,9 / −8,9 °C | FAO Frost Prot. Vol. 1, Tabla 4.8 (Proebsting) | vid general | con fuente |
| Brotación, 50 % | sin dato | −2,2 °C | Ferguson 2014, Tabla 2 (Gardea 1987) | vid similar | adaptado |
| Racimos visibles (BBCH 53-57) | sin dato | −1,2 °C | Ferguson 2014; FAO T4.8 ("new growth" −1,1) | vid general | adaptado |
| Floración y cuaje (BBCH 60-71) | sin dato | 0 a −0,5 °C | FDF Chile (fragmento) | vid general | adaptado |
| T_brote − T_abrigo | 0 °C | −2 °C en calma (−0,5 °C con viento) | Trought et al. 1999, sección 2 y Tabla 1 | vid general (Nueva Zelanda) | adaptado |
| Hora de la mínima | — | Amanecer | FAO Frost Prot. Vol. 1, cap. 1-2 | vid general | con fuente |
| Enfriamiento nocturno | — | <1 °C/h desde 2 h después de la puesta | FAO Frost Prot., Fig. 1.4 | vid general | con fuente |
| Inicio de los grados-día | — | 1 de septiembre | Jorquera-Fontena y Orrego-Verdugo 2010 (Chile); GFV adaptado | vid similar | adaptado |
| Floración y envero del Malbec (base 0) | — | 1306 / 2658 °C·día | Parker et al. 2013, Tablas 1-2 | Malbec otro lugar (Francia) | con fuente |
| Etapas BBCH intermedias | — | Reparto lineal dentro de los tramos de 260 y 712 grados-día | — | — | supuesto |
| Kc vid | — | 0,30 / 0,70 / 0,45 | FAO-56, Tabla 12 | vid general | con fuente |
| p | — | 0,45 (ajustar con la ETc) | FAO-56, Tabla 22 | vid general | con fuente |
| Lámina por riego por surco | — | 76-152 mm (media 90 mm) | Morábito et al.; *Agronomía y Ambiente* | vid Mendoza | con fuente |
| Eficiencia del surco | — | 59 % | Morábito, Mirábile y Salatino 2007, *Ingeniería del Agua* 14:199-213 | vid Mendoza | con fuente |
| Proporción parral / espaldero | — | 45 % / 55 % | INV (vía prensa, 2016) | vid Mendoza | con fuente |
| Tamaño de viñedo | — | 15,3 ha (Uco); 9,8 ha (provincia) | INV 2021 | vid Mendoza | con fuente |
| Última helada (Mendoza Aero, ≤3 °C) | — | 17/IX (20 %: 3/X) | Portal FAUBA | Mendoza | con fuente |
| Malbec ha 2024 | — | Tupungato 5.042; San Rafael 2.191; San Martín 1.456 | INV, *Informe Malbec 2025* | Malbec Mendoza | con fuente |
| Capacidad de campo y punto de marchitez, ETo, humedad relativa | — | No encontrado | — | — | supuesto |

## Glosario

- **BBCH:** escala internacional que asigna un número a cada etapa de la planta (09 = brotación, 65 = plena floración, 81 = inicio del envero).
- **Grados-día:** suma diaria de cuánto supera la temperatura media a una base (10 °C en tu modelo); mide el "calor acumulado".
- **F*:** grados-día necesarios para llegar a una etapa en el modelo GFV (en base 0 °C).
- **LT10, LT50, LT90:** temperatura que mata al 10 %, 50 % y 90 % de las yemas.
- **Hc (resistencia al frío):** temperatura letal estimada de la yema en un día dado.
- **Envero:** momento en que la uva verde empieza a tomar color.
- **Inversión térmica:** noche en que el aire de abajo está más frío que el de arriba.
- **Kc:** número que convierte la evaporación de referencia (ETo) en el consumo de agua de la vid.
- **p:** fracción del agua disponible del suelo que la planta puede usar antes de sufrir estrés.
- **Eficiencia de aplicación:** porcentaje del agua regada que queda en la zona de las raíces.

## Caveats

- Varios datos de Mendoza (INV 2025, conducción, heladas de San Rafael, cosecha 2025) vienen de fragmentos o de la prensa, no del PDF completo. En la evaluación conviene mostrarlos como "verificados de forma secundaria".
- Los valores de helada de Concord corresponden a otra especie (*V. labruscana*), más resistente al frío. Los de Ferguson para el Malbec se obtuvieron en Washington.
- La diferencia entre el abrigo y el brote viene de Nueva Zelanda y de una estimación de autores, no de una serie medida en Mendoza.
