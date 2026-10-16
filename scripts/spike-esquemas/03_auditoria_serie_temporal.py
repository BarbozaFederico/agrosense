"""Spike de esquemas · Prueba 3.

Pregunta: si una serie temporal no admite validador (prueba 2), ¿se puede usar el
mismo $jsonSchema como FILTRO de búsqueda para encontrar lecturas mal formadas?
Es la "consulta de auditoría" (opción B del spike de esquemas).

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python scripts/spike-esquemas/03_auditoria_serie_temporal.py

Usa la base de PRUEBA `agrosense_tests`, que se borra al empezar.
"""

import sys
from datetime import datetime, timezone

from pymongo import MongoClient

from _comun import casos, esquema_lectura

sys.stdout.reconfigure(encoding="utf-8")

cliente = MongoClient("mongodb://localhost:27017")
cliente.drop_database("agrosense_tests")
bd = cliente["agrosense_tests"]

esquema = esquema_lectura(incluir_id=True)

# Serie temporal SIN validador (es lo único que permite MongoDB 9.0.2).
bd.create_collection("lecturas", timeseries={"timeField": "ts", "metaField": "meta", "granularity": "minutes"})
info = next(bd.list_collections(filter={"name": "lecturas"}))
print("Versión del servidor:", cliente.server_info()["version"], "| tipo de colección:", info["type"])
print("---")


# Cargamos los siete documentos de las pruebas anteriores. Para saber cuál es cuál
# sin agregar un campo de más, cada uno tiene un minuto distinto: el caso N va a las 09:0N.
def hora(minuto: int) -> datetime:
    return datetime(2026, 9, 14, 9, minuto, tzinfo=timezone.utc)


descripciones = {}
documentos = []
for n, (descripcion, doc) in enumerate(casos(hora(0)), start=1):
    descripciones[n] = descripcion
    documentos.append({**doc, "ts": hora(n)})
bd.lecturas.insert_many(documentos)
print("Lecturas cargadas (sin validación):", bd.lecturas.count_documents({}))
print("---")


def casos_de(docs) -> list[str]:
    """Traduce documentos a la descripción de su caso, usando el minuto de la hora."""
    return [descripciones[d["ts"].minute] for d in docs]


def probar(descripcion: str, accion) -> None:
    try:
        print(f"OK    | {descripcion} | {accion()}")
    except Exception as e:  # noqa: BLE001
        print(f"ERROR | {descripcion} | {str(e)[:120]}")


# $nor: [{ $jsonSchema }] significa "que NO cumpla el esquema".
no_cumple = {"$nor": [{"$jsonSchema": esquema}]}

# 1) ¿Qué lecturas CUMPLEN el esquema? (esperado: casos 1 y 7)
probar("1. find({$jsonSchema}) → lecturas que cumplen",
       lambda: casos_de(bd.lecturas.find({"$jsonSchema": esquema}).sort("ts", 1)))

# 2) ¿Qué lecturas NO cumplen? Es la consulta de auditoría (esperado: casos 2 a 6)
probar("2. find({$nor: [{$jsonSchema}]}) → lecturas mal formadas",
       lambda: casos_de(bd.lecturas.find(no_cumple).sort("ts", 1)))

# 3) Lo mismo dentro de una agregación ($match), contando cuántas fallan
probar("3. aggregate $match + $count → cantidad de lecturas mal formadas",
       lambda: list(bd.lecturas.aggregate([{"$match": no_cumple}, {"$count": "mal_formadas"}])))

# 4) Auditoría combinada con un filtro común (por nodo y rango de fechas)
probar("4. Auditoría filtrando por nodo y rango de fechas",
       lambda: bd.lecturas.count_documents({"meta.nodo_id": "N-SR-1-A",
                                            "ts": {"$gte": hora(0), "$lt": hora(10)}, **no_cumple}))

# 5) Borrar las lecturas mal formadas con el mismo filtro (posible "limpieza")
probar("5. delete_many con $nor + $jsonSchema",
       lambda: f"borrados {bd.lecturas.delete_many(no_cumple).deleted_count}")
print("Lecturas que quedan después de limpiar:", bd.lecturas.count_documents({}), "→",
      casos_de(bd.lecturas.find().sort("ts", 1)))
