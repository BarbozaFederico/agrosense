"""Esquema de `configuracion` (configuración). Campos en docs/modelo-datos.md, sección 3.10.

Un único documento con _id "general" (ADR-006, decisión 4).

Incluye los límites de temperatura "sospechosa" y la "noche extrema" (ADR-009).
Las reglas que el esquema no puede expresar (porque comparan dos campos) están en
verificar_coherencia(): la usan las pruebas y la va a usar el seed.
"""

from db.schemas import comunes as c

NOMBRE = "configuracion"
SERIE_TEMPORAL = False

# Umbrales de riego de un tipo de suelo, por período (% de humedad de suelo).
UMBRALES_SUELO = {
    "bsonType": "object",
    "required": ["sep_oct", "nov", "dic_ene", "feb_mar"],
    "additionalProperties": False,
    "properties": {
        "sep_oct": c.PORCENTAJE,
        "nov": c.PORCENTAJE,
        "dic_ene": c.PORCENTAJE,
        "feb_mar": c.PORCENTAJE,
    },
}

# Un límite de frío: número que no puede ser positivo (un límite de frío > 0 °C es un
# error de carga), o vacío (None) para dejarlo "pendiente de validar".
LIMITE_FRIO_O_NULL = {"bsonType": ["double", "int", "long", "null"], "maximum": 0}

# Límite de "sospechoso" de la temperatura del sensor (temperatura_c, de abrigo), por
# departamento, en °C (ADR-009). Una lectura ESTRICTAMENTE más fría que este valor es
# posible pero rara para la zona, a diferencia de las "imposibles" (-40 a 60 °C,
# db/schemas/lecturas.py). No se rechaza ni se excluye de las consultas:
#   - el simulador lo usa como techo de frío de las noches comunes;
#   - la auditoría (db/queries/auditoria_lecturas.py) cuenta las que lo superan.
# Un solo valor por departamento, el de septiembre (el mes más frío de la temporada).
# Las claves van en snake_case y sin tildes (CLAUDE.md, sección 2): san_rafael, san_martin.
# Valores: récord de septiembre de las normales 1991-2020 del SMN
# (docs/investigacion/verificacion-fuentes.md).
# Tupungato no tiene estación del SMN: queda en None, A VALIDAR (el simulador falla
# si intenta generar heladas allí sin valor; la auditoría avisa "no auditado").
# La referencia de La Consulta (-7,3 °C, mínima anual media) es solo contexto, no un límite.
SOSPECHOSO_MINIMO_C = {
    "bsonType": "object",
    "required": ["san_rafael", "san_martin", "tupungato"],
    "additionalProperties": False,
    "properties": {
        "san_rafael": LIMITE_FRIO_O_NULL,                        # -4,5 °C (SMN, San Rafael Aero)
        "san_martin": LIMITE_FRIO_O_NULL,                        # -2,8 °C (SMN, San Martín)
        "tupungato": LIMITE_FRIO_O_NULL,                         # None: a validar
    },
}

# Noche extrema precargada (RF-13, ADR-009): la única noche que puede superar el límite
# de "sospechoso", en una sola finca. Es un objeto único, no una lista.
#   finca_id:  finca donde ocurre (San Rafael, donde el evento de 2026 está documentado).
#   inicio y fin: ventana explícita, en UTC (Argentina es UTC-3). El simulador la usa para
#     generar y la auditoría para reconocer las lecturas "esperadas". Primera semana de
#     octubre de 2026; las horas exactas las fija el seed, comprobando con Q9 que la
#     parcela esté en BBCH 07 o más (si no, la alerta no se ve).
#   minimo_c:  piso del sensor esa noche. Ninguna lectura puede ser más fría.
#     SUPUESTO: cifra de prensa del evento (-8,3 °C) menos delta_brote_c (2 °C), porque se
#     presume que la prensa informó temperatura de nivel del cultivo y no de abrigo.
#     A VALIDAR con la investigación (docs/investigacion/verificacion-fuentes.md).
NOCHE_EXTREMA = {
    "bsonType": "object",
    "required": ["finca_id", "inicio", "fin", "minimo_c"],
    "additionalProperties": False,
    "properties": {
        "finca_id": c.CODIGO_FINCA,
        "inicio": c.FECHA,
        "fin": c.FECHA,
        "minimo_c": {"bsonType": ["double", "int", "long"], "maximum": 0},
    },
}

ESQUEMA = {
    "bsonType": "object",
    "required": ["_id", "delta_brote_c", "nodo_inactivo_min", "sospechoso_minimo_c",
                 "noche_extrema", "riesgo", "umbrales_riego"],
    "additionalProperties": False,
    "properties": {
        "_id": {"enum": ["general"]},                            # un solo documento
        "delta_brote_c": {"bsonType": ["double", "int", "long"], "minimum": 0},  # 2 °C (ADR-005)
        "nodo_inactivo_min": {"bsonType": ["int", "long"], "minimum": 1},        # 30 min
        "sospechoso_minimo_c": SOSPECHOSO_MINIMO_C,              # límite de "sospechoso" por departamento
        "noche_extrema": NOCHE_EXTREMA,                          # la noche precargada que puede superarlo
        "riesgo": {                                              # cortes del índice (ADR-005)
            "bsonType": "object",
            "required": ["margen_bajo_c", "margen_alto_c", "horas_duracion",
                         "margen_duracion_c", "aire_seco_pct"],
            "additionalProperties": False,
            "properties": {
                "margen_bajo_c": c.NUMERO,
                "margen_alto_c": c.NUMERO,
                "horas_duracion": c.NUMERO,
                "margen_duracion_c": c.NUMERO,
                "aire_seco_pct": c.PORCENTAJE,
            },
        },
        "umbrales_riego": {                                      # por tipo de suelo (ADR-005)
            "bsonType": "object",
            "required": ["franco", "franco_arenoso", "pedregoso"],
            "additionalProperties": False,
            "properties": {
                "franco": UMBRALES_SUELO,
                "franco_arenoso": UMBRALES_SUELO,
                "pedregoso": UMBRALES_SUELO,
            },
        },
    },
}


def verificar_coherencia(config: dict, departamento_de_finca: dict[str, str],
                         temperatura_minima_imposible_c: float) -> list[str]:
    """Reglas que el esquema no puede expresar porque comparan dos campos.

    Devuelve una lista de errores en texto (vacía si todo es coherente).

    config                          el documento de configuración.
    departamento_de_finca           {"F-SR": "san_rafael", ...}: clave de departamento de cada finca.
    temperatura_minima_imposible_c  el mínimo de lecturas.py (hoy -40, provisional).
    """
    errores = []
    limites = config["sospechoso_minimo_c"]

    # 1) Cada límite tiene que ser más cálido que lo "imposible".
    for departamento, limite in limites.items():
        if limite is not None and limite <= temperatura_minima_imposible_c:
            errores.append(f"sospechoso_minimo_c.{departamento} ({limite}) tiene que ser más cálido "
                           f"que el mínimo imposible ({temperatura_minima_imposible_c})")

    noche = config["noche_extrema"]

    # 2) La ventana tiene que tener sentido.
    if noche["inicio"] >= noche["fin"]:
        errores.append("noche_extrema.inicio tiene que ser anterior a noche_extrema.fin")

    # 3) La finca de la noche tiene que existir, tener límite y quedar más fría que él:
    #    si no superara el límite, no haría falta declararla.
    departamento = departamento_de_finca.get(noche["finca_id"])
    if departamento is None:
        errores.append(f"noche_extrema.finca_id ({noche['finca_id']}) no corresponde a ninguna finca")
    elif limites.get(departamento) is None:
        errores.append(f"noche_extrema: el departamento {departamento} no tiene límite de sospechoso")
    elif noche["minimo_c"] >= limites[departamento]:
        errores.append(f"noche_extrema.minimo_c ({noche['minimo_c']}) tiene que ser más frío que "
                       f"sospechoso_minimo_c.{departamento} ({limites[departamento]})")
    return errores
