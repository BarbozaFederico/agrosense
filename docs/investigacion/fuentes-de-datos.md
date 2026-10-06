> **Documento de trabajo.** Relevamiento de fuentes abiertas de datos (octubre de 2026). Las afirmaciones de prensa deben verificarse en la fuente primaria. Se quitaron datos de contacto personales (correos) por ser el repositorio público. El MVP usa datos sintéticos; ver [`../vision.md`](../vision.md).

# ¿Hay datos públicos para el MVP de monitoreo de viñedos en Mendoza? Informe de fuentes abiertas (octubre 2026)

**Respuesta corta: sí, varios organismos publican de forma abierta temperatura y humedad del aire de Mendoza, y hay alertas de helada oficiales. En cambio, nadie publica de forma abierta humedad de suelo medida in situ en viñedos de Mendoza, ni datos de turnos de riego en formato reutilizable.** Para el MVP conviene usar datos reales en dos tareas: calibrar los perfiles de helada y validar el simulador. La humedad de suelo por parcela y los nodos de sensores tienen que seguir siendo simulados.

## TL;DR

- **Temperatura y humedad del aire: SÍ se publican de forma abierta.** El SMN publica datos horarios de todo el país, descargables en ZIP desde datos.gob.ar. El SIGA del INTA tiene descarga libre, con datos horarios de estaciones automáticas. La Dirección de Contingencias Climáticas (DACC) de Mendoza muestra en su web datos actuales y estadísticos de su red propia de los oasis. Pero la DACC no ofrece descarga masiva: sus series horarias históricas se piden por correo.
- **Alertas de helada: SÍ se publican, pero como texto o pronóstico, no como dataset.** La DACC opera un Sistema de Pronóstico, Alerta y Prevención de Heladas del 1 de agosto al 30 de noviembre. El SMN emite alertas por frío extremo con umbrales de percentil 10 y publica un dataset de alertas de 365 días. Los umbrales de daño para la vid por estado fenológico están publicados en un informe del IDR y la DACC (−1,1 °C en corola visible; −0,6 °C en plena flor y fruto cuajado).
- **Humedad de suelo y riego: NO hay datos abiertos in situ para viñedos de Mendoza.** El mapa de humedad SAOCOM de la CONAE cubre solo la región pampeana. La alternativa práctica es el reanálisis ERA5-Land, vía Open-Meteo (CC BY 4.0) o NASA POWER. El DGI publica boletines PDF diarios y caudales telemétricos en la web, pero los turnos son datos de cada usuario y no un dataset abierto.

## Key Findings: respuesta variable por variable

| # | Variable / alerta | Veredicto | Quién y cómo |
|---|---|---|---|
| 1 | Temperatura del aire (mínimas, horaria) | **SÍ, abierta** | SMN (datos.gob.ar, ZIP diario); INTA SIGA (descarga libre); DACC (web, sin descarga masiva) |
| 1b | Datos de heladas (registros, riesgo) | **SÍ, con limitaciones** | DACC: "Riesgo de heladas", "Horas y unidades de frío", caracterizaciones vitícolas en PDF; solo web/PDF |
| 2 | Humedad relativa del aire | **SÍ, abierta** | SMN horario; DACC (temperatura, humedad y punto de rocío en la web); Datos Abiertos Mendoza (CSV 2016, una estación urbana) |
| 3 | Humedad de suelo in situ en viñedos | **NO se publica de forma abierta** | No se encontró ningún ente que la publique. Alternativas: ERA5-Land (Open-Meteo), simulación, convenio con una bodega o con el INTA |
| 3b | Humedad de suelo satelital/modelada | **SÍ, con limitaciones** | CONAE SAOCOM: libre, pero solo región pampeana. Open-Meteo/ERA5-Land: global, grilla de 0,1° (resolución nativa de 9 km según Copernicus) |
| 4 | Alertas y pronósticos de helada | **SÍ, con limitaciones** | DACC: pronóstico de la mínima y alerta por oasis (web, radio, teléfono). SMN: SAT y dataset de alertas. No hay API de alertas agrícolas |
| 5a | Caudales y boletín hídrico (DGI) | **SÍ, con limitaciones** | Boletín Hidronivometeorológico en PDF (días hábiles); telemetría de canales en la web (l/s); sin API |
| 5b | Turnos de riego | **NO, como dataset abierto** | Consulta individual por padrón o titular (Oficina Virtual, AsIC, Subdelegación Malargüe) |
| 5c | ET0 y balance hídrico | **SÍ, con limitaciones** | DACC tiene una sección de "Evapotranspiración" (web). Se puede calcular ET0 con FAO-56 a partir de datos del SMN o el INTA. ET0 directa en Open-Meteo/NASA POWER |
| 5d | Recomendaciones de riego para vid | **No se verificó un servicio abierto** | No se encontró ninguna publicación sistemática y reutilizable |

## Details

### 1. Servicio Meteorológico Nacional (SMN)
- **Qué publica:** en el portal nacional datos.gob.ar, el SMN tiene los datasets "Datos meteorológicos horarios" (temperatura, presión, viento y humedad de las estaciones de superficie de todo el país), "Registro de Temperatura (365 días)" (máximas y mínimas diarias del último año), "Observaciones diarias de Temperaturas Extremas", "Listado de Estaciones Meteorológicas" y "Alertas Meteorológicas (365 días)".
- **Formato y frecuencia:** ZIP con actualización diaria. El recurso horario apunta a `https://ssl.smn.gob.ar/dpd/zipopendata.php?dato=datohorario`. La ficha del dataset horario dice "No se especificó la licencia". El portal datos.gob.ar declara en general: "Los datos publicados acá son públicos y se pueden reutilizar libremente citando la fuente".
- **Limitaciones:** el archivo horario parece ser un volcado diario y no una serie histórica larga; no se verificó cuántos días incluye. Para series largas hay que acumular los archivos todos los días, o recurrir al Banco de Datos del DCAO-UBA, que tiene registros horarios y diarios del SMN de 1991 a octubre de 2016 por pedido académico ("pueden realizar el pedido por email"). La red del SMN en Mendoza es poco densa (estaciones sinópticas, sobre todo en aeropuertos y ciudades) y no representa el microclima de un viñedo. No se verificó la lista exacta de estaciones de Mendoza; hay que consultar el dataset "Listado de Estaciones".

### 2. INTA – SIGA (Sistema de Información y Gestión Agrometeorológica)
- **Qué publica:** datos actuales e históricos de estaciones del INTA y de algunas externas. Según la documentación del SIGA, la "Red EMA = Datos Horarios + Datos Diarios" (estaciones automáticas) y la "Red EMC = Datos Diarios (Reciente + Histórico)" (convencionales). El INTA lo presenta como una base "de libre descarga". La página de Información Agroclimática de argentina.gob.ar dice: "Todos los datos son de libre descarga".
- **Mendoza:** el Centro Regional Mendoza-San Juan tiene EEA en Luján de Cuyo, Junín, La Consulta y Rama Caída, y el SIGA las lista bajo "Mendoza - San Juan". No se verificó cuántas estaciones automáticas hay en Mendoza ni si cada una tiene datos horarios.
- **Acceso programático:** el INTA mantiene el paquete de R `{siga}` (GitHub AgRoMeteorologiaINTA), que descarga metadatos y datos en CSV con `siga_estaciones()`, `siga_datos()` y `siga_descargar()`. Sus ejemplos usan datos diarios, por ejemplo la variable `temperatura_abrigo_150cm_maxima`. **No se verificó** que la web permita descargar datos horarios en CSV, ni la licencia formal de los datos. El sitio bloquea el acceso automatizado, así que ese punto queda pendiente de verificar a mano.

### 3. Dirección de Agricultura y Contingencias Climáticas (DACC), Gobierno de Mendoza
- **Red:** estaciones propias en los tres oasis, con central de datos en Tunuyán. La unidad lógica "realiza la lectura cada 1 minuto de todos los sensores" y, al cierre de cada hora, calcula el máximo, el medio y el mínimo de cada sensor. La temperatura del aire y la humedad relativa se miden a **1,80 m**, la temperatura del suelo a 0 m y la "temperatura profunda" a −10 cm. **No miden humedad de suelo.**
- **Qué publica en la web:** "Datos Actuales" (tablas HTML con nombre, hora, temperatura, humedad y punto de rocío), "Datos Estadísticos – Mensuales/Anuales", "Horas y unidades de frío", "Evapotranspiración", "Caracterización Vitícola" (PDF por temporada) y "Riesgo de heladas". En la tabla de datos instantáneos, por ejemplo, la estación 1 registró 5,1 °C, 56 % de humedad y −2,6 °C de punto de rocío el 28/08/2025 a las 04:22. Ese aire seco es típico del riesgo de helada negra.
- **Limitaciones:** no se encontró descarga en CSV ni API; solo hay tablas web y PDF. Las series se piden por correo al área de Agrometeorología de la DACC (contacto en la sección "Pedido de información" de su sitio; se omite aquí la dirección personal). La DACC no publica una cifra oficial del tamaño de la red: su página de Pronóstico Meteorológico solo la nombra como "red de estaciones telemétricas Meteorólogo Carlos Bustos", y el sitio del Ministerio de Producción habla de "estaciones meteorológicas propias distribuidas en todo el territorio" y de "cuatro radares meteorológicos" con sistema TITAN. Un proveedor comercial (Agrometrix) habla de una "Red de 12 estaciones meteorológicas", y una nota oficial menciona que la de Dubois-Tupungato es "la novena estación que la DCC posee en el Valle de Uco". Es una fuente secundaria y quizás desactualizada.
- **Sistema de Pronóstico, Alerta y Prevención de Heladas:** según la DACC, asesora "en forma continua durante las 24 horas, desde el 1º de agosto hasta el 30 de noviembre de cada año" con el pronóstico extendido, el "pronóstico de la mínima probable para el día siguiente", parámetros en tiempo real y "las temperaturas críticas para cada estado fenológico". Se difunde por Internet, teléfono, radio VHF y radios AM/FM. El pronóstico diario se actualiza a las 17 h con los modelos WRF del SMN y del NCEP, imágenes GOES y la red telemétrica. Los medios reproducen esas alertas con mínimas por zona (por ejemplo, Los Andes: "en el Valle de Uco se esperan marcas de -2.5 a 0.5°C").

### 4. Departamento General de Irrigación (DGI)
- **Boletín de Información Hidronivometeorológica:** PDF que se publica en días hábiles. Contiene valores medios diarios de estaciones del Sistema Telemétrico, "compuesto por 118 estaciones remotas": volúmenes de embalses, caudales medios diarios de ríos (m³/s), equivalente agua-nieve y meteorología de alta montaña. Sirve para el contexto hídrico (año seco o húmedo) y no para la parcela.
- **Telemetría de red primaria:** hay una página web pública con altura (cm) y caudal (l/s) de canales e hijuelas, con fecha y hora (por ejemplo, "100 - Rama Jarillal Carrodilla · Caudal: 2841.0 l/s · 24/09/2026"). Es solo visualización, sin API documentada.
- **Turnos de riego:** cada Inspección de Cauce arma sus cuadros de turno, con tiempos "proporcionales a la superficie que cada usuario tiene". Se consultan uno por uno (por padrón o titular en la Subdelegación Malargüe; registro por correo en AsIC Primera Zona). **No hay un dataset abierto de turnos.**
- **Pronóstico de escurrimientos:** se publica por temporada (por ejemplo, 2026/2027, anticipado como año "húmedo" en la cuenca del río Mendoza).

### 5. Humedad de suelo: satélite y reanálisis
- **CONAE – SAOCOM:** el Mapa de Humedad del Perfil de Suelo hasta 50 cm y el "Visor de series temporales" (10 capas hasta unos 2 m) son de acceso "libre y abierto", pero **solo para la región pampeana**, de modo que no sirven para Mendoza. Para productos L1 de archivo hay que registrarse y aceptar una licencia en línea, y hay que citar "Producto SAOCOM® - ©CONAE".
- **Open-Meteo (ERA5 / ERA5-Land):** API JSON/CSV sin clave. Según su documentación, la serie horaria desde 1940 corresponde a ERA5 (0,25°, unos 25 km), mientras que ERA5-Land (0,1°), el que trae la humedad de suelo, empieza en 1950, con capas de 0–7, 7–28, 28–100 y 100–255 cm. Los datos tienen licencia CC BY 4.0, y según los términos de uso de Open-Meteo el uso no comercial es gratuito por debajo de 10.000 llamadas diarias, 5.000 por hora y 600 por minuto. Según la ficha de Copernicus CDS, ERA5-Land tiene una resolución nativa de 9 km sobre una grilla de 0,1° × 0,1° (Open-Meteo la indica como "0.1° (~11 km)").
- **NASA POWER:** API gratuita con endpoints horarios y diarios y comunidad "ag" (agroclimatología). Según el tutorial oficial de NASA POWER, su resolución es de 0,5° × 0,625° para meteorología (unos 50 km) y de 1° × 1° para parámetros solares, sobre la base del reanálisis MERRA-2 (NASA/GMAO): demasiado gruesa para distinguir parcelas.
- **SISSA / CRC-SAS:** sus índices de sequía basados en estaciones se descargan en CSV desde el visor, pero para la API hay que pedir una clave por correo. No se verificó que ofrezca humedad de suelo descargable.

### 6. Otras fuentes revisadas
- **Datos Abiertos Mendoza (provincial):** dataset "Registro de mediciones de Calidad del aire – Meteorología" (temperatura, humedad relativa, viento y lluvia de la estación de la Secretaría de Ambiente) en CSV, solo para 2016, con licencia ODbL. Es una estación urbana: sirve como ejemplo de importación, no para viñedos.
- **IDR + DACC:** el informe "Evolución Fenológica Frutales 2021" publica la tabla de temperaturas críticas de daño (ver la sección de umbrales).
- **UTN – PromeTEO:** es una red de sensores de temperatura y humedad para viñedos, nacida como tesis de la UTN **Regional Buenos Aires** y no de la Regional Mendoza. No se encontró que publique datos abiertos.
- **No verificados en esta investigación** (no se consultaron sus páginas por límite de búsqueda; no hay que suponer que publiquen o no publiquen): INV, COVIAR/Fondagro, IANIGLA, IDE Mendoza/SIAT, Defensa Civil, Bolsas, UNCuyo (FCA/IBAM), Meteostat, NOAA GHCN, NASA SMAP, Copernicus Global Land, CHIRPS, Google Earth Engine, Weather Underground y las redes privadas (Davis WeatherLink, Metos/FieldClimate, ZENTRA, Sensoterra). Las redes privadas suelen exigir cuenta del dueño de la estación. Es una inferencia, no una verificación.

### Tabla comparativa

| Ente | Variable(s) | Cobertura en Mendoza | Frecuencia | Formato | Serie histórica | Licencia y acceso | Enlace |
|---|---|---|---|---|---|---|---|
| SMN | T, HR, viento, presión; Tmáx/Tmín; alertas | Estaciones sinópticas (pocas) | Horaria, actualización diaria | ZIP (texto) | 365 días (temp. y alertas); horario: no verificado | Libre; "No se especificó la licencia" (datos.gob.ar: reutilización citando la fuente) | datos.gob.ar/dataset/smn-datos-meteorologicos-horarios |
| INTA SIGA | T (abrigo 1,5 m), HR, lluvia, etc. | EEA Mendoza, Junín, La Consulta, Rama Caída (cantidad no verificada) | Horaria (EMA) / diaria (EMC) | Web + CSV (paquete R `{siga}`) | Sí, histórica | "Libre descarga"; licencia formal no verificada | inta.gob.ar/unidades/212000/siga |
| DACC Mendoza | T y HR (1,80 m), rocío, T suelo, ET0, horas de frío, riesgo de heladas | Red propia en los 3 oasis | Lectura cada 1 min, agregación horaria | Web (HTML/PHP), PDF | Mensual/anual en web; horaria por pedido | Visualización libre; series por correo | mendoza.gov.ar/contingencias/agrometeorologia |
| DACC – Alerta heladas | Mínima pronosticada, alerta por oasis | 3 oasis | Diaria (17 h), 1/8–30/11 | Web, radio, teléfono | No como dataset | Libre (difusión) | contingencias.mendoza.gov.ar/alerta_y_prevencion_heladas.php |
| DGI | Caudales, embalses, nieve, meteo de alta montaña | Toda la provincia (118 estaciones remotas) | Diaria (días hábiles); telemetría casi en tiempo real | PDF; web | PDFs por fecha | Libre (visualización) | irrigacion.gov.ar/web/pronostico |
| CONAE SAOCOM | Humedad de suelo (0–50 cm) | **No cubre Mendoza** (solo región pampeana) | Por pasada / diaria (modelo) | GeoTIFF, WMS | Desde 2020 aprox. | Libre con registro y licencia | argentina.gob.ar/ciencia/conae/productos-saocom |
| Open-Meteo (ERA5/ERA5-Land) | T, HR, humedad de suelo, ET0 | Global, grilla de 0,1° (9 km nativos, ERA5-Land) | Horaria | API JSON/CSV | ERA5 desde 1940; ERA5-Land desde 1950 | CC BY 4.0; gratis no comercial (<10.000 llamadas/día, 5.000/hora, 600/minuto) | open-meteo.com |
| NASA POWER | T2M, RH2M, lluvia, radiación | Global, 0,5° × 0,625° (MERRA-2) | Horaria/diaria | API CSV/JSON/NetCDF | Desde 1981 (diaria) | Libre (política de datos de NASA) | power.larc.nasa.gov |
| SISSA / CRC-SAS | Índices de sequía (SPI, CDI) | Estaciones regionales y grilla CHIRPS | Mensual/decádica | CSV (visor); API con clave | Sí | Clave por correo para la API | sissa.crc-sas.org |
| Datos Abiertos Mendoza | T, HR, viento, lluvia (estación urbana) | Ciudad de Mendoza | No declarada (2016) | CSV | Solo 2016 | ODbL | datosabiertos.mendoza.gov.ar |

### Umbrales y criterios oficiales de helada y riego en vid

- **Temperaturas críticas por estado fenológico (IDR + DACC, informe 2021, Cuadro 2):** vid −1,1 °C en estado D (corola visible), −0,6 °C en estado F (plena flor) y −0,6 °C en estado H (fruto cuajado). El informe usa la escala de estados D, F y H propia de frutales. No se encontró en esta investigación un umbral oficial de la DACC para brotación de la vid, aunque la DACC dice que informa "las temperaturas críticas para cada estado fenológico" durante la temporada. Como referencia periodística (Los Andes, sin firma institucional verificada): las yemas dormidas resisten "hasta -15 °C" y los brotes verdes, "entre -2 a -5 °C".
- **Período de riesgo:** la alerta funciona del 1 de agosto al 30 de noviembre. Según la DACC citada por la prensa, el riesgo se vuelve alto "desde mediados de agosto", con la brotación.
- **Altura y abrigo:** las estaciones de la DACC miden la temperatura del aire a 1,80 m. El SIGA del INTA usa la variable "temperatura_abrigo_150cm", es decir, la temperatura en abrigo a 1,5 m. Un técnico citado por Campo Andino advierte que, fuera del abrigo, "la temperatura puede ser hasta un grado más baja". Es un dato operativo útil para un offset del simulador.
- **Humedad y punto de rocío:** la DACC explica que con aire seco "el riesgo es mayor (helada negra)" y que las nubes y el viento reducen el riesgo. No se encontró un criterio oficial publicado basado en el **bulbo húmedo**; eso queda sin verificar.
- **SMN:** el SAT emite alertas por frío extremo con umbrales del percentil 10 (P10) de las temperaturas máximas y mínimas. Sube de nivel según la persistencia del evento y la probabilidad de superar P5 o P1. Los umbrales del SMN no son agronómicos ni distinguen estados fenológicos.
- **Riego:** no se encontró un umbral oficial abierto de humedad de suelo o de déficit para disparar el riego de la vid en Mendoza. El estándar técnico publicado es FAO-56 (Penman-Monteith) para calcular la ET0, que requiere radiación, temperatura, humedad y viento, o como mínimo Tmáx y Tmín.

## Recommendations

1. **Calibrar las heladas con datos reales (viable).** Bajar series horarias de Open-Meteo (ERA5-Land) para las coordenadas de las 3 parcelas, en las noches de heladas documentadas (por ejemplo, septiembre y octubre de cada temporada, que se pueden identificar por las alertas de la DACC o el SMN). Con eso se extraen perfiles reales de descenso nocturno, hora de la mínima y humedad relativa. Conviene contrastarlos con las tablas instantáneas de la DACC y con las estaciones del SIGA (por ejemplo, la EEA Mendoza en Luján de Cuyo). Hay que aplicar una corrección de unos −1 °C entre el abrigo y la planta y tener en cuenta el sesgo de la celda de reanálisis, que suaviza las mínimas en el fondo de los valles.
2. **Umbrales del MVP.** Alerta de helada por estado fenológico con los valores del IDR y la DACC (−1,1 / −0,6 / −0,6 °C), más un umbral de "brotación" configurable (−2 °C como valor de trabajo, sin aval oficial verificado). Agregar el punto de rocío como factor de severidad. Para el riego, usar el déficit acumulado ET0 − lluvia o un umbral simulado de humedad volumétrica, y documentarlo como un supuesto del proyecto.
3. **Importación directa a MongoDB.**
   - Open-Meteo y NASA POWER devuelven JSON listo para `mongoimport` o un script en Python, y caben en una *time-series collection* (`timeField: ts`, `metaField: {nodo, parcela, fuente}`).
   - El ZIP horario del SMN se descarga y se parsea a diario con un cron, para ir acumulando una serie propia.
   - Las alertas del SMN (dataset de 365 días) pueden ser una colección `alertas_oficiales` para comparar con las alertas del MVP.
   - La DACC y la telemetría del DGI requieren *scraping* de HTML. Es útil como demostración, pero frágil.
   - Los boletines del DGI (PDF) sirven como metadatos de contexto, no como serie.
4. **Pedido formal recomendado.** Escribir al área de Agrometeorología de la DACC pidiendo series horarias de 1 o 2 estaciones del Valle de Uco o de Luján en temporadas con heladas, en un marco académico (UM, BDII). Es la mejor fuente de verdad local y no está publicada para descarga.
5. **Mezclar fuentes en el diseño de la base.** Guardar un campo `fuente` (`simulado`, `era5land`, `smn`, `inta`, `dacc`) en cada documento. Así las 8 consultas avanzadas pueden comparar lo simulado con lo real, por ejemplo el error de la mínima nocturna o las alertas del MVP frente a las oficiales. Eso suma valor académico.

## Conclusión práctica: qué es real y qué simulado

- **Se puede alimentar con datos públicos reales:** temperatura y humedad del aire (ERA5-Land vía Open-Meteo para las parcelas; SMN e INTA como estaciones de referencia), eventos y perfiles de helada históricos, alertas oficiales de helada para comparar (SMN como dataset; DACC como texto), ET0 (calculada o tomada de Open-Meteo), y contexto hídrico (caudales y embalses del DGI, en forma manual o semimanual).
- **Debe seguir simulado:** los 10 nodos de sensores (no hay ningún viñedo con datos abiertos por nodo), la **humedad de suelo por parcela** (no existe in situ abierta en Mendoza; ERA5-Land sirve solo como tendencia de unos 10 km, no como sensor), los turnos de riego de una finca concreta, las alertas de riego (no hay umbral oficial abierto) y los escenarios extremos de helada para pruebas de carga e índices.

## Caveats

- No se pudo abrir la página de documentación del SIGA (bloqueo a accesos automáticos) ni la página de Evapotranspiración de la DACC. La descarga horaria del SIGA en CSV, su licencia y el número de estaciones de Mendoza **quedan sin verificar**.
- La cantidad de días que trae el ZIP horario del SMN no se verificó. La ficha del dataset dice "No se especificó la licencia".
- La cifra de 12 estaciones de la DACC viene de un proveedor comercial. La nota oficial sobre la "novena estación" del Valle de Uco no tiene fecha visible (probablemente es de 2020).
- Los umbrales del IDR y la DACC usan la nomenclatura de estados de frutales (D, F, H). La relación con la escala fenológica de la vid (brotación, hojas separadas, floración) no está explicitada en el informe.
- Las afirmaciones periodísticas (−2 a −5 °C en brotes; hasta 1 °C menos fuera del abrigo) son referencias técnicas citadas por la prensa, no normas oficiales.
- Varias fuentes pedidas (INV, COVIAR, IANIGLA, IDE Mendoza, UNCuyo, Meteostat, GHCN, SMAP, redes privadas) no se verificaron en esta investigación por límite de búsquedas.
