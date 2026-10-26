"""Esquema de `variedades` (configuración). Campos en docs/modelo-datos.md, sección 3.9.

Las etapas van embebidas como lista (ADR-006, decisión 2).
"""

from db.schemas import comunes as c

NOMBRE = "variedades"
SERIE_TEMPORAL = False

# Número o vacío (None): una etapa puede no tener umbral o grados-día.
NUMERO_O_NULL = {"bsonType": ["double", "int", "long", "null"]}

ESQUEMA = {
    "bsonType": "object",
    "required": ["_id", "nombre", "ficticia", "grados_dia", "etapas"],
    "additionalProperties": False,
    "properties": {
        "_id": c.TEXTO,  # "malbec"
        "nombre": c.TEXTO,
        "ficticia": {"bsonType": "bool"},  # True solo en la variedad simulada X
        "grados_dia": {
            "bsonType": "object",
            "required": ["base_c", "tope_c", "inicio", "hasta_brotacion"],
            "additionalProperties": False,
            "properties": {
                "base_c": c.NUMERO,  # 10 °C
                "tope_c": c.NUMERO,  # 32 °C
                "inicio": {  # desde cuándo se cuenta (1/9)
                    "bsonType": "object",
                    "required": ["mes", "dia"],
                    "additionalProperties": False,
                    "properties": {
                        "mes": {"bsonType": ["int", "long"], "minimum": 1, "maximum": 12},
                        "dia": {"bsonType": ["int", "long"], "minimum": 1, "maximum": 31},
                    },
                },
                "hasta_brotacion": c.NUMERO,
            },
        },
        "etapas": {
            "bsonType": "array",
            "minItems": 1,
            "items": {
                "bsonType": "object",
                "required": [
                    "bbch_desde",
                    "bbch_hasta",
                    "nombre",
                    "baggiolini",
                    "umbral_helada_c",
                    "gd_desde_brotacion",
                ],
                "additionalProperties": False,
                "properties": {
                    "bbch_desde": c.ETAPA_BBCH,
                    "bbch_hasta": c.ETAPA_BBCH,
                    "nombre": c.TEXTO,
                    "baggiolini": c.TEXTO,  # solo para mostrar
                    "umbral_helada_c": NUMERO_O_NULL,  # None: la etapa no se evalúa
                    "gd_desde_brotacion": NUMERO_O_NULL,
                },
            },
        },
    },
}
