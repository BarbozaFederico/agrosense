"""Umbrales de humedad de suelo (%) para la alerta de riego, por tipo de suelo y período.

PENDIENTE: NO CARGAR HASTA VERIFICAR. Los valores de capacidad de campo por textura
vienen de una estimación general, no de la Tabla 19 de la FAO-56 (Allen et al. 1998):
el HTML oficial de fao.org no la trae y todavía no se leyó en el PDF
(docs/investigacion/vid-malbec-complemento.md, sección 5b; ADR-005, decisión 5).

Mientras valga None, el cargador (db.seeds.cargar) no puede cargar `configuracion` y se
detiene con un mensaje claro. Para completarlo hay que:
    1. Leer la Tabla 19 (θFC y θWP por textura) en el PDF de la FAO-56.
    2. Calcular el umbral de cada suelo y período: θFC − p × (θFC − θWP), con p = 0,45 en
       septiembre y octubre; 0,40 en noviembre; 0,60 de diciembre a enero y 0,50 de febrero
       a marzo (vid-malbec.md, sección d).
    3. Escribir acá el diccionario, con la forma:
           {"franco": {"sep_oct": ..., "nov": ..., "dic_ene": ..., "feb_mar": ...},
            "franco_arenoso": {...}, "pedregoso": {...}}
       y anotar la fuente de cada suelo en este archivo.
Nota: en la investigación el suelo "franco arenoso" no tiene valores por período (solo
13,5 % en setiembre y octubre, ADR-005) y la tabla de vid-malbec.md usa "arenoso", que no
es ninguno de los tres suelos de las fincas.
"""

UMBRALES_RIEGO = None
