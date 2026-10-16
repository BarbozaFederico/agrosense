"""Piezas de esquema que se repiten en varias colecciones.

Qué es un $jsonSchema: una regla que describe cómo tiene que ser un documento
(qué campos tiene, de qué tipo y con qué valores). MongoDB la usa para rechazar
los documentos que no la cumplen (ADR-006).

El esquema es un diccionario de Python que pymongo le envía a MongoDB tal cual:
el que lo guarda y lo aplica es el servidor, no Python.

"bsonType" es el tipo de dato tal como lo guarda MongoDB (BSON):
    "string" texto · "date" fecha · "bool" verdadero/falso · "object" subdocumento
    "array" lista · "objectId" identificador automático · "null" vacío
    "int" y "long" enteros · "double" número con decimales

En Python se escribe True, False y None (en el $jsonSchema llegan como true,
false y null).
"""

# Un número cualquiera. Se aceptan enteros y decimales porque Python guarda 76
# como entero y 76.5 como decimal: los dos son válidos.
NUMERO = {"bsonType": ["double", "int", "long"]}

# Un número entero (por ejemplo, una cantidad de minutos).
ENTERO = {"bsonType": ["int", "long"]}

# Un porcentaje: número entre 0 y 100.
PORCENTAJE = {"bsonType": ["double", "int", "long"], "minimum": 0, "maximum": 100}

# Un número mayor que 0. "exclusiveMinimum": el 0 no está permitido.
POSITIVO = {"bsonType": ["double", "int", "long"], "minimum": 0, "exclusiveMinimum": True}

# Texto obligatorio que no puede estar vacío.
TEXTO = {"bsonType": "string", "minLength": 1}

# Una fecha. En Python se usa datetime con zona UTC.
FECHA = {"bsonType": "date"}

# Un par [longitud, latitud] en grados (orden de GeoJSON).
COORDENADA = {"bsonType": "array", "minItems": 2, "maxItems": 2, "items": NUMERO}

# Un punto GeoJSON: {"type": "Point", "coordinates": [longitud, latitud]}.
PUNTO = {
    "bsonType": "object",
    "required": ["type", "coordinates"],
    "additionalProperties": False,
    "properties": {
        "type": {"enum": ["Point"]},
        "coordinates": COORDENADA,
    },
}

# Un polígono GeoJSON: lista de anillos; cada anillo es una lista de al menos
# 4 coordenadas (el primer punto se repite al final para cerrarlo).
POLIGONO = {
    "bsonType": "object",
    "required": ["type", "coordinates"],
    "additionalProperties": False,
    "properties": {
        "type": {"enum": ["Polygon"]},
        "coordinates": {
            "bsonType": "array",
            "minItems": 1,
            "items": {"bsonType": "array", "minItems": 4, "items": COORDENADA},
        },
    },
}

# Códigos legibles de ADR-006. "pattern" es una expresión regular que el texto
# tiene que cumplir: por ejemplo ^F-[A-Z]{2}$ acepta "F-SR" y rechaza "finca1".
CODIGO_FINCA = {"bsonType": "string", "pattern": "^F-[A-Z]{2}$"}
CODIGO_PARCELA = {"bsonType": "string", "pattern": "^P-[A-Z]{2}-[0-9]+$"}
CODIGO_NODO = {"bsonType": "string", "pattern": "^N-[A-Z]{2}-[0-9]+-[A-Z]$"}

# Identificador automático de MongoDB (para alertas, riegos, eventos...).
OBJECT_ID = {"bsonType": "objectId"}

# Etapa fenológica en escala BBCH: entero de 0 a 99.
ETAPA_BBCH = {"bsonType": ["int", "long"], "minimum": 0, "maximum": 99}

# Origen del dato (CLAUDE.md, "Datos sintéticos").
FUENTE_SIMULADA = {"enum": ["simulado", "simulacion_en_vivo"]}
