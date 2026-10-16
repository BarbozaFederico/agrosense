"""Spike de esquemas · Prueba 2.

Pregunta: la prueba 1 mostró que MongoDB 9.0.2 no acepta crear una serie temporal
con `validator` en el mismo create_collection. ¿Se puede agregar el validador
después, con collMod? ¿Funciona el esquema cerrado?

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python scripts/spike-esquemas/02_validador_serie_temporal.py

Usa la base de PRUEBA `agrosense_tests`, que se borra al empezar.
"""

import sys

from pymongo import MongoClient

from _comun import TS, casos, esquema_lectura, probar_insercion

sys.stdout.reconfigure(encoding="utf-8")

cliente = MongoClient("mongodb://localhost:27017")
cliente.drop_database("agrosense_tests")
bd = cliente["agrosense_tests"]


def crear_con_collmod(nombre: str, incluir_id: bool) -> None:
    """Paso 1: crear la serie temporal SIN validador. Paso 2: agregarlo con collMod."""
    try:
        bd.create_collection(nombre, timeseries={"timeField": "ts", "metaField": "meta", "granularity": "minutes"})
        print(f"OK    | crear serie temporal {nombre}")
    except Exception as e:  # noqa: BLE001
        print(f"ERROR | crear {nombre} | {e}")
        return
    try:
        bd.command("collMod", nombre,
                   validator={"$jsonSchema": esquema_lectura(incluir_id)},
                   validationLevel="strict", validationAction="error")
        info = next(bd.list_collections(filter={"name": nombre}))
        print(f"OK    | collMod {nombre} | tipo: {info['type']} | validador guardado: {'validator' in info['options']}")
    except Exception as e:  # noqa: BLE001
        print(f"ERROR | collMod {nombre} | {str(e).split(', full error')[0]}")


print("Versión del servidor:", cliente.server_info()["version"])
print("---")
crear_con_collmod("ts_sin_id", False)
crear_con_collmod("ts_con_id", True)
print("---")

for nombre in ["ts_sin_id", "ts_con_id"]:
    for descripcion, doc in casos(TS):
        probar_insercion(bd[nombre], descripcion, doc)
    print("---")

# insert_many: así va a cargar el simulador. ¿Un documento malo frena todo el lote?
valido, campo_extra = casos(TS)[0][1], casos(TS)[1][1]
antes = bd.ts_con_id.count_documents({})
try:
    bd.ts_con_id.insert_many([dict(valido), dict(campo_extra), dict(valido)], ordered=False)
    print("LOTE | entraron todos")
except Exception as e:  # noqa: BLE001
    print(f"LOTE | error en el lote: {str(e)[:60]}")
print(f"LOTE | insert_many de 3 (1 inválido, ordered=False): entraron {bd.ts_con_id.count_documents({}) - antes}")

print("---")
for nombre in ["ts_sin_id", "ts_con_id"]:
    print(f"Documentos guardados en {nombre}: {bd[nombre].count_documents({})}")
