> **Documento de trabajo.** Informe de búsqueda amplia usado para plantear el problema del proyecto. Combina datos de organismos y de prensa: las cifras de prensa deben verificarse en la fuente primaria (INV, DGI, Boletín Oficial) antes de usarse fuera de este documento. Las propuestas de modelo de este informe son exploratorias; el alcance del MVP está en [`../vision.md`](../vision.md) y [`../requisitos.md`](../requisitos.md).

# Clima, crisis económica y datos dispersos: problemáticas de viñateros y contratistas de Mendoza (2020–oct. 2026) y oportunidades para una base de datos MongoDB

Para el período 2020-2026, las fuentes describen en los viñateros de Mendoza dos crisis que se suman: una climática, con heladas tardías recurrentes como principal causa de pérdida, granizo y una sequía que terminó en 2026, y otra económica, con tres cosechas seguidas en que la uva se pagó por debajo del costo. El problema que mejor justifica un proyecto de base de datos es que la información para gestionar el riesgo existe, pero está repartida entre organismos (DCC, DGI, INV, SMN/INTA, bodegas, gremios) y no se integra a nivel de finca y parcela. Por eso las cifras de daño llegan semanas tarde, se discuten políticamente y no se cruzan con contratos, seguros ni cosecha.

## TL;DR

- **Clima:** la helada tardía es el riesgo dominante. En el Oasis Sur, el 76,3% de las 136.809 ha con pérdida denunciadas desde 2016-17 se debió a heladas y el 23,7% a granizo. Hubo heladas severas en 2020, 2022, 2025 y el 7/9/2026, con −8,3 °C en Monte Comán. La sequía de 2025-26 (Río Mendoza al 61% de un año medio) da paso en 2026-27 a un año húmedo con "Súper Niño", que eleva el riesgo de granizo y de enfermedades por hongos.
- **Economía:** Mendoza cosechó 13,15 millones de quintales en 2026 (−8% a −12% según la base de comparación). La uva se pagó entre $140 y $150/kg contra un costo de $200 a $240/kg. Los contratistas cobran $32.100/ha por mes más el 15-18% de una producción que vale menos y que se les paga con meses de demora. Desde 2016, Mendoza perdió 17.903 ha de vid.
- **Datos (la oportunidad para MongoDB):** no hay un registro integrado que vincule finca → parcela → evento climático → denuncia/tasación → seguro → contrato → cosecha → pago. Un modelo documental con índices geoespaciales (2dsphere), colecciones de series temporales para sensores y agregaciones por departamento y oasis responde directamente a las necesidades que muestran las noticias.

## Resumen ejecutivo

El sector vitícola mendocino viene achicándose. Según el Informe Anual de Superficie del INV, al 31/12/2025 Mendoza tenía 140.682 ha de vid en 14.371 viñedos (71,7% del país), con 17.903 ha menos que en 2016. La concentración avanza: los viñedos de menos de 10 ha son el 75% de las unidades pero suman solo el 25,8% de la superficie (CEPA, oct. 2025, con datos de 2024). Sobre esta estructura frágil actúan cuatro amenazas climáticas:

1. **Heladas tardías** (septiembre a noviembre). Son la principal causa de pérdida, sobre todo en San Rafael, General Alvear, el Este y el Valle de Uco.
2. **Granizo** (primavera y verano). Su frecuencia es menor que la de las heladas, pero es destructivo. Juan Rivera, doctor en Ciencias de la Atmósfera e investigador del Conicet, dijo a El Sol que, según estudios de EE. UU. y Europa, el granizo grande está aumentando, aunque aclaró que en Mendoza todavía no hay investigaciones sobre su frecuencia ni su tamaño.
3. **Sequía hídrica** (2019-2025). Hubo años con ríos al 58-63% de la media.
4. **Lluvias, humedad y tormentas** ligadas a El Niño en 2026-27.

En la respuesta estatal cambió el enfoque: Mendoza pasó de la lucha antigranizo con aviones a priorizar un seguro paramétrico/indemnizatorio, el Fondo Compensador Agrícola (FCA). Para no cortar la asistencia directa, la Provincia ofrece vender o ceder los aviones a los municipios. La respuesta depende de un circuito administrativo lento: inscripción en el RUT, denuncia en 10 días hábiles (o 20 días de observación más 10 hábiles para heladas), tasación pericial, certificado de daños, decreto provincial de emergencia y homologación nacional. Este flujo se puede modelar casi tal cual como documentos con estados.

## Cronología de eventos climáticos y hechos relevantes

| Fecha | Evento | Zonas | Datos clave | Medio (fecha) |
|---|---|---|---|---|
| 5/10/2020 | Helada tardía | San Rafael, Gral. Alvear, San Martín y otros | 30.373 ha de vid con 24% de daño promedio; 16.341 ha de frutales; 5.394 denuncias (SR 1.669, GA 1.282, SM 747) | Los Andes (2/1/2021) |
| Oct. y 31/10-1/11/2022 | Tres heladas tardías ("la peor en tres décadas") | 135 distritos de 15 departamentos; Valle de Uco, Este y Sur | ~10.000 ha de vid + 10.000 ha de frutales con daño relevante; compensación de hasta $72.000/ha con daño total | La Nación (3/11/2022); Infocampo (4/11/2022); Diario Uno |
| Nov. 2022 | Granizo sobre fincas ya heladas | Este, Sur, Valle de Uco | Más de 40.000 ha con pérdidas superiores al 80%; productores del Este con 95-100% de pérdida | MDZ (15/11/2022) |
| 12-13/1/2023 | Granizada de 7 minutos | Medrano (Rivadavia), Junín, San Martín | Entre 5.000 y 6.000 ha; 80% de daño en viñedos | Infocampo/Télam (13/1/2023) |
| Ene. 2023 | Balance helada + granizo | Provincia | 26.000 ha con pérdida total, con posibilidad de llegar a 30.000 | Infocampo (24/1/2023) |
| Feb. 2023 | Granizo en el Este y Maipú | Este | 6.000 ha con "alto daño" + 6.000 con "bajo daño" según la manga de radar; los viñedos con malla se salvaron | Los Andes |
| 1º sem. 2023 | Consecuencia económica | — | Exportaciones de vino −31,7% frente a 2022 tras "la peor cosecha de la historia" | Mendoza Post |
| 18/1/2024 | Emergencia por granizo, zonda y heladas | 4 oasis | Vigencia del 1/12/2023 al 31/3/2025 | Los Andes (18/1/2024) |
| Temporada 2024-25 | Granizo; aviones suspendidos para priorizar el seguro | Sur (SR, GA) | 3.500 adheridos al FCA; $7.300 millones pagados (75% al Oasis Sur); 2.300 ha con granizo en San Rafael | El Sol; Prensa Gob. Mendoza; Mendoza24 |
| 22/9/2025 | Helada | San Rafael, Gral. Alvear | Denuncias habilitadas hasta el 24/10/2025 | Diario Mendoza |
| 26-28/9/2025 | Granizo "sin precedentes" por la época | San Carlos (La Consulta, Altamira, El Chacón) | Frutales con pérdida total; vid dañada en sarmientos; 54 familias asistidas | Infocampo (26/9/2025) |
| 6/10/2025 | Helada tardía | 11 departamentos (Este, Norte, Centro, Sur) | Denuncias hasta el 7/11/2025; no se publicaron cifras oficiales en hectáreas | Prensa Gob. Mendoza (27/10/2025); MDZ y Sitio Andino (28/10/2025) |
| 8/10/2025 | Pronóstico hídrico 2025-26: sequía moderada | Todas las cuencas | Río Mendoza 845 hm³ (61% de un año medio); Tunuyán 535 hm³ (63%); Diamante 605 hm³ (62%); Malargüe 180 hm³ (60%) | DGI / Prensa Gob. (8/10/2025) |
| 10/11/2025 | Convenio de lucha antigranizo con San Rafael | Sur | 3 aviones (2 operativos + 1 de soporte), bengalas de yoduro de plata y radar provincial | ADN País (10/11/2025); Los Andes |
| 28/1/2026 (BO 3/2/2026) | Decreto 125/2026 de emergencia y desastre | Centro, Este, Norte y Sur | Heladas: del 1/12/2025 al 31/3/2027; granizo: del 1/1/2026 al 31/3/2027 | Los Andes (3/2/2026); MendoVoz |
| Feb. 2026 | Cosecha atrasada | Provincia; Sur | −26% de uva ingresada a fin de febrero (2,30 contra 3,15 millones de qq); San Rafael −48% (26.630 qq, mínimo en 9 años) | 617 News (con datos del INV) |
| Feb. 2026 | Pronóstico de cosecha del INV | Mendoza | 13,45 millones de qq (−9% frente a 14,79 millones en 2025); pérdidas de hasta 30% en el Este, el Sur y el Valle de Uco | Los Andes; Diario Mendoza |
| 19-20/5/2026 | Informe final de cosecha 2026 del INV | País y Mendoza | País 18.391.299 qq (−8%); Mendoza 13.147.187 qq | Revista Chacra (20/5/2026); Diario Uno |
| 27/5/2026 | Resolución nacional 765/2026 que homologa la emergencia | 16 departamentos | Emergencia nacional por granizo y heladas | Perfil; Diario Uno |
| 7/9/2026 | Helada en plena brotación y floración | Sur (Monte Comán −8,3 °C, Villa Atuel −8 °C, Palermo Chico −7,7 °C); Este; Valle de Uco | Daños en carozo, vid y olivo; denuncias del 28/9 al 9/10/2026; sin cifra oficial todavía | Minuto Ya (7, 25 y 28/9/2026); Bichos de Campo (18/9/2026); Sitio Andino (25/9/2026) |
| 13-14/9/2026 | Nueva helada | San Rafael, Gral. Alvear (Las Malvinas −7,4 °C) | Algunas zonas superan las 70 horas de helada acumuladas | Minuto Ya (14 y 28/9/2026) |
| 10/9/2026 | Disputa por los aviones antigranizo | Sur | $14.000 millones girados a productores (72% a SR y GA); propuesta de ceder 2 aviones a los municipios | Mendoza24 (10/9/2026) |
| 1/10/2026 | Pronóstico hídrico 2026-27: año húmedo | Todas las cuencas | Río Mendoza 1.780 hm³ (129% de la media de 1.378); Tunuyán 1.340 (media 1.210); Grande 3.470 (media 3.129); Potrerillos con 395 hm³ contra 203 un año antes | Los Andes; El Sol; Enolife (1/10/2026) |
| Sept.-oct. 2026 | Alerta por "Súper Niño" | Provincia | Pico proyectado de +2,5 °C (escenario central +1,8 °C), con mayor incidencia entre octubre y diciembre; riesgo de granizo, aluviones y hongos | Informe Digital; Sitio Andino; El Sol; La Nación (4/10/2026) |

## Problemáticas principales por tema

### 1. Heladas tardías: el riesgo número uno

- **Peso relativo:** según el Ministerio de Producción (Mendoza24, 10/9/2026), del total de hectáreas con pérdida de cosecha en el Oasis Sur desde 2016-17, el 76,3% correspondió a heladas y el 23,7% a granizo, sobre 136.809 ha denunciadas.
- **Recurrencia:** Diario San Rafael informa que en las últimas diez temporadas San Rafael acumuló 90.594 ha denunciadas por heladas (unas 9.060 ha/año) y General Alvear más de 45.600 ha (unas 4.560 ha/año). Una nota de La Nación cita al Ing. Agr. Alberto Ortiz Maldonado, ex decano de Ciencias Agrarias de la UNCuyo, quien en su libro "Distribución geográfica de los elementos meteorológicos principales y adversidades de Mendoza" afirma que "el total de la producción provincial sufre daños superiores al 35% al menos en una de cada diez cosechas por las heladas". En esa misma nota, un estudio de la DACC indica que "el 14,66% de las 67.000 hectáreas cultivadas" está expuesto a heladas.
- **Calendario:** el riesgo se concentra entre septiembre y mediados de noviembre. La helada más tardía recordada por técnicos fue un 13 de noviembre (Diario Uno). Las de 2026 llegaron muy temprano en el calendario de brotación (7 y 14 de septiembre).
- **Medición diferida:** a diferencia del granizo, el daño por helada recién se ve entre 30 y 45 días después (Ministerio de Economía, en Unidiversidad). Por eso la ley fija 20 días de observación antes de abrir las denuncias. Mientras tanto no hay datos oficiales: tras la helada del 6/10/2025 no se publicaron hectáreas, y para la del 7/9/2026 el Gobierno aclaró que "todavía no existe una cifra definitiva".
- **Defensa activa:** se usan calefactores, riego, ventiladores y aspersión, además de tratamientos hormonales en frutales. Sobre los ventiladores antihelada, Matías Manzanares, de la Asociación de Viñateros de Mendoza, dijo a Bichos de Campo: "Otro método que se está empezando a aplicar es el uso de un ventilador… Pero ahí ya hablamos de 9 o 10 millones de pesos". Esta inversión queda fuera del alcance del pequeño productor descapitalizado.

### 2. Granizo y el sistema antigranizo

- **Infraestructura de la DACC:** el Sistema Integral de Lucha Antigranizo se apoya en 4 pilares (defensa activa, defensa pasiva con incentivo a la malla, gestión del riesgo con RUT y compensación, e investigación). Cuenta con tres radares (dos de banda S y uno de banda C), cuatro aviones Piper PA-31T Cheyenne II, 12 generadores en superficie en el Valle de Uco, una red de pluviómetros, un modelo WRF de pronóstico y 23 estaciones meteorológicas.
- **Cambio de política:** en 2024-25 se interrumpieron los vuelos para priorizar el seguro agrícola. En 2025-26 volvieron solo en el Sur, por convenio con San Rafael. En septiembre de 2026 la Provincia evaluaba vender los aviones o cederlos a los municipios. El intendente de General Alvear, Alejandro Molero, advirtió: "No creo que este sea el año para dejar de tener la lucha antigranizo" (El Sol).
- **Datos en disputa:** San Rafael sostiene que el granizo afectó en promedio 5.300 ha/año entre 2005 y 2024, 2.300 ha en 2024-25 y 2.900 ha en 2025-26, frente a unas 11.000 ha/año entre 1993 y 1998, y lo presenta como prueba de que el sistema funciona. El ministro Vargas Arizu "puso en duda la solidez estadística" de esos datos (Mendoza24, 10/9/2026). Esta controversia ilustra la falta de una serie histórica auditable y compartida.
- **Defensa pasiva:** en el granizo de febrero de 2023 en el Este, los viñedos con malla se salvaron y las ciruelas no (Los Andes). Ante El Niño, el INTA recomendó revisar y reparar las mallas (29/9/2026). No encontré en la prensa relevada un costo actualizado por hectárea de malla antigranizo; es un dato pendiente que conviene pedir a la DACC o a proveedores.
- **Tendencia:** según Juan Rivera, investigador del Conicet citado por El Sol, "el granizo chico se está reduciendo, pero el grande, el más dañino, se está incrementando". Rivera se basa en estudios de EE. UU. y Europa y aclara que en Mendoza todavía no hay investigaciones sobre la frecuencia ni el tamaño del granizo. Un estudio suyo de 2020 en Frontiers concluyó que la lucha antigranizo "no influye en la frecuencia de los eventos de granizo" (Infobae, 9/3/2024).

### 3. Sequía, agua y riego

- En 2025-26 hubo sequía hidrológica moderada en los ríos Mendoza, Tunuyán, Diamante y Grande, con entre 58% y 63% de la media. El Atuel fue calificado como "escaso" (73%). El derrame real del Río Mendoza fue de 797 hm³ contra 845 pronosticados (El Sol). El INV citó la "sequía moderada y la menor disponibilidad de agua para riego" como factor de la menor cosecha 2026.
- Para 2026-27 el panorama se invierte. Tras nevadas récord, el DGI pronostica un año húmedo, y su sistema telemétrico de 118 estaciones remotas alimenta un boletín público (Enolife, 1/10/2026). El nuevo riesgo es el exceso: Irrigación y las organizaciones de productores coordinan para que los turnos de riego no coincidan con las lluvias y así evitar anegamientos y pudriciones (LV18, 29/9/2026).
- Los beneficios por emergencia incluyen la eximición del 50% del canon de riego superficial y subterráneo y una bonificación del 25% en la energía para riego (Radio Regional, 28/9/2026).

### 4. Zonda, lluvias, calor y El Niño

- El decreto de enero de 2024 incluyó el viento Zonda entre las causales de emergencia. En septiembre de 2026 un Zonda dejó 193 incidentes en la provincia (Minuto Ya).
- Para la temporada 2026-27 los especialistas advierten por mildiu (peronóspora), oídio y podredumbres de racimo. Recomiendan tratamientos preventivos antes de las lluvias, desbrote y deshoje, y controles después de cada tormenta (El Sol). Un técnico lo resumió así: "El Niño nos da agua en el río… pero nos la cobra desde el cielo" (Elonce). El ministro de Producción pidió inscribirse en el FCA, comprar fungicidas y limpiar los cauces.

### 5. Seguros, emergencia y ayudas

| Instrumento | Cobertura / monto | Requisitos y datos | Medio |
|---|---|---|---|
| Ley 9083 de Emergencia Agropecuaria | Emergencia: daño del 50-79%; desastre: ≥80%. Eximición de impuesto inmobiliario, 50% del canon de riego, 25% de la energía para riego | RUT al día; denuncia (mínimo 10% de afectación); tasación; Certificado de Daños | Radio Regional (28/9/2026); Sitio Andino |
| FCA 2024-25 | $1,5 millones/ha (específica granizo e integral); $600.000/ha (inicial) | Hasta 30 ha (antes 20); 3.500 adheridos; $7.300 millones pagados | Infocampo (13/8/2024); El Sol |
| FCA 2025-26 | $2 millones/ha (granizo); $800.000 (inicial granizo + helada); $2 millones (integral). Aporte desde $16.000/ha (Centro-Norte) hasta $51.000/ha (Sur) | +30% de aporte si hubo emergencia en 3 de los últimos 5 ciclos; cooperativas ACOVI con 10% de bonificación; anticipo de $1.754 millones a 279 productores con daño ≥90% (252 del Sur: 161 SR, 91 GA); unos 4.000 adheridos en el Sur | Prensa Gob. Mendoza; ACOVI; Sitio Andino; Diario NDI |
| FCA 2026-27 | Hasta $2,5 millones/ha (Diario Uno); otra nota menciona $1,5 millones/ha con aportes de $20.000 (Centro-Norte), $50.000 (Este) y $63.750 (Sur) | Inscripción del 20/8 al 20/9/2026; RUT actualizado al 31/7/2026; vigencia del 21/9/2026 al 31/5/2027; pago en cuotas, con suspensión de la cobertura por mora | Diario Uno; Radio Regional (26/8/2026) |
| Recuperagro (2022-23) | Apoyo al empleo, hasta 4 trabajadores por RUT de hasta 20 ha | $67,6 millones a 2.000 productores; cupo de 4.000 beneficiarios; $833,7 millones previstos | Infocampo (30/1/2023) |
| Refuerza Mendoza (2025) | 60% del Salario Mínimo, Vital y Móvil durante 3 meses para trabajadores rurales | Fincas de hasta 60 ha en zonas en emergencia (Decreto 1096, en el marco del Decreto 43/25) | El Sol |
| FTyC: cosecha y acarreo 2026 | $7.000/qq (uva no varietal) y $9.000/qq (varietal) | Productores de hasta 20 ha | Prensa Gob. Mendoza |

Hay dos alertas sobre estos datos. Primero, los montos del FCA 2026-27 difieren entre medios, así que conviene verificar el reglamento en el Boletín Oficial. Segundo, el reglamento de tasación 2026-27 (Resolución 24/2026 de la DCC) asigna un perito adicional cada 300 ha y fija criterios por cultivo y estado fenológico (El Sol), es decir, reglas de negocio que el sistema debería parametrizar.

### 6. Economía: precio de la uva, costos y abandono

- **Precio por debajo del costo por tercer año seguido:** la uva se paga entre $140 y $150/kg contra un costo real de $200 a $240/kg, según Matías Manzanares (AVM) en Diario Uno. La uva para mosto ronda los $200/kg, el mismo valor nominal que hace dos años (Sitio Andino), y los productores dicen que no puede bajar de $500/kg. Bichos de Campo habla de pérdidas de hasta USD 2.000/ha y de viñateros que evaluaban no levantar la cosecha.
- **Diagnóstico gremial:** la Asociación de Viñateros de Mendoza habló de "una de las peores crisis de rentabilidad que hayamos vivido en décadas" (Bichos de Campo, 17/10/2025). En junio de 2026 denunció rindes de menos de 60 litros por quintal, abandono creciente de hectáreas y falta de controles del INV en bodega (Infomendoza, 9/6/2026; Mundo Empresarial, 28/6/2026). Sin anticipos de las bodegas, los productores no tienen fondos para la poda y la atadura.
- **Retroceso estructural:** según el Informe Anual de Superficie 2024 del INV, el país quedó en 199.946 ha en 22.039 viñedos al 31/12/2024, con 4.901 ha y 988 viñedos menos que en 2023; La Nación (4/3/2025) lo describió como "el peor registro en 34 años". En la verificación de 2024 el INV dio de baja en Mendoza 535 viñedos con 3.957,7 ha.

### 7. Contratistas de viña y trabajo rural

- **Esquema de pago:** el contratista cobra una mensualidad por hectárea más el 15-18% de la producción. En octubre de 2025 la mensualidad era de $32.100/ha (unos $321.000 por 10 ha); el gremio pedía $60.000/ha y el ingreso básico promedio rondaba los $273.000 (Los Andes; Enolife). El obrero de viña (CCT 154/91) tenía un básico cercano a $600.000, y la escala FOEVA de enero de 2026 marcaba $412.803 más montos no remunerativos (Mendoza Post).
- **Impacto del clima en el contratista:** como su porcentaje depende de lo cosechado, una helada o un granizo le recortan el ingreso tanto como al dueño. Hay casos documentados, como un contratista que perdió el 99% de la producción en 2023 (Mendoza Post). Ya en 2023 los contratistas se quejaban de que "los programas de ayuda de la Provincia y de la Nación son para los patrones" (El Otro Diario).
- **Pagos demorados:** en octubre de 2025 había contratistas que habían cosechado entre febrero y abril y aún no sabían cuándo cobrarían su porcentaje (Enolife). El productor tampoco cobra a tiempo, porque las bodegas pagan en cuotas.
- **Cosecha:** FOEVA estimó para 2026 una caída del 30% en el valor del tacho, con pagos de $320 a $350 contra unos $550 en 2025 (Diario de Cuyo, con foco sanjuanino; Diario NDI, 4/10/2026, para Mendoza). Hay informalidad y trabajadores sin registrar, según el gremio de contratistas.

### 8. Información y gestión de datos: el vacío central

- **Cifras tardías y contradictorias:** las mismas noticias muestran estimaciones oficiales que cambian con el tiempo. En noviembre de 2022 se hablaba de 20.000 ha, luego de 26.000 y luego de 30.000 con pérdida total. Las cifras sobre el granizo (San Rafael frente a la Provincia) se contradicen. La caída de Mendoza en 2026 figura como −8%, −9% o −12,4% según la base de comparación (Los Andes compara 15.044.810 qq de 2025 con 13.181.415 de 2026; el INV informa 13.147.187 qq).
- **Cobertura meteorológica desigual:** la ficha de la SAGyP/Fondagro "Proyecto de Adquisición de Estaciones Meteorológicas en San Rafael Mendoza" (argentina.gob.ar) describe un aporte no reembolsable pedido por la COVIAR para el Este (La Paz, Santa Rosa, Junín, Rivadavia, San Martín), zona que concentra cerca del 50% de la vitivinicultura, y afirma que "contingencia climática del gobierno de Mendoza no tiene instalada estaciones meteorológicas ni en la zona del este ni en sus cercanías". Las alertas de heladas se brindan del 1/8 al 30/11 por internet, teléfono y radio VHF, sin un canal de datos abiertos interoperable.
- **Registros duplicados:** el RUT (Provincia), el Registro de Viñedos y las Declaraciones Juradas de cosecha y elaboración (INV), los turnos y padrones de riego (DGI) y los certificados de daños (DCC) usan identificadores distintos (CUIT, número de viñedo INV, padrón de riego, RUT). El productor debe actualizar datos en varios lugares, y estar en el RUT es condición excluyente para cobrar.
- **Iniciativas existentes:** PromeTEO (red de sensores de temperatura y humedad para viñedos, UTN), estaciones privadas, ventiladores con activación automática por umbral (Grupo Halpern), el boletín hidronivometeorológico del DGI y una herramienta Conicet-INTA para medir el impacto de El Niño en los cultivos. Todas son piezas aisladas.

## Tabla de datos cuantitativos clave

| Indicador | Valor | Fecha / período | Fuente (medio) |
|---|---|---|---|
| Superficie de vid en Mendoza | 140.682 ha; 14.371 viñedos; 71,7% del país; tamaño medio 9,8 ha | 31/12/2025 | INV, Informe Anual de Superficie (Agroempresario, 15/9/2026) |
| Serie de superficie en Mendoza | 147.379 (2022) → 145.393 (2023) → 142.785 (2024) → 140.682 ha (2025) | 2022-2025 | INV (Uvas Argentinas; Infomendoza; CEPA) |
| Pérdida de superficie en Mendoza en una década | −17.903 ha (−11,3%) | 2016-2025 | INV |
| Superficie nacional | 196.220 ha; 20.939 viñedos | 31/12/2025 | INV |
| Concentración | 75% de los viñedos <10 ha = 25,8% de la superficie; >25 ha = 44,7% | 2024 | CEPA Mendoza (oct. 2025) |
| Cosecha en Mendoza | 14.791.253 qq (2025) → 13.147.187 qq (2026) | 2025-2026 | INV (El Descorche; Revista Chacra) |
| Cosecha nacional 2026 | 18.391.299 qq (−8%) | mayo 2026 | INV (Revista Chacra, 20/5/2026) |
| Malbec en Mendoza 2026 | 3,24 millones de qq | 2026 | Los Andes |
| Helada de 2020 | 30.373 ha de vid; 24% de daño medio; 5.394 denuncias | oct. 2020 | Los Andes (2/1/2021) |
| Helada de 2022 | ~10.000 ha de vid + 10.000 de frutales; 135 distritos | nov. 2022 | La Nación; Infocampo |
| Pérdida total por helada + granizo | 26.000 ha (hasta 30.000) | ene. 2023 | Infocampo |
| Hectáreas denunciadas en el Oasis Sur | 136.809 ha (76,3% heladas / 23,7% granizo) | 2016-17 a 2025-26 | Min. Producción (Mendoza24) |
| Promedio de heladas en San Rafael / Gral. Alvear | ~9.060 / ~4.560 ha por año | última década | Diario San Rafael |
| Granizo en San Rafael | 5.300 ha/año (2005-24); 2.300 (2024-25); 2.900 (2025-26) | — | Municipalidad de San Rafael (Mendoza24) |
| Histórico de la DACC (temporada 2018-19) | Heladas 8.608 ha; promedio histórico de granizo 20.528 ha; Sur 51,7% y Este 36,2% de los daños | 2019 | Prensa Gob. Mendoza |
| Transferencias por contingencias | >$14.000 millones (72% a SR y GA) | última temporada | Mendoza24 (10/9/2026) |
| Río Mendoza, derrame | 1.370 hm³ (24-25) → 797 (25-26) → 1.780 pronosticados (26-27) | 2024-2027 | DGI |
| Potrerillos | 203 hm³ (28/9/2025) → 395 hm³ (28/9/2026) | — | DGI (Los Andes) |
| Precio de la uva frente al costo | $140-150/kg frente a $200-240/kg | 2026 | AVM (Diario Uno) |
| Mensualidad del contratista | $32.100/ha + 15-18% de la producción | oct. 2025 | Los Andes; Enolife |
| Tacho de cosecha | $320-350 (2026) frente a ~$550 (2025) | feb. 2026 | FOEVA (Diario de Cuyo; Diario NDI) |
| Temperatura mínima en la helada del 7/9/2026 | −8,3 °C en Monte Comán | 7/9/2026 | Minuto Ya; San Rafael Digital |

## Necesidades y vacíos de información detectados

1. **Una sola "verdad" georreferenciada por evento.** Hoy la manga de radar, las denuncias y las tasaciones se publican por separado y tarde. Falta poder responder rápido qué parcelas, de qué variedad y en qué estado fenológico quedaron dentro del polígono de un granizo o bajo un umbral de helada.
2. **Series históricas auditables** de daños por evento, distrito y cultivo. La discusión sobre la eficacia de los aviones muestra que no existen o no son públicas.
3. **Cobertura meteorológica en tiempo real en el Este** y una integración de estaciones públicas (DACC, DGI, SMN, INTA) y privadas (bodegas, sensores IoT).
4. **Trazabilidad económica del contratista:** su porcentaje, la uva entregada, la bodega, el precio y el calendario de pagos. Hoy no figura en ningún registro público y queda fuera de las ayudas.
5. **Interoperabilidad de identificadores** (CUIT, RUT, número de viñedo INV, padrón del DGI) para no duplicar trámites ni perder beneficios.
6. **Datos de costos:** malla por hectárea, defensa activa, labores y cosecha. Son dispersos y no aparecen actualizados en la prensa.
7. **Alertas personalizadas** por parcela, según el estado fenológico y la temperatura crítica, en lugar de avisos genéricos por oasis.

## Oportunidades: entidades y datos para modelar en MongoDB

### Colecciones propuestas

| Colección | Contenido principal | Patrón / índice MongoDB |
|---|---|---|
| `productores` | CUIT, nombre, RUT, cooperativa (ACOVI, etc.), contacto, fincas[] (referencias) | Índice único en `cuit` y en `rut` |
| `contratistas` | CUIT, contratos[] embebidos (finca, ha, mensualidad/ha, % de producción, vigencia), pagos[] | Embebido acotado; índice en `contratos.fincaId` |
| `fincas` | Ubicación (Polygon GeoJSON), departamento, distrito, oasis, padrón DGI, derecho de riego | `2dsphere` en `geometria`; compuesto `{oasis, departamento}` |
| `parcelas` (cuarteles) | fincaId, número de viñedo INV, variedad, año de plantación, conducción, malla (sí/no, año), defensa antihelada, fenología actual | `2dsphere`; `{fincaId, variedad}` |
| `estaciones` | Tipo (DACC, DGI, INTA, privada, IoT), Point GeoJSON, sensores | `2dsphere` para la estación más cercana |
| `lecturas` | Temperatura, humedad, viento, lluvia, temperatura de bulbo húmedo | **Colección de series temporales** (`timeField: ts`, `metaField: {estacionId, tipo}`, `granularity: "minutes"`); TTL opcional para datos crudos |
| `eventos_climaticos` | Tipo (helada, granizo, zonda, lluvia), inicio y fin, polígono afectado (manga de radar), intensidad, temperatura mínima, fuente | `2dsphere`; `{tipo, inicio}` |
| `siniestros` (denuncias) | parcelaId, eventoId, fecha de denuncia, % de daño tasado, perito, estado (denunciado → tasado → certificado), categoría según la Ley 9083 | Validación con `$jsonSchema`; `{estado, eventoId}` |
| `seguros` (FCA) | Temporada, modalidad (específica, inicial, integral), ha cubiertas, aporte, cuotas[], mora, indemnización | `{productorId, temporada}` único |
| `emergencias` | Decreto o resolución (125/2026, 765/2026), vigencia, distritos[], tipo | Índice por `distritos` (multikey) |
| `cosechas` | parcelaId, temporada, quintales, bodega, destino (vino o mosto), precio/kg, plan de pagos[] | `{temporada, departamento}` para agregaciones |
| `tareas_costos` | Labor (poda, atadura, curación, cosecha), fecha, costo, responsable (contratista u obrero) | Patrón *bucket* por parcela y temporada |
| `alertas` | Regla (por ejemplo, temperatura < −1,5 °C en floración), destinatarios, estado | Change streams sobre `lecturas` |
| `hidrologia` | Pronóstico de escurrimiento por río, embalses, turnos de riego | Series temporales mensuales |

### Consultas tipo que el sistema debería resolver

- **Impacto geoespacial:** "Parcelas de Malbec en floración dentro del polígono del granizo del día X", con `$geoIntersects` sobre `eventos_climaticos.geometria` y filtros por variedad y fenología.
- **Horas de helada:** con `$setWindowFields` o `$group` por estación y día, sumar los minutos bajo 0 °C (en San Rafael se reportaron más de 70 horas acumuladas en septiembre de 2026) y cruzarlos con las parcelas cercanas mediante `$geoNear`.
- **Pérdidas por departamento y temporada:** `$lookup` de siniestros → parcelas → fincas y `$group` por `{departamento, tipoEvento}`, para reconstruir series como el 76,3% frente al 23,7% del Oasis Sur.
- **Brecha de cobertura:** productores con daño ≥50% sin FCA vigente o en mora, usando `$lookup` con `seguros` filtrado por temporada.
- **Ingreso del contratista:** mensualidad × ha + porcentaje × quintales × precio, menos lo ya pagado, según la fecha de cobro de la bodega.
- **Rentabilidad:** costo/ha desde `tareas_costos` frente al ingreso/ha desde `cosechas`, para detectar fincas en riesgo de abandono.

### Ejemplo de documento (siniestro)

```json
{
  "_id": "SIN-2026-000123",
  "parcelaId": "PAR-SR-0456",
  "eventoId": "EVT-HEL-2026-09-07",
  "tipoEvento": "helada",
  "fechaEvento": "2026-09-07",
  "ventanaDenuncia": {"desde": "2026-09-28", "hasta": "2026-10-09"},
  "fenologia": "brotacion",
  "tasacion": {"perito": "DCC-0897", "danioPct": 82, "fecha": "2026-10-20"},
  "categoriaLey9083": "desastre",
  "certificado": {"nro": "CD-26-5521", "emitido": true},
  "seguroFCA": {"temporada": "2026-27", "modalidad": "integral", "indemnizacionEstimada": 2500000},
  "estado": "certificado"
}
```

## Recomendaciones para el proyecto de BDII

1. **Centrar el caso de uso en heladas tardías del Oasis Sur y el Este.** Es donde las fuentes concentran pérdidas (San Rafael, General Alvear, San Martín) y donde falta información en tiempo real.
2. **Modelar el ciclo completo del siniestro como máquina de estados** (evento → denuncia → tasación → certificado → emergencia → indemnización), con las reglas de la Ley 9083 (50-79% y ≥80%) y los plazos (10 días hábiles; 20 días de observación más 10 hábiles en heladas).
3. **Usar colecciones de series temporales** para las lecturas de sensores y estaciones, y `2dsphere` para fincas, estaciones y eventos. Es el diferencial técnico más defendible frente a un modelo relacional.
4. **Incluir al contratista como entidad de primer nivel.** Ningún sistema público lo hace, y su ingreso depende directamente del clima y del calendario de pago de las bodegas.
5. **Cargar datos semilla reales:** superficie por departamento del INV 2025, cosechas 2025-2026, pronósticos del DGI y los eventos de la cronología anterior, para demostrar agregaciones con cifras verificables.

## Caveats

- **Cifras de 2025-26 y 2026 incompletas:** no encontré cifras oficiales en hectáreas para las heladas del 6/10/2025, el granizo de enero y febrero de 2026 ni la helada del 7/9/2026 (las denuncias cierran el 9/10/2026). Algunos titulares que circulan, como "24.000 ha con pérdida total" o "100.000 ha perdidas", corresponden a temporadas anteriores (2022-23) y no deben atribuirse a 2026.
- **Discrepancias entre medios:** la variación de la cosecha mendocina 2026 aparece como −8%, −9% o −12,4%, y los montos del FCA 2026-27 difieren entre Diario Uno y Radio Regional. Conviene ir a la fuente primaria (INV, Boletín Oficial).
- **Datos sanjuaninos:** el dato del tacho de 2026 proviene de FOEVA con foco en San Juan, retomado por un medio mendocino. Las notas sobre falta de cosechadores (unos 18.000 necesarios, tacho a $300-500) son de 2024.
- **Proyecciones:** el escenario de "Súper Niño" es un pronóstico (pico de +2,5 °C, escenario central +1,8 °C), no un hecho consumado. Sus efectos sobre el granizo y las enfermedades son riesgos, no daños registrados.
- **Fuentes de parte:** varias cifras económicas provienen de gremios (AVM, FOEVA, contratistas) o de municipios con interés en la discusión, como San Rafael con los aviones, y deben leerse como posiciones de parte.
