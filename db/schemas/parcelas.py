"""Esquema de `parcelas` (colección común). Campos en docs/modelo-datos.md, sección 3.2.

La etapa fenológica NO se guarda acá: se calcula (ADR-006, decisión 5).
"""

from db.schemas import comunes as c

NOMBRE = "parcelas"
SERIE_TEMPORAL = False

ESQUEMA = {
    "bsonType": "object",
    "required": [
        "_id",
        "finca_id",
        "nombre",
        "variedad_id",
        "superficie_ha",
        "geometria",
        "conduccion",
        "densidad_plantas_ha",
    ],
    "additionalProperties": False,
    "properties": {
        "_id": c.CODIGO_PARCELA,  # "P-SR-1"
        "finca_id": c.CODIGO_FINCA,  # referencia a fincas._id
        "nombre": c.TEXTO,
        "variedad_id": c.TEXTO,  # referencia a variedades._id
        "superficie_ha": c.POSITIVO,  # mayor que 0
        "geometria": c.POLIGONO,  # Q4 ($geoIntersects)
        "conduccion": {"enum": ["espaldero", "parral"]},
        "densidad_plantas_ha": {"bsonType": ["int", "long"], "minimum": 1},
    },
}
