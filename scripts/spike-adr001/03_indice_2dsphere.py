"""Spike ADR-001 · Prueba 3.

Pregunta: ¿se puede poner un índice geoespacial (2dsphere) en una serie temporal?
Importa para Q3 (nodos más cercanos, $geoNear) y Q4 (parcelas dentro de un
polígono, $geoIntersects). Si no se puede combinar, `eventos_climaticos` va como
colección común (CLAUDE.md, sección 5).

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python scripts/spike-adr001/03_indice_2dsphere.py

Usa la base de PRUEBA `spike_agrosense`. No toca ninguna base real.
Las coordenadas están inventadas, solo para probar. En GeoJSON el orden es
[longitud, latitud].
"""

import sys
from datetime import datetime, timezone

from pymongo import MongoClient

sys.stdout.reconfigure(encoding="utf-8")

cliente = MongoClient("mongodb://localhost:27017")
cliente.drop_database("spike_agrosense")
bd = cliente["spike_agrosense"]

ts = datetime(2026, 10, 13, 3, 0, tzinfo=timezone.utc)

# Un polígono de prueba (cerrado: el primer punto se repite al final) y dos puntos.
poligono = {"type": "Polygon", "coordinates": [[[-68.40, -34.70], [-68.20, -34.70], [-68.20, -34.55],
                                               [-68.40, -34.55], [-68.40, -34.70]]]}
punto_dentro = {"type": "Point", "coordinates": [-68.30, -34.62]}   # cae dentro del polígono
punto_fuera = {"type": "Point", "coordinates": [-69.15, -33.37]}    # cae fuera

# Cinco colecciones, para comparar dónde funciona el índice:
#   ts_area:     serie temporal, con el POLÍGONO como campo común (fuera de meta)
#   ts_punto:    serie temporal, con un PUNTO como campo común (fuera de meta)
#   ts_meta:     serie temporal, con un PUNTO DENTRO de meta
#   comun_area:  colección común, con el polígono (punto de comparación)
#   comun_nodos: colección común, con puntos (punto de comparación para $geoNear)
opciones_ts = {"timeField": "ts", "metaField": "meta"}
for nombre in ["ts_area", "ts_punto", "ts_meta"]:
    bd.create_collection(nombre, timeseries=opciones_ts)
bd.create_collection("comun_area")
bd.create_collection("comun_nodos")

bd.ts_area.insert_one({"ts": ts, "meta": {"evento_id": "E-1"}, "area": poligono})
bd.comun_area.insert_one({"evento_id": "E-1", "area": poligono})
bd.ts_punto.insert_many([
    {"ts": ts, "meta": {"nodo_id": "N-01"}, "ubicacion": punto_dentro, "temperatura": -0.4},
    {"ts": ts, "meta": {"nodo_id": "N-02"}, "ubicacion": punto_fuera, "temperatura": -0.2},
])
bd.ts_meta.insert_many([
    {"ts": ts, "meta": {"nodo_id": "N-01", "ubicacion": punto_dentro}, "temperatura": -0.4},
    {"ts": ts, "meta": {"nodo_id": "N-02", "ubicacion": punto_fuera}, "temperatura": -0.2},
])
bd.comun_nodos.insert_many([
    {"nodo_id": "N-01", "ubicacion": punto_dentro},
    {"nodo_id": "N-02", "ubicacion": punto_fuera},
])


def probar(descripcion: str, accion) -> None:
    """Ejecuta un caso y muestra OK o ERROR (igual que en la prueba 2)."""
    try:
        print(f"OK    | {descripcion} | {accion()}")
    except Exception as e:  # noqa: BLE001 — en un spike queremos ver cualquier error
        mensaje = str(e).split(", full error")[0]
        # El error de índice es muy largo: mostramos la causa final.
        print(f"ERROR | {descripcion} | {mensaje.split(':: caused by ::')[-1].strip()}")


print("Versión del servidor:", cliente.server_info()["version"])
print("---")

# --- Crear índices ---

# 1) Índice 2dsphere en una serie temporal, sobre un campo común (el polígono)
probar("1. Índice 2dsphere en serie temporal, campo común (area)",
       lambda: bd.ts_area.create_index([("area", "2dsphere")]))

# 1b) Lo mismo con un PUNTO: separa "polígono" de "campo común".
probar("1b. Índice 2dsphere en serie temporal, campo común con un PUNTO (ubicacion)",
       lambda: bd.ts_punto.create_index([("ubicacion", "2dsphere")]))

# 2) Índice 2dsphere en una serie temporal, sobre un campo dentro de meta
probar("2. Índice 2dsphere en serie temporal, dentro de meta (meta.ubicacion)",
       lambda: bd.ts_meta.create_index([("meta.ubicacion", "2dsphere")]))

# 3) Índice 2dsphere en una colección común (punto de comparación)
probar("3. Índice 2dsphere en colección común (area)",
       lambda: bd.comun_area.create_index([("area", "2dsphere")]))

# --- Consultar ---

# 4) $geoIntersects (técnica de Q4) en colección común: ¿qué eventos contienen este punto?
probar("4. $geoIntersects en colección común",
       lambda: bd.comun_area.count_documents({"area": {"$geoIntersects": {"$geometry": punto_dentro}}}))

# 5) $geoIntersects en la serie temporal. Si el caso 1 falló, no hay índice y la
#    consulta recorre todo.
probar("5. $geoIntersects en serie temporal (sin índice si el caso 1 falló)",
       lambda: bd.ts_area.count_documents({"area": {"$geoIntersects": {"$geometry": punto_dentro}}}))

# 6) $geoNear (técnica de Q3) en la serie temporal con el índice dentro de meta.
probar("6. $geoNear en serie temporal (índice en meta.ubicacion)", lambda: [
    {"nodo": d["meta"]["nodo_id"], "distancia_m": round(d["distancia_m"]) if d.get("distancia_m") is not None else None}
    for d in bd.ts_meta.aggregate([
        {"$geoNear": {"near": punto_dentro, "distanceField": "distancia_m", "key": "meta.ubicacion"}},
        {"$limit": 2},
    ])
])

# 7) $geoNear en una colección común: punto de comparación. ¿Devuelve la distancia?
bd.comun_nodos.create_index([("ubicacion", "2dsphere")])
probar("7. $geoNear en colección común (para comparar con el caso 6)", lambda: [
    {"nodo": d["nodo_id"], "distancia_m": round(d["distancia_m"])}
    for d in bd.comun_nodos.aggregate([
        {"$geoNear": {"near": punto_dentro, "distanceField": "distancia_m"}},
        {"$limit": 2},
    ])
])

# Índices que quedaron creados en cada colección
print("---")
for nombre in ["ts_area", "ts_punto", "ts_meta", "comun_area", "comun_nodos"]:
    print(f"Índices de {nombre}: {', '.join(i['name'] for i in bd[nombre].list_indexes())}")
