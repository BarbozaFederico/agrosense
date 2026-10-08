> **Documento de trabajo.** Informe de investigación profunda (octubre de 2026) sobre el Malbec en Mendoza, usado para parametrizar el simulador y la colección `variedades` ([ADR-004](../decisions/ADR-004-temporada-malbec.md)). Cada valor lleva su marca: "con fuente", "adaptado" o "supuesto". Los datos de fuentes secundarias (por ejemplo, la reproducción en Wikipedia de las normales del SMN o la tabla del INV leída en un buscador) deben confirmarse en la fuente primaria antes de la evaluación.

> **Verificado el 8/10/2026:** ver [`verificacion-fuentes.md`](verificacion-fuentes.md), que corrige las mínimas absolutas del SMN y la humedad de día y de noche, y confirma otros datos. Prevalece sobre este informe donde haya diferencias.

# Malbec en Mendoza: parámetros respaldados para un simulador de sensores de viñedo (San Rafael, Tupungato y San Martín)

Hay fuentes publicadas para casi todos los parámetros del simulador, pero los grados-día por etapa no tienen un valor medido en Mendoza: el mejor dato del Malbec viene de un estudio de 23 años en Washington (EE.UU.), y conviene usarlo como modelo inicial y corregirlo con las observaciones manuales que ya prevé el proyecto. El clima mensual sí tiene buena base: el SMN tiene normales 1991-2020 para San Rafael Aero y San Martín, y la DACC tiene la estación El Peral (Tupungato, 1.300 m) con promedios 1998-2012. Los umbrales de helada por etapa vienen de tablas de la FAO y de la Universidad Estatal de Washington (WSU), medidas en otra variedad de uva (Concord). Varios datos de manejo no los encontré en fuentes primarias: el sistema de riego por departamento, la densidad de plantación, el tamaño de parcela y la humedad de suelo en % para Mendoza. En esos casos los marco como "adaptado" o "supuesto".

## TL;DR (resumen ejecutivo)

- **Grados-día:** usá temperatura base 10 °C con promedio diario, (Tmáx + Tmín) / 2. Acumulá desde el 1 de septiembre hasta la brotación y después reiniciá la cuenta desde la brotación. Para el Malbec, el estudio de Zapata et al. (2017) da 260 grados-día de brotación a floración y 712 de floración a envero (base 10 °C, Washington). No hay datos Malbec-Mendoza para las etapas intermedias: las propongo como supuestos y las corregís con observaciones.
- **Heladas:** el brote verde se daña cerca de −2 °C. La tabla FAO/WSU (uva Concord) da, para 10% y 90% de daño: hinchazón temprana −10,6 / −19,4 °C; hinchazón tardía −6,1 / −12,2 °C; primera hoja −2,8 / −6,1 °C; segunda hoja −2,2 / −5,6 °C; tercera hoja −2,2 / −3,3 °C; cuarta hoja −2,2 / −2,8 °C. Los valores del IDR + DACC (−1,1 °C y −0,6 °C) son de **frutales** y sus letras D, F y H **no** son las mismas letras de la vid. Sirven solo como margen conservador.
- **Clima y riego:** San Martín es la zona más cálida y seca (lluvia septiembre-marzo de 220,1 mm). San Rafael es intermedia pero más lluviosa (282,2 mm). Tupungato/El Peral es la más fresca: en septiembre su máxima media es 18,4 °C, contra 22,2 °C en San Martín. En Mendoza predomina el riego por superficie: según Schilardi (INA), que cita al INDEC 2002, los surcos y melgas "representan el 90% de la superficie bajo riego", y el goteo se estima en unas 40.000 ha, cerca del 14%. Los turnos del DGI en el Valle de Uco rotan cada 6 a 9 días (lo más común, 7 días y 6 horas), con cerca de 1 hora de agua por hectárea.

## Key Findings

1. **No existe una tabla publicada de grados-día por código BBCH para el Malbec en Mendoza.** La fuente más cercana y defendible es Zapata et al. 2017 (American Journal of Enology and Viticulture, 68:60-72). Da para el Malbec una temperatura base estimada de 7,7 °C hasta brotación, 8,8 °C de brotación a floración y 11,0 °C de floración a envero. Con base fija de 10 °C da 18 grados-día hasta brotación (contando desde el 1 de abril del hemisferio norte), 260 de brotación a floración y 712 de floración a envero.
2. **Las fechas medias del Malbec en Mendoza** vienen de la colección de Chacras de Coria (Luján de Cuyo): brotación el 29 de septiembre, floración el 10 de noviembre y madurez el 5 de marzo (Rodríguez et al., UNCuyo, 1999).
3. **El Malbec es especialmente vulnerable a las heladas de primavera.** Brota en época media, es vigoroso y sus yemas secundarias (yemas de reserva) dan poca fruta: si la helada mata el brote principal, la planta casi no recupera cosecha (Gil y Pszczólkowski, 2015, citados por la revista RIVAR). También es sensible al corrimiento (caída de flores) y a la peronóspora.
4. **La duración de la helada pesa menos que la temperatura mínima.** Según la FAO, en eventos de 2 a 24 horas "importa menos cuánto dura que cuán bajo llega la temperatura". Para el índice, las horas bajo el umbral conviene usarlas como factor que agrava, no como variable principal.
5. **La humedad cambia el umbral real.** Una yema mojada (rocío, escarcha o agua) se daña a temperaturas más de 5 °F (unos 2,8 °C) más altas en la etapa de brotación (Johnson y Howell, 1981, citados por NC State). El aire seco (punto de rocío bajo, "helada negra") hace que la temperatura baje más rápido. El suelo húmedo y compactado guarda más calor de día y lo suelta de noche (FAO).
6. **Superficie de Malbec (INV, datos 2024):** Mendoza tiene 39.856,4 ha, el 84,7% del Malbec del país. Es el 27,9% de los viñedos de la provincia (142.785 ha). San Rafael tiene unas 2.191 ha de Malbec, el 19,1% de sus 11.478 ha de vid. Según la tabla por departamento del INV (Informe de Variedades Malbec, abril 2025), Tupungato tiene 5.042 ha de Malbec, el 47,6% de sus 10.587 ha de vid, y San Martín tiene 1.456 ha, el 5,6% de sus 25.847 ha de vid. Esa tabla la leí en el resumen del buscador porque el PDF bloquea la descarga automática: conviene confirmarla.

## Details

### Tema 1. Grados-día por etapa (el punto más importante)

**Qué son los grados-día:** una suma que mide cuánto calor acumuló la planta. Cada día se suma lo que la temperatura media superó una temperatura base, por debajo de la cual la vid casi no crece. Ejemplo: si un día la media fue 16 °C y la base es 10 °C, ese día suma 6 grados-día. Si la media fue 8 °C, suma 0 (nunca se resta).

**Método recomendado y su respaldo**

| Elemento | Valor | Qué significa | Fuente |
|---|---|---|---|
| Temperatura base | 10 °C | Por debajo de 10 °C se considera que la vid no avanza | DACC Mendoza usa "Temperatura media diaria − 10" en sus informes vitícolas (DACC, Análisis agrometeorológico Oasis Centro 2011-2012, http://www.contingencias.mendoza.gov.ar/web1/agrometeorologia/pdf/centro/cvitCentro11-12.pdf). La escala de Winkler también usa base 10 °C (van Leeuwen et al., IVES) |
| Fórmula | GD = máx(0, (Tmáx + Tmín)/2 − 10) | Promedio del día menos la base | Zapata et al. 2017 usan (Tmáx + Tmín)/2 |
| Umbral superior | Opcional, 32 °C (Zapata) | Por encima de 32 °C el calor extra no se cuenta | Zapata et al. 2017: "the starting date for the calculations was 1 January, and an upper threshold was specified for Ti = 32 °C" (cita confirmada en una publicación que reproduce el trabajo; DOI 10.5344/ajev.2016.15077) |
| Inicio de la acumulación | 1 de septiembre en el hemisferio sur, y reinicio en la brotación observada | En el hemisferio norte se acumula desde el 1 de enero o el 1 de abril. Desplazarlo 6 meses es una convención, no está validada para Mendoza | Adaptado de Zapata et al. 2017 y Parker et al. 2013 |
| Precisión esperada | Error de 2,4 a 6,4 días según la etapa (Malbec) | El modelo acierta mejor la floración que la brotación o el envero | Zapata et al. 2017, Malbec: brotación 6,4 d, floración 2,4 d, envero 5,8 d (evaluación) |

Con una lectura cada 5 minutos podrías calcular grados-día por hora. Pero los valores publicados se calcularon con el promedio diario: si usás otro método, los umbrales ya no son comparables.

**Grados-día del Malbec: lo que hay publicado**

| Tramo | Zapata et al. 2017, Malbec, Washington, base 10 °C | Zapata, base propia de cada etapa | Parker et al. 2013, "Cot" (= Malbec), base 0 °C desde el 1 de marzo, Europa |
|---|---|---|---|
| Hasta brotación | 18 GD (desde el 1 de abril, hemisferio norte) | 78 GD con base 7,7 °C desde el 1 de enero | No informa |
| Brotación → floración | 260 GD | 317 GD con base 8,8 °C | Floración: 1.306 °C·día acumulados |
| Floración → envero | 712 GD | 644 GD con base 11,0 °C | Envero: 2.658 °C·día acumulados |
| Días observados en Washington | Brotación → floración 54 d; floración → envero 66 d | — | — |

Fuentes: Zapata D. et al., "Predicting Key Phenological Stages for 17 Grapevine Cultivars", Am J Enol Vitic 68:60-72, 2017, https://www.ajevonline.org/content/68/1/60 (tabla verificada por el subagente en la copia de academia.edu). Parker A. et al., Agric. For. Meteorol. 180:249-264, 2013. Ojo: el texto de Zapata dice "106 días (Malbec)" de brotación a envero, pero su tabla da 120 días. Usá la tabla.

**Propuesta de grados-día por código BBCH, contados desde la brotación (base 10 °C)**

Solo los tramos marcados "con fuente" vienen de un estudio del Malbec. El resto es una interpolación mía para que el simulador avance de forma gradual. Hay que defenderla como supuesto y corregirla con observaciones.

| BBCH | Cómo se ve la planta | GD desde la brotación | Marca |
|---|---|---|---|
| 09 | Brotación: aparecen las puntitas verdes del brote | 0 (se alcanza con unos 70 GD desde el 1 de septiembre) | Supuesto, calibrado con la fecha de Chacras de Coria |
| 11 | Primera hoja abierta y separada del brote | 30 | Supuesto |
| 15 | Cinco hojas abiertas | 80 | Supuesto |
| 53 | Racimos florales (inflorescencias) bien visibles | 110 | Supuesto |
| 57 | Racimos florales completos; las florcitas se separan | 190 | Supuesto |
| 61 | Inicio de floración: 10% de las capuchas de las flores cayeron | 230 | Supuesto |
| 65 | Plena floración: 50% de las capuchas cayeron | 260 | Con fuente (Zapata 2017, "bloom") |
| 69 | Fin de floración | 300 | Supuesto |
| 71 | Cuaje: las flores fecundadas se convierten en granitos | 330 | Supuesto |
| 77-79 | Cierre del racimo: los granos se tocan | 600 | Supuesto |
| 81-83 | Envero: los granos empiezan a cambiar de color | 972 (260 + 712) | Con fuente (Zapata 2017, "veraison") |
| 89 | Madurez para cosecha | 1.450 a 1.700 | Supuesto (calor acumulado entre brotación y comienzos de marzo en las estaciones de Mendoza) |

**Diferencias entre departamentos: calor acumulado por mes (base 10 °C)**

| Mes | San Martín (SMN, cálculo con la media mensual) | San Rafael Aero (SMN, cálculo con la media mensual) | Tupungato, El Peral 1.300 m (DACC, valor medido 1998-2012) |
|---|---|---|---|
| Septiembre | 120 | 66 | 55 |
| Octubre | 251 | 186 | 160 |
| Noviembre | 351 | 291 | 239 |
| Diciembre | 446 | 391 | 321 |
| Enero | 471 | 428 | 366 |
| Febrero | 378 | 336 | 320 |
| Marzo | 338 | 291 | 276 |

San Martín y San Rafael: cálculo propio, (media mensual − 10) × días del mes, con las normales SMN 1991-2020. Subestima un poco los meses fríos. El Peral: valores "Gd" que publica la DACC.

Qué significa: San Martín (Este, unos 770 m) acumula casi el doble de calor que Tupungato en septiembre y octubre. Por eso brota y florece antes. Con el modelo de arriba, las fechas esperadas quedan así: San Martín, brotación hacia el 18 de septiembre y floración hacia el 26 de octubre. San Rafael (unos 750 m), brotación hacia el 1 de octubre y floración hacia el 8 de noviembre. Tupungato/El Peral, brotación hacia el 3 de octubre y floración hacia el 15 de noviembre. Son resultados del modelo ("adaptado"), no fechas observadas. Como punto de control, en Chacras de Coria la brotación media es el 29 de septiembre y la floración el 10 de noviembre. Advertencia: con 712 GD el modelo pone el envero en San Martín hacia fines de diciembre, lo que parece temprano para el Este. Es probable que haya que corregirlo hacia enero con las observaciones.

### Tema 2. Umbrales de helada por etapa BBCH

**Escalas fenológicas:** son "calendarios de dibujos" del desarrollo de la planta. BBCH usa números (00 a 99). Baggiolini usa letras (A a N). Eichhorn-Lorenz (E-L, modificada por Coombe en 1995) usa números del 1 al 47.

**Equivalencias entre escalas para la vid** (Lorenz et al. 1995; Coombe 1995; Baggiolini 1952; son escalas estándar, conviene verificarlas contra el original)

| BBCH | Baggiolini (vid) | E-L | Cómo se ve la planta |
|---|---|---|---|
| 00 | A | 1 | Yema de invierno, dormida, cubierta de escamas marrones |
| 01-03 | B (inicio) | 2 | La yema se hincha |
| 05 | B | 3 | Yema algodonosa: asoma una pelusa marrón clara |
| 07-09 | C | 4 | Brotación: se ve la punta verde |
| 10-11 | D | 7 | Salida de hojas: primera hoja separada |
| 12-15 | E | 9-12 | Hojas extendidas (2 a 5 hojas) |
| 53 | F | 12 | Racimos florales visibles |
| 55 | G | 15 | Racimos florales separados, alargándose |
| 57 | H | 17 | Botones florales separados |
| 60-69 | I | 19-26 | Floración: caen las capuchas de las flores (65 = plena flor = E-L 23) |
| 71 | J | 27 | Cuaje: aparecen los granitos |
| 75 | K | 31 | Grano del tamaño de una arveja |
| 77-79 | L | 32-33 | Cierre del racimo |
| 81-83 | M | 35 | Envero: los granos cambian de color |
| 89 | N | 38 | Madurez para cosecha |

**Temperaturas críticas para la vid.** Las mediciones son con uva Concord: no hay datos del Malbec por etapa.

| Etapa (fuente) | BBCH aproximado | 10% de daño | 90% de daño | Qué significa |
|---|---|---|---|---|
| Hinchazón temprana de la yema ("first swell") | 01 | −10,6 °C | −19,4 °C | La yema todavía aguanta mucho frío |
| Hinchazón tardía ("late swell") | 03-05 | −6,1 °C | −12,2 °C | Ya perdió buena parte de su resistencia |
| Brotación ("budburst") | 07-09 | No visible en el extracto consultado | No visible | Interpolá entre −6,1 y −2,8 °C (por ejemplo −3,5 °C), marcado "adaptado" |
| Primera hoja | 10-11 | −2,8 °C | −6,1 °C | El brote verde es muy sensible |
| Segunda hoja | 12 | −2,2 °C | −5,6 °C | |
| Tercera hoja | 13 | −2,2 °C | −3,3 °C | |
| Cuarta hoja | 14-15 | −2,2 °C | −2,8 °C | Entre el 10% y el 90% de daño casi no hay margen |
| Brotes y tejido verde en general | 09-57 | −2,0 °C (umbral muy usado) | Daño severo por debajo de −2,5 °C | Barlow 2010; Fuller y Telli 1999, citados en literatura científica |
| Floración y cuaje | 60-71 | Sin dato de la vid en las fuentes consultadas | — | Usá el margen conservador de frutales (ver abajo) |

Fuente principal: FAO, "Frost Protection: fundamentals, practice and economics", Vol. 1, Tabla 4.8 (Snyder y de Melo-Abreu, 2005), https://www.fao.org/4/y7223e/y7223e0a.htm, a partir de WSU EB1615 (Proebsting et al., uva Concord).

**Los estados D, F y H del informe IDR + DACC 2021**

El informe de fenología del IDR (Instituto de Desarrollo Rural) monitorea **frutales**. Sus estados son "corola visible", "flor abierta" y "fruto cuajado" (IDR, "Informe Evolución Fenológica Frutales 2021", https://www.mendoza.gov.ar/wp-content/uploads/sites/23/2024/12/Fenologia-de-Frutales-2021.pdf). En frutales, la letra D es "corola visible". En la vid, la letra D es "salida de hojas", así que **las letras no coinciden entre especies**. Comparar por órgano de la planta sería así (adaptado):

| Estado de frutal (IDR + DACC) | Umbral de frutal | Equivalente funcional en la vid | Uso recomendado |
|---|---|---|---|
| D: corola visible (botón floral cerrado que muestra color) | −1,1 °C | BBCH 57 (botones florales separados, Baggiolini H de la vid) | Margen conservador para BBCH 57 |
| F: plena flor | −0,6 °C | BBCH 65 (plena floración, Baggiolini I) | Margen conservador para BBCH 60-69 |
| H: fruto cuajado | −0,6 °C | BBCH 71 (cuaje, Baggiolini J) | Margen conservador para BBCH 71 |

La DACC también publica una tabla para frutales (no para vid): en plena floración, el duraznero aguanta hasta −2,8 °C y el cerezo, el peral y el ciruelo −2,2 °C. Con frutos chicos verdes, la mayoría aguanta hasta −1,1 °C (DACC, "Heladas", https://www.mendoza.gov.ar/contingencias/agrometeorologia/heladas/).

### Tema 3. Criterios para el índice de riesgo de helada

| Factor | Qué dice la evidencia | Cómo usarlo en el índice | Fuente |
|---|---|---|---|
| Temperatura mínima frente al umbral de la etapa | Es el factor que más pesa | Variable principal | FAO 2005, cap. 4 |
| Duración (horas bajo el umbral) | En eventos de 2 a 24 h, la duración importa menos que lo bajo que llega la temperatura (Levitt 1980). Los ensayos de laboratorio usan escalones de 20 a 30 minutos | Agravante: sube un nivel si hay 2 horas o más bajo el umbral | FAO 2005 |
| Humedad del aire: helada blanca o negra | Helada blanca: el aire tiene agua y se forma escarcha. Al condensarse y congelarse, el agua libera calor y frena la caída de temperatura. Helada negra: aire seco y punto de rocío muy bajo, sin escarcha visible; la temperatura cae más y es más dañina | Agravante: sube un nivel si el punto de rocío es ≤ −5 °C o la humedad nocturna es < 60% | FAO 2005; UC Davis, "Frost Protection Principles" |
| Temperatura de bulbo húmedo | Es la temperatura más baja que alcanza algo mojado al evaporarse su agua. Una planta mojada no baja de ese valor. Se usa para decidir cuándo prender aspersores | Calculala con temperatura y humedad. Regla práctica: bulbo húmedo ≈ T − (T − punto de rocío)/3 | FAO 2005; Rutgers NJAES E363 |
| Yema mojada | En brotación, las yemas mojadas se dañan a temperaturas más de 5 °F (unos 2,8 °C) más altas | Si hubo lluvia o riego por aspersión y la humedad es ≥ 95%, subí el umbral 1 a 2 °C (supuesto) | Johnson y Howell 1981, citados por NC State |
| Humedad de suelo | El suelo húmedo y compactado guarda y conduce más calor. La meta es mantenerlo cerca de su capacidad máxima de agua y mojar 1 a 2 días antes de la helada. Solo importa la capa superficial | Agravante leve: sube un nivel si la humedad está bajo el umbral de riego | FAO 2005; UCANR |
| Abrigo meteorológico frente a la altura de los brotes | Con cielo despejado hay inversión térmica: el aire más frío queda cerca del suelo. La FAO midió diferencias de 1 °C o más en pocos cientos de metros a la misma altura | No encontré una diferencia cuantificada entre el abrigo (1,5-1,8 m) y los brotes. Supuesto: los brotes a 0,8-1,2 m están 0,5 a 1,5 °C más fríos | FAO 2005 |

**Índices publicados:** el IDR elaboró un mapa interactivo que cruza las temperaturas críticas de las estaciones de la DACC con el estado fenológico (2018-2021). En Argentina también existe el "índice de peligrosidad de heladas" (IPH), que combina la fenología con la probabilidad de llegar a temperaturas críticas (Agrociencia Uruguay, 2014). Para frutales norpatagónicos hay un índice con niveles basado en LT10 y LT50 (temperaturas de 10% y 50% de daño). Ninguno trae cortes publicados para la vid en Mendoza: la clasificación bajo/medio/alto de este informe es **adaptada**.

### Tema 4. Umbral de humedad de suelo para la alerta de riego

| Concepto | Qué significa | Valor | Marca |
|---|---|---|---|
| Capacidad de campo | El máximo de agua que el suelo retiene después de drenar ("suelo lleno") | Franco: ~28% de agua en volumen; arenoso: ~14%; pedregoso/franco-arenoso con grava: ~18% | Supuesto (rangos generales por textura, no medidos en Mendoza) |
| Punto de marchitez | El suelo tiene tan poca agua que la planta ya no puede sacarla | Franco ~12%; arenoso ~6%; pedregoso ~8% | Supuesto |
| Fracción que se puede gastar antes de regar (p) | Qué parte del agua disponible puede usar la vid sin estrés | 0,45 para vid de vino | FAO-56 (Allen et al. 1998), verificar en la Tabla 22 |
| Umbral de reposición (alerta) | CC − p × (CC − PM) | Franco ≈ 21%; arenoso ≈ 10%; pedregoso ≈ 13,5% | Adaptado |

Ejemplo simple: en un suelo franco, con 28% de agua el suelo está lleno, con 21% conviene regar y con 12% la planta ya no puede tomar agua.

**Riego deficitario controlado (RDC) en Malbec:** consiste en regar a propósito menos de lo que la planta consume, en etapas en las que eso no daña la cosecha. En un ensayo en Mendoza presentado en el INA, el riego "estándar" reponía cada semana el 70% del consumo estimado de una vid bien regada. El "déficit temprano" reponía solo el 35% entre cuaje y envero. El "déficit tardío" aplicaba el recorte después del envero (Tarara et al., INA CRA, https://www.ina.gov.ar/archivos/pdf/CRA-IIIFERTI/CRA-RYD-27-Tarara.pdf). En Malbec regado por goteo, una planta sin estrés mostró potencial de tallo de −0,55 a −0,7 MPa (una medida de cuánto "le cuesta" a la planta sacar agua; más negativo es más seco). Una planta con estrés mostró −0,8 MPa en tallo y −1,5 MPa en hoja. La evapotranspiración de referencia promedio fue de 5 mm por día (De Lorenzi et al., INA, https://www.ina.gov.ar/archivos/publicaciones/CRA-RYD-23_De%20Lorenzi1_Flujo_savia_vid_malbec.pdf). Existe además un trabajo del INTA sobre RDC en Malbec (Dayer et al. 2012, EEA Luján de Cuyo), del que solo verifiqué el título.

| Período | Necesidad de agua | Umbral propuesto |
|---|---|---|
| Septiembre-octubre (brotación, hojas) | Baja: poca hoja y aire fresco | Umbral normal (p = 0,45) |
| Noviembre (floración, cuaje) | Media; la falta de agua aumenta el corrimiento | Umbral normal o algo más húmedo (p = 0,40) |
| Diciembre-enero (cuaje a envero) | Alta; es la ventana clásica del RDC | Más seco permitido (p = 0,60), adaptado de Tarara |
| Febrero-marzo (envero a cosecha) | Alta al principio, baja hacia la cosecha | p = 0,50 |

### Tema 5. Sistema de riego

| Dato | Valor | Fuente |
|---|---|---|
| Superficie regada en Mendoza | 267.889 ha; 8% (21.621 ha) con riego localizado, sobre todo goteo | INDEC, Censo Nacional Agropecuario 2002, citado por Fontela (INA) |
| Riego por superficie (surco o melga) | ~90% de la superficie regada | INDEC 2002, citado por Schilardi (INA) |
| Goteo, estimación posterior | ~40.000 ha, ~14% de la superficie regada | Schilardi (INA) |
| Riego por departamento | No encontré datos por departamento para la vid | — |
| Turnos del DGI (Valle de Uco, Canal Matriz) | Rotación de 6 días 6 h a 9 días 8 h, la más común 7 días 6 h. Cerca de 1 h por hectárea (mínimo 40 min, máximo 3 h). Cada cuadro de turnos cubre 90-100 ha | Gobierno de Mendoza, Memoria técnica "Modernización de riego Canal Matriz Valle de Uco", 2025 |
| Dotación legal | Máximo 1,5 L/s por hectárea; si el agua no alcanza para 1 L/s por hectárea, se reparte por turnos | Ley de Aguas de Mendoza (1884), arts. 122 y 162 |
| Riego en zonas Este y Sur | Ahí se practica el riego por superficie en vid y frutales | Documento educativo de la DGE Mendoza (fuente secundaria) |
| Pozos | La mayor densidad de perforaciones está en Maipú, San Martín y Guaymallén | FAO, "Áreas de riego Provincia de Mendoza" |

**Volúmenes de riego.** No encontré una fuente primaria con volumen por evento.

| Sistema | Por evento | Equivalencias | Frecuencia | Marca |
|---|---|---|---|---|
| Surco | 60 mm | 600.000 L/ha, unos 150 L por planta con 4.000 plantas/ha | Cada turno del DGI (~7 días) | Supuesto (lámina típica de riego por superficie) |
| Goteo, octubre | 1,5 mm/día | 15.000 L/ha/día, ~3,8 L por planta por día | Diario o día por medio | Supuesto (ETo ~4 mm × coeficiente de cultivo ~0,35) |
| Goteo, enero-febrero | 3,5 mm/día | 35.000 L/ha/día, ~8,8 L por planta por día | Diario | Adaptado (ETo de 5 mm/día de De Lorenzi × coeficiente 0,7 de FAO-56) |

Equivalencia útil: 1 mm de riego = 10.000 litros por hectárea = 1 litro por metro cuadrado.

**Riego contra heladas.** El aspersor sobre la planta protege porque el agua, al congelarse, libera calor. Hay que prenderlo antes de que la temperatura de bulbo húmedo llegue al umbral de daño y apagarlo cuando el bulbo húmedo vuelva a superar 0 °C. Si se corta antes, la evaporación enfría y puede empeorar el daño. El goteo da resultados variables. El riego previo (mojar el suelo 1 a 2 días antes) es una protección pasiva de pocos grados (FAO 2005; UCANR). La DACC recomienda además no plantar en zonas bajas donde se junta el aire frío.

### Tema 6. Datos del Malbec y de su clima

**6a. La variedad**

| Rasgo | Dato | Fuente |
|---|---|---|
| Brotación | Media (Gil y Pszczólkowski); otras fuentes la llaman precoz. En Washington brota el día 107 del año (± 5,3) | RIVAR vol. 3 n.º 7; Zapata 2017 |
| Heladas de primavera | Muy sensible: sus yemas secundarias dan poca fruta | Gil y Pszczólkowski 2015, en RIVAR |
| Vigor | Vigoroso; conviene evitar suelos muy fértiles porque aumentan la corredura | RIVAR |
| Calor | Necesita buena amplitud térmica y noches frescas. Es más sensible que el Cabernet Sauvignon a las noches cálidas. Lo ideal es que las máximas medias no superen 30 °C durante la maduración | Rodríguez et al., UNCuyo 1999 |
| Corrimiento | Muy sensible; el frío durante la floración provoca una fuerte caída de flores | vitivinicultura.net (fuente secundaria) |
| Enfermedades | Sensible a mildiu (peronóspora), antracnosis, ácaros, oídio y podredumbre gris (botrytis) | RIVAR; vitivinicultura.net |

**6b. Presencia en Mendoza**

| Departamento | Malbec (ha) | Vid total (ha) | % de Malbec | Fuente y comentario |
|---|---|---|---|---|
| San Rafael | 2.191 (2024) | 11.478 | 19,1% | Diario San Rafael, abril 2025, citando al INV |
| Tupungato | 5.042 (2024; el 12,6% del Malbec de Mendoza) | 10.587 | 47,6% | INV, Informe de Variedades Malbec, abril 2025, tabla "Mendoza - Superficie Malbec por departamento (ha) - Año 2024" (leída en el resumen del buscador; confirmar en el PDF) |
| San Martín | 1.456 (2024; el 3,7% del Malbec de Mendoza) | 25.847 | 5,6% | Misma tabla del INV 2025 (leída en el resumen del buscador). Ojo: hay otra fila "San Martín" de 219 ha que parece ser del departamento homónimo de San Juan; confirmar en el PDF |
| Mendoza total | 39.856,4 | 142.785 | 27,9% | INV, Informe Malbec 2025 (datos 2024) |

Altitud y zona: San Martín, unos 770 m, clima árido (BWk). San Rafael, unos 750 m, clima semiárido frío (BSk). Tupungato, de 1.000 a más de 1.300 m (El Peral está a 1.300 m). Valle de Uco y la zona Centro concentran el 63,1% del Malbec del país (INV). Los suelos de Mendoza son jóvenes y sin horizontes diferenciados (Catania y Avagnina, INTA 2000, citados por RIVAR). No encontré una descripción de suelos por departamento en fuentes primarias.

**6c. Cultivo.** No encontré en fuentes primarias la proporción de espaldero frente a parral, la densidad de plantación ni el tamaño de cuartel. Lo único verificado es una finca en venta en Tupungato con "4 ha de Malbec en espaldero", riego por surco "con derecho de 6 horas semanales y pozo propio" (aviso inmobiliario, no es fuente técnica). Supuestos para el simulador: espaldero (plantas en fila, apoyadas en alambres verticales) con 2,5 m entre hileras × 1,0 m entre plantas = 4.000 plantas/ha; parral (techo de alambres a unos 2 m) con 2,5 × 2,5 m = 1.600 plantas/ha; cuartel de 1 a 5 ha.

**6d. Clima mensual de septiembre a marzo**

San Rafael Aero (SMN, normales 1991-2020)

| Mes | Máx. (°C) | Mín. (°C) | Media (°C) | Amplitud (°C) | HR media (%) | Lluvia (mm) | Días con lluvia | Mínima absoluta (°C) |
|---|---|---|---|---|---|---|---|---|
| Sep | 20,5 | 4,9 | 12,2 | 15,6 | 52,6 | 21,5 | 4,0 | −6,9 |
| Oct | 23,9 | 8,2 | 16,0 | 15,7 | 51,3 | 38,3 | 5,1 | −2,4 |
| Nov | 27,6 | 11,4 | 19,7 | 16,2 | 48,2 | 36,2 | 5,8 | −0,3 |
| Dic | 30,7 | 14,2 | 22,6 | 16,5 | 46,6 | 41,2 | 6,0 | 1,5 |
| Ene | 31,8 | 15,8 | 23,8 | 16,0 | 50,0 | 54,2 | 6,9 | 4,3 |
| Feb | 30,2 | 14,7 | 22,0 | 15,5 | 56,1 | 50,6 | 6,4 | 4,8 |
| Mar | 27,4 | 12,9 | 19,4 | 14,5 | 61,3 | 40,2 | 5,1 | −2,7 |

San Martín (SMN, normales 1991-2020)

| Mes | Máx. | Mín. | Media | Amplitud | HR media | Lluvia | Días con lluvia | Mínima absoluta |
|---|---|---|---|---|---|---|---|---|
| Sep | 22,2 | 7,3 | 14,0 | 14,9 | 50,9 | 8,4 | 1,9 | −5,2 |
| Oct | 25,9 | 11,1 | 18,1 | 14,8 | 49,7 | 15,4 | 2,5 | −1,9 |
| Nov | 29,4 | 14,4 | 21,7 | 15,0 | 48,8 | 26,6 | 3,8 | −0,3 |
| Dic | 32,2 | 17,0 | 24,4 | 15,2 | 48,8 | 29,6 | 4,6 | 2,4 |
| Ene | 32,9 | 18,3 | 25,2 | 14,6 | 53,5 | 48,0 | 6,4 | 5,3 |
| Feb | 31,2 | 16,9 | 23,5 | 14,3 | 58,6 | 45,0 | 5,3 | 4,0 |
| Mar | 28,5 | 15,0 | 20,9 | 13,5 | 63,8 | 47,1 | 4,3 | −1,4 |

Tupungato: estación El Peral, 1.300 m (DACC, promedios 1998-2012)

| Mes | Máx. | Mín. | Media | Amplitud | HR media | Lluvia (mm) | Días con helada |
|---|---|---|---|---|---|---|---|
| Sep | 18,37 | 3,73 | 10,57 | 14,6 | 51,25 | 27,2 | 4,38 |
| Oct | 23,03 | 7,63 | 15,07 | 15,4 | 48,77 | 34,0 | 0 |
| Nov | 26,18 | 10,03 | 17,95 | 16,2 | 47,21 | 21,8 | 0 |
| Dic | 28,68 | 12,40 | 20,48 | 16,3 | 48,34 | 17,1 | — |
| Ene | 29,75 | 14,26 | 21,81 | 15,5 | 52,34 | 32,1 | — |
| Feb | 28,34 | 13,71 | 20,52 | 14,6 | 58,90 | 30,3 | 0 |
| Mar | 25,55 | 11,25 | 17,85 | 14,3 | 63,15 | 52,5 | 0,07 |

Fuentes: SMN, "Estadísticas Climatológicas Normales 1991-2020" (2023), https://repositorio.smn.gob.ar/handle/20.500.12160/2506 (valores tomados de su reproducción en Wikipedia, que cita al SMN). DACC, "Análisis agrometeorológico Oasis Centro, campaña vitícola 2011-2012". La DACC no publica días con lluvia para El Peral.

**Heladas:** el período de alerta por heladas tardías en Mendoza va del 1 de septiembre al 15 de noviembre (IDR, "Informe sobre heladas tardías", 2020). Frecuencia media de días con helada (DACC, 1998-2011): Tunuyán, 10,97 en septiembre, 1,02 en octubre y 0,48 en noviembre. Tres Esquinas, 10,1 / 1,28 / 0,69. La Consulta, 4,91 / 0,33 / 0,07. Agua Amarga, 3,33 / 0 / 0. No encontré la fecha media de última helada por departamento: hay un trabajo nacional sobre la metodología ("Información agroclimática de las heladas en la Argentina"), pero no pude ver sus valores para Mendoza. En octubre de 2025, el INTA La Consulta pronosticó mínimas de hasta −3,5 °C en el Valle de Uco, con el brote "alto, con racimos y pronto a la floración" (Infocampo).

**6e. Rendimiento (contexto).** INV 2024: Mendoza cosechó 3.459.719 quintales de Malbec sobre 39.856 ha, unos 8.680 kg/ha en promedio (cálculo propio; 1 quintal = 100 kg). No encontré rendimientos por departamento.

## Recommendations

1. Al defender los grados-día, presentalos como "modelo inicial de Zapata et al. 2017 + corrección con observaciones". Así es exactamente como está diseñado tu sistema, y esa es tu mejor defensa.
2. En el índice de helada, usá la tabla FAO/WSU de la vid como umbral principal y los valores del IDR + DACC como margen conservador para floración y cuaje. Aclarale al tribunal que las letras D, F y H son de frutales.
3. Usá el SMN para San Rafael y San Martín y la DACC (El Peral) para Tupungato. La humedad diurna y nocturna calculala desde el punto de rocío (ver valores "supuesto").
4. Antes de la evaluación, bajá a mano el PDF del INV "Informe de Variedades Malbec 2025": el sitio bloqueó el acceso automático y ahí está la tabla por departamento con San Martín y Tupungato.

## Caveats

- Los grados-día del Malbec vienen de Washington (hemisferio norte, otro clima). Desplazar la fecha de inicio 6 meses no está validado.
- Las temperaturas críticas son de uva Concord, medidas en laboratorio. El Malbec puede diferir.
- Los datos climáticos del SMN que usé vienen de su reproducción en Wikipedia, que cita al SMN. Conviene contrastarlos con el PDF oficial.
- Los datos de vid total por departamento del Gobierno de Mendoza no indican el año, y no coinciden con el INV en San Rafael (12.171 frente a 11.478 ha).
- La humedad de día y de noche no viene en las fuentes: la calculé suponiendo un punto de rocío constante en el día. Es una aproximación.

## Valores recomendados para el simulador

**a) Grados-día (base 10 °C, (Tmáx + Tmín)/2, acumulación desde el 1 de septiembre y reinicio en BBCH 09)**

| BBCH | GD desde la brotación | Fuente | Marca |
|---|---|---|---|
| 09 | 0 (≈ 70 GD desde el 1 de septiembre) | Calibrado con Chacras de Coria (UNCuyo 1999) | Supuesto |
| 11 / 15 | 30 / 80 | Interpolación | Supuesto |
| 53 / 57 | 110 / 190 | Interpolación | Supuesto |
| 61 / 65 / 69 | 230 / 260 / 300 | Zapata 2017 (65) | 65: con fuente; resto: supuesto |
| 71 | 330 | Interpolación | Supuesto |
| 77-79 | 600 | Interpolación | Supuesto |
| 81-83 | 972 | Zapata 2017 | Con fuente (Washington) |
| 89 | 1.450-1.700 | Calor entre brotación y marzo en estaciones de Mendoza | Supuesto |

**b) Umbral de helada (temperatura del aire a la altura del brote)**

| BBCH | Umbral (10% de daño) | 90% de daño | Fuente | Marca |
|---|---|---|---|---|
| 00 | −15 °C | — | TFG UMH (yema de invierno) | Con fuente (secundaria) |
| 01 | −10,6 °C | −19,4 °C | FAO Tabla 4.8 | Con fuente (Concord) |
| 03-05 | −6,1 °C | −12,2 °C | FAO Tabla 4.8 | Con fuente (Concord) |
| 07-09 | −3,5 °C | −7,0 °C | Interpolación entre las etapas vecinas | Adaptado |
| 11 | −2,8 °C | −6,1 °C | FAO Tabla 4.8 | Con fuente (Concord) |
| 12-15 | −2,2 °C | −2,8 a −5,6 °C | FAO Tabla 4.8 | Con fuente (Concord) |
| 53-57 | −1,1 °C | −2,2 °C | IDR + DACC (corola visible, frutales); −2,2 de FAO | Adaptado |
| 60-69 | −0,6 °C | −2,0 °C | IDR + DACC (plena flor, frutales); −2,0 de Barlow 2010 | Adaptado |
| 71 | −0,6 °C | −2,0 °C | IDR + DACC (fruto cuajado, frutales) | Adaptado |

**c) Cortes del índice de riesgo de helada.** Margen = Tmín − umbral de la etapa.

| Paso | Regla | Marca |
|---|---|---|
| Nivel base | Bajo: margen > 2 °C. Medio: margen entre 0 y 2 °C. Alto: margen ≤ 0 °C | Adaptado (FAO recomienda un margen de seguridad sobre los umbrales publicados) |
| Duración | Sube un nivel si pasa ≥ 2 h por debajo de umbral + 1 °C | Supuesto (la FAO dice que la duración es secundaria) |
| Aire seco (helada negra) | Sube un nivel si la HR nocturna es < 60% o el punto de rocío es ≤ −5 °C | Supuesto basado en FAO |
| Planta mojada | Si la HR es ≥ 95% tras lluvia o aspersión, el umbral sube 1,5 °C | Adaptado de Johnson y Howell 1981 |
| Suelo seco | Sube un nivel (solo de bajo a medio) si la humedad de suelo está bajo el umbral de riego | Supuesto basado en FAO |
| Tope | Nunca supera "alto"; no es un porcentaje de daño | — |

**d) Umbral de humedad de suelo para la alerta de riego (% de agua en volumen)**

| Período | Franco | Arenoso | Pedregoso | Marca |
|---|---|---|---|---|
| Septiembre-octubre (p 0,45) | 21% | 10% | 13,5% | Adaptado (FAO-56) |
| Noviembre (p 0,40) | 21,5% | 11% | 14% | Adaptado |
| Diciembre-enero, RDC (p 0,60) | 18,5% | 9% | 12% | Adaptado (Tarara, INA) |
| Febrero-marzo (p 0,50) | 20% | 10% | 13% | Adaptado |

**e) Riego por finca**

| Finca | Sistema | Volumen y frecuencia | Marca |
|---|---|---|---|
| San Rafael | Surco por turno del DGI + riego extra desde pozo | 60 mm (600.000 L/ha) cada 7 días 6 h; extra de 30 mm si salta la alerta | Supuesto (turnos según DGI Valle de Uco; predominio de superficie según INDEC 2002) |
| Tupungato | Goteo con represa o pozo + turno | Octubre 1,5 mm/día; diciembre-febrero 3,5 mm/día; extra de 4 mm | Adaptado (De Lorenzi, FAO-56) |
| San Martín | Surco por turno + pozo | 60 mm cada 7 días 6 h; extra de 30 mm | Supuesto |

**f) Fechas esperadas para 2026 (resultados del modelo; corregir con observaciones)**

| Departamento | Brotación (BBCH 09) | Floración (BBCH 65) | Marca |
|---|---|---|---|
| San Martín | ~18 de septiembre | ~26 de octubre | Adaptado |
| San Rafael | ~1 de octubre | ~8 de noviembre | Adaptado |
| Tupungato | ~3 de octubre | ~15 de noviembre | Adaptado |
| Referencia de Luján (Chacras de Coria) | 29 de septiembre | 10 de noviembre | Con fuente (UNCuyo 1999) |

**g) Clima mensual.** Temperaturas y lluvia: con fuente (tablas de la sección 6d). Humedad de día (a la hora de la máxima) y de noche (a la hora de la mínima): supuesto, calculadas desde el punto de rocío medio.

| Mes | San Rafael: HR día / noche (%) | San Martín: HR día / noche (%) | Tupungato: HR día / noche (%) |
|---|---|---|---|
| Sep | 31 / 86 | 30 / 80 | 31 / 82 |
| Oct | 31 / 86 | 31 / 78 | 30 / 80 |
| Nov | 30 / 82 | 31 / 77 | 29 / 79 |
| Dic | 29 / 79 | 31 / 77 | 30 / 81 |
| Ene | 31 / 82 | 34 / 82 | 33 / 84 |
| Feb | 35 / 89 | 37 / 88 | 37 / 91 |
| Mar | 38 / 93 | 41 / 93 | 39 / 97 |

Heladas en el simulador: 6 a 8 noches, concentradas en septiembre (unas 5 a 6), con 1 o 2 en octubre y 0 o 1 en noviembre. Mínimas entre −1 y −5 °C, sin pasar las mínimas absolutas del SMN (septiembre −6,9 °C en San Rafael y −5,2 °C en San Martín). Marca: adaptado (frecuencias DACC, extremos SMN).

**h) Densidad y parcela:** espaldero de 2,5 × 1,0 m = 4.000 plantas/ha. Parcela de 2 ha, es decir 8.000 plantas por parcela. Marca: supuesto.

**i) Condiciones que favorecen enfermedades (para alertas futuras)**

| Problema | Condición | Marca |
|---|---|---|
| Peronóspora (mildiu) | "Regla de los tres 10": ≥ 10 °C, ≥ 10 mm de lluvia en 24-48 h y brotes de ≥ 10 cm | Adaptado (regla clásica, no verificada en esta búsqueda) |
| Oídio | 20-27 °C, humedad moderada; no necesita agua libre sobre la hoja | Adaptado (literatura general) |
| Botrytis (podredumbre gris) | 15-25 °C con HR > 90% u hoja mojada por muchas horas, sobre todo del envero a la cosecha | Adaptado (literatura general) |
| Corrimiento | Frío o lluvia durante BBCH 60-69 (por ejemplo, Tmín < 10 °C varios días en plena flor) | Supuesto; la sensibilidad del Malbec sí tiene fuente |

## Glosario

- **BBCH:** escala con números (00 a 99) que describe cada etapa de la planta.
- **Baggiolini:** escala de etapas de la vid con letras de la A a la N.
- **Eichhorn-Lorenz (E-L):** otra escala numérica de etapas de la vid, del 1 al 47.
- **Grados-día:** una suma que mide cuánto calor acumuló la planta.
- **Temperatura base:** el valor por debajo del cual se considera que la planta no crece (aquí, 10 °C).
- **Brotación:** cuando las yemas se abren y asoma el brote verde.
- **Envero:** cuando los granos de uva empiezan a cambiar de color.
- **Cuaje:** cuando las flores fecundadas se convierten en granitos.
- **Corrimiento (corredura):** caída de flores o granitos recién formados, que deja racimos ralos.
- **LT10 / LT90:** temperaturas que matan el 10% o el 90% de las yemas o brotes.
- **Punto de rocío:** temperatura a la que el aire se satura y aparece el rocío o la escarcha.
- **Bulbo húmedo:** temperatura que marca un termómetro mojado; una planta mojada no baja de ese valor.
- **Helada blanca / negra:** con escarcha visible (aire húmedo) o sin escarcha (aire seco, suele ser más dañina).
- **Inversión térmica:** noche en la que el aire de abajo está más frío que el de arriba.
- **Capacidad de campo:** el máximo de agua que el suelo retiene después de drenar.
- **Punto de marchitez:** humedad de suelo tan baja que la planta ya no puede sacar agua.
- **Riego deficitario controlado (RDC):** regar a propósito menos de lo que la planta consume, en etapas en las que eso no daña la cosecha.
- **Evapotranspiración:** el agua que se pierde por evaporación del suelo y por la transpiración de la planta.
- **Turno de riego:** el horario fijo en el que el DGI entrega agua a cada finca.
- **Espaldero / parral:** plantas en fila, apoyadas en alambres verticales / techo de alambres a unos 2 m del suelo.
