"""Valida documentos con un $jsonSchema SIN guardarlos (ADR-007).

Para qué: `lecturas` es una serie temporal y no admite validador, así que el
simulador valida cada lote antes de insertarlo. La validación la hace MongoDB
con el MISMO esquema de db/schemas/lecturas.py: Python no necesita entender
el $jsonSchema (spike de esquemas, prueba 4).

Cómo funciona: una agregación sobre la base (no sobre una colección):
    $documents   crea los documentos "en el aire", sin guardarlos.
    $match       con $jsonSchema deja pasar solo los que cumplen el esquema.
Lo que vuelve son los válidos; el resto son los inválidos.

Para saber cuál es cuál, cada documento viaja con una etiqueta "__i" (su
posición en la lista). El esquema se copia y se le agrega "__i" como campo
permitido, para que el esquema cerrado no la rechace.

Uso:
    from db.schemas import lecturas
    from db.schemas.validar import validar_documentos

    validos, invalidos = validar_documentos(bd, lecturas.ESQUEMA, lote)
"""

from pymongo.database import Database

# Un comando de MongoDB no puede pesar más de 16 MB: los lotes grandes se
# validan en partes de este tamaño (5.000 lecturas se validan en ~0,08 s).
TAMANO_PARTE = 5000


def validar_documentos(bd: Database, esquema: dict, documentos: list[dict]) -> tuple[list[dict], list[dict]]:
    """Devuelve (válidos, inválidos), en el mismo orden en que llegaron."""
    # Copia del esquema que además permite la etiqueta "__i".
    esquema_con_etiqueta = {**esquema, "properties": {**esquema["properties"], "__i": {}}}

    indices_validos: set[int] = set()
    for inicio in range(0, len(documentos), TAMANO_PARTE):
        parte = documentos[inicio : inicio + TAMANO_PARTE]
        etiquetados = [{**doc, "__i": inicio + i} for i, doc in enumerate(parte)]
        resultado = bd.aggregate(
            [
                {"$documents": etiquetados},
                {"$match": {"$jsonSchema": esquema_con_etiqueta}},
                {"$project": {"_id": 0, "__i": 1}},
            ]
        )
        indices_validos.update(d["__i"] for d in resultado)

    validos = [doc for i, doc in enumerate(documentos) if i in indices_validos]
    invalidos = [doc for i, doc in enumerate(documentos) if i not in indices_validos]
    return validos, invalidos
