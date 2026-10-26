"""Spike ADR-001 · Prueba 1.

Pregunta: ¿se puede crear `lecturas` como serie temporal e insertar datos?

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python scripts/spike-adr001/01_crear_serie_temporal.py

Usa una base de PRUEBA llamada `spike_agrosense`. No toca ninguna base real.
Los valores de las lecturas son inventados solo para probar: no representan nada.
"""

import sys
from datetime import datetime, timezone
from pprint import pprint

from pymongo import MongoClient

# La consola de Windows usa otra codificación: forzamos UTF-8 para ver bien los acentos.
sys.stdout.reconfigure(encoding="utf-8")

# 1) Elegimos la base de prueba.
cliente = MongoClient("mongodb://localhost:27017")
bd = cliente["spike_agrosense"]

# 2) Borramos la base de prueba para empezar limpio. Así el script se puede repetir.
cliente.drop_database("spike_agrosense")

# 3) Crear la colección de serie temporal.
#    timeField:   campo que guarda CUÁNDO se hizo la lectura.
#    metaField:   campo que guarda DE DÓNDE vino (nodo, parcela, finca).
#    granularity: avisa que las lecturas llegan cada pocos minutos
#                 (el proyecto simula una lectura cada 5 minutos).
bd.create_collection(
    "lecturas",
    timeseries={"timeField": "ts", "metaField": "meta", "granularity": "minutes"},
)


# 4) Insertar lecturas de prueba: 2 nodos de la misma parcela, 3 instantes cada uno.
#    Las fechas van en UTC. Mendoza está en UTC-3, así que 03:00 UTC equivale
#    a las 00:00 hora local.
def hora(h: int, m: int) -> datetime:
    return datetime(2026, 10, 13, h, m, tzinfo=timezone.utc)


meta_n01 = {"nodo_id": "N-01", "parcela_id": "P-1", "finca_id": "F-1"}
meta_n02 = {"nodo_id": "N-02", "parcela_id": "P-1", "finca_id": "F-1"}

resultado = bd.lecturas.insert_many(
    [
        {"ts": hora(3, 0), "meta": meta_n01, "temperatura": -0.4, "humedad_suelo": 31.0, "humedad_aire": 62.0},
        {"ts": hora(3, 5), "meta": meta_n01, "temperatura": -0.8, "humedad_suelo": 31.0, "humedad_aire": 63.0},
        {"ts": hora(3, 10), "meta": meta_n01, "temperatura": -1.1, "humedad_suelo": 30.9, "humedad_aire": 64.0},
        {"ts": hora(3, 0), "meta": meta_n02, "temperatura": -0.2, "humedad_suelo": 33.0, "humedad_aire": 60.0},
        {"ts": hora(3, 5), "meta": meta_n02, "temperatura": -0.5, "humedad_suelo": 33.1, "humedad_aire": 61.0},
        {"ts": hora(3, 10), "meta": meta_n02, "temperatura": -0.9, "humedad_suelo": 33.0, "humedad_aire": 62.0},
    ]
)

# 5) Verificar. Estas líneas son las que hay que mirar y anotar.
print("Versión del servidor:", cliente.server_info()["version"])
# insert_many devuelve los _id que insertó (inserted_ids); contarlos da la cantidad.
print("Documentos insertados:", len(resultado.inserted_ids))
print("Documentos en la colección:", bd.lecturas.count_documents({}))

# El tipo de la colección tiene que decir "timeseries". Si dice "collection", es común.
info = next(bd.list_collections(filter={"name": "lecturas"}))
print("Tipo de colección:", info["type"])
pprint(info["options"])

# Dos lecturas ordenadas por fecha, para ver cómo quedaron los documentos.
pprint(list(bd.lecturas.find().sort("ts", 1).limit(2)))
