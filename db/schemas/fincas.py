"""Esquema de `fincas` (colección común). Campos en docs/modelo-datos.md, sección 3.1.

Reglas generales de todos los esquemas (ADR-006 y ADR-007):
    required: campos obligatorios.
    additionalProperties: False → esquema cerrado: un campo que no esté en
        "properties" (por ejemplo, un error de tipeo) hace que se rechace el documento.
    _id va declarado en "properties"; si no, el esquema cerrado rechaza todo
        (spike de esquemas, prueba 1).
    enum: lista de valores permitidos.
"""

from db.schemas import comunes as c

NOMBRE = "fincas"
SERIE_TEMPORAL = False

ESQUEMA = {
    "bsonType": "object",
    "required": ["_id", "nombre", "departamento", "oasis", "altitud_m", "geometria",
                 "sistema_riego", "tipo_suelo", "ficticia"],
    "additionalProperties": False,
    "properties": {
        "_id": c.CODIGO_FINCA,                                   # "F-SR", "F-TU", "F-SM"
        "nombre": c.TEXTO,
        "departamento": {"enum": ["San Rafael", "Tupungato", "San Martín"]},
        "oasis": {"enum": ["Sur", "Valle de Uco", "Este"]},
        "altitud_m": {"bsonType": ["double", "int", "long"], "minimum": 0},
        "geometria": c.POLIGONO,
        "sistema_riego": {"enum": ["surco", "goteo"]},           # ADR-005
        "tipo_suelo": {"enum": ["franco", "franco_arenoso", "pedregoso"]},  # ADR-005
        "ficticia": {"enum": [True]},                            # todas las fincas son ficticias
    },
}
