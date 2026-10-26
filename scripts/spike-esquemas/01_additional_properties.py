"""Spike de esquemas · Prueba 1.

Pregunta: ¿funciona un $jsonSchema cerrado (additionalProperties: False) en una
serie temporal? ¿Y el _id que agrega MongoDB solo?
Importa para ADR-006 (validación estricta: validationAction "error" y esquema cerrado).

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python scripts/spike-esquemas/01_additional_properties.py

Usa la base de PRUEBA `agrosense_tests`, que se borra al empezar. No toca la base real.
Los valores son inventados, solo para probar.
"""

import sys

from pymongo import MongoClient

from _comun import TS, casos, esquema_lectura, probar_insercion

sys.stdout.reconfigure(encoding="utf-8")

cliente = MongoClient("mongodb://localhost:27017")
cliente.drop_database("agrosense_tests")
bd = cliente["agrosense_tests"]


def crear(nombre: str, serie_temporal: bool, incluir_id: bool) -> None:
    """Crea una colección (serie temporal o común) con el esquema indicado."""
    opciones = {
        "validator": {"$jsonSchema": esquema_lectura(incluir_id)},
        "validationLevel": "strict",
        "validationAction": "error",
    }
    if serie_temporal:
        opciones["timeseries"] = {"timeField": "ts", "metaField": "meta", "granularity": "minutes"}
    try:
        bd.create_collection(nombre, **opciones)
        print(f"OK    | crear {nombre}")
    except Exception as e:  # noqa: BLE001
        print(f"ERROR | crear {nombre} | {str(e).split(', full error')[0]}")


print("Versión del servidor:", cliente.server_info()["version"])
print("---")

# Cuatro variantes: serie temporal / común, con y sin _id declarado
crear("ts_sin_id", True, False)
crear("ts_con_id", True, True)
crear("comun_sin_id", False, False)
crear("comun_con_id", False, True)
print("---")

# OJO: si una colección no se pudo crear, el primer insert la crea igual,
# pero como colección COMÚN y SIN validación.
for nombre in ["ts_sin_id", "ts_con_id", "comun_sin_id", "comun_con_id"]:
    for descripcion, doc in casos(TS):
        probar_insercion(bd[nombre], descripcion, doc)
    print("---")

# ¿Qué tipo de colección quedó y con qué validación?
for nombre in ["ts_sin_id", "ts_con_id", "comun_sin_id", "comun_con_id"]:
    info = next(bd.list_collections(filter={"name": nombre}))
    print(
        f"{nombre}: tipo {info['type']} | validador: {'validator' in info['options']} | "
        f"documentos: {bd[nombre].count_documents({})}"
    )
