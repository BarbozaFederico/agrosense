"""Esquema de `lecturas` (SERIE TEMPORAL). Campos en docs/modelo-datos.md, sección 3.4.

IMPORTANTE (ADR-007): en MongoDB 9.0.2 una serie temporal NO admite validador.
Este esquema NO se instala en la colección. Se usa de dos formas:
    1. El simulador valida cada lote antes de insertarlo, con
       db/schemas/validar.py (MongoDB valida sin guardar, con $documents).
    2. La auditoría (db/queries/auditoria_lecturas.py) busca las lecturas que
       no lo cumplen: find({"$nor": [{"$jsonSchema": ESQUEMA}]}).
"""

from db.schemas import comunes as c

NOMBRE = "lecturas"
SERIE_TEMPORAL = True

# Opciones de la serie temporal (ADR-001):
#   timeField: cuándo se midió · metaField: de dónde vino
#   granularity: las lecturas llegan cada pocos minutos (cada 5)
OPCIONES_SERIE_TEMPORAL = {"timeField": "ts", "metaField": "meta", "granularity": "minutes"}

ESQUEMA = {
    "bsonType": "object",
    "required": ["ts", "meta", "temperatura_c", "humedad_suelo_pct", "humedad_aire_pct"],
    "additionalProperties": False,
    "properties": {
        "_id": c.OBJECT_ID,  # lo agrega MongoDB al guardar
        "ts": c.FECHA,
        "meta": {
            "bsonType": "object",
            "required": ["nodo_id", "parcela_id", "finca_id", "fuente"],
            "additionalProperties": False,  # meta también cerrado
            "properties": {
                "nodo_id": c.CODIGO_NODO,
                "parcela_id": c.CODIGO_PARCELA,
                "finca_id": c.CODIGO_FINCA,
                "fuente": c.FUENTE_SIMULADA,
                "escenario_id": c.TEXTO,  # solo en simulaciones en vivo (RF-15)
            },
        },
        # Rango amplio de control: descarta valores imposibles (por ejemplo, 500 °C),
        # no valores raros pero posibles.
        "temperatura_c": {"bsonType": ["double", "int", "long"], "minimum": -40, "maximum": 60},
        "humedad_suelo_pct": c.PORCENTAJE,
        "humedad_aire_pct": c.PORCENTAJE,
    },
}
