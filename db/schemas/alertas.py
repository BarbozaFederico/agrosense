"""Esquema de `alertas` (colección común). Campos en docs/modelo-datos.md, sección 3.5.

Además de los campos, este esquema controla dos reglas que combinan campos
(con "allOf" y "anyOf"):
    allOf: el documento tiene que cumplir TODAS las reglas de la lista.
    anyOf: el documento tiene que cumplir AL MENOS UNA de las opciones.
"""

from db.schemas import comunes as c

NOMBRE = "alertas"
SERIE_TEMPORAL = False

ESQUEMA = {
    "bsonType": "object",
    "required": [
        "_id",
        "tipo",
        "parcela_id",
        "estado",
        "inicio",
        "fin",
        "etapa_bbch",
        "umbral",
        "valor_extremo",
        "riesgo",
        "fuente",
    ],
    "additionalProperties": False,
    "properties": {
        "_id": c.OBJECT_ID,
        "tipo": {"enum": ["helada", "riego"]},
        "parcela_id": c.CODIGO_PARCELA,  # solo referencias (ADR-003)
        "estado": {"enum": ["abierta", "cerrada"]},
        "inicio": c.FECHA,
        "fin": {"bsonType": ["date", "null"]},  # None mientras está abierta (ADR-006)
        "etapa_bbch": c.ETAPA_BBCH,
        "umbral": c.NUMERO,  # °C del brote (helada) o % de suelo (riego)
        "valor_extremo": c.NUMERO,  # mínima registrada
        "riesgo": {
            "bsonType": ["object", "null"],  # None en riego y mientras está abierta
            "required": ["nivel", "margen_c", "agravantes"],
            "additionalProperties": False,
            "properties": {
                "nivel": {"enum": ["bajo", "medio", "alto"]},
                "margen_c": c.NUMERO,
                "agravantes": {
                    "bsonType": "array",
                    "uniqueItems": True,
                    "items": {"enum": ["duracion", "aire_seco", "suelo_seco"]},
                },
            },
        },
        "fuente": c.FUENTE_SIMULADA,
        "escenario_id": c.TEXTO,
    },
    "allOf": [
        # Regla 1: una alerta abierta no tiene fin; una cerrada sí.
        {
            "anyOf": [
                {"properties": {"estado": {"enum": ["abierta"]}, "fin": {"bsonType": "null"}}},
                {"properties": {"estado": {"enum": ["cerrada"]}, "fin": {"bsonType": "date"}}},
            ]
        },
        # Regla 2: el riesgo solo existe en alertas de helada cerradas (ADR-006, decisión 6).
        {
            "anyOf": [
                {"properties": {"riesgo": {"bsonType": "null"}}},
                {
                    "properties": {
                        "tipo": {"enum": ["helada"]},
                        "estado": {"enum": ["cerrada"]},
                        "riesgo": {"bsonType": "object"},
                    }
                },
            ]
        },
    ],
}
