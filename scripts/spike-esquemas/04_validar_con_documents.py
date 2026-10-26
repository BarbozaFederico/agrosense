"""Spike de esquemas · Prueba 4 (Python).

Pregunta: ¿puede Python pedirle a MongoDB que valide documentos con un
$jsonSchema SIN guardarlos? Es lo que necesita el simulador para validar las
lecturas antes de insertarlas (ADR-007), porque `lecturas` no admite validador.

Idea: la etapa `$documents` de una agregación crea documentos "en el aire"
(no los guarda en ninguna colección). Después `$match` con `$jsonSchema` deja
pasar solo los que cumplen el esquema. Lo que vuelve son los válidos.

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python scripts/spike-esquemas/04_validar_con_documents.py

Usa la base de PRUEBA `agrosense_tests`. No crea ni modifica colecciones.
"""

import sys
import time
from datetime import datetime, timezone

from pymongo import MongoClient

# La consola de Windows usa otra codificación: forzamos UTF-8 para ver bien los acentos.
sys.stdout.reconfigure(encoding="utf-8")

cliente = MongoClient("mongodb://localhost:27017")
bd = cliente["agrosense_tests"]

# Mismo esquema de lectura de las pruebas 1 a 3.
esquema = {
    "bsonType": "object",
    "required": ["ts", "meta", "temperatura_c", "humedad_suelo_pct", "humedad_aire_pct"],
    "additionalProperties": False,
    "properties": {
        "_id": {"bsonType": "objectId"},
        "ts": {"bsonType": "date"},
        "meta": {
            "bsonType": "object",
            "required": ["nodo_id", "parcela_id", "finca_id", "fuente"],
            "additionalProperties": False,
            "properties": {
                "nodo_id": {"bsonType": "string"},
                "parcela_id": {"bsonType": "string"},
                "finca_id": {"bsonType": "string"},
                "fuente": {"enum": ["simulado", "simulacion_en_vivo"]},
                "escenario_id": {"bsonType": "string"},
            },
        },
        "temperatura_c": {"bsonType": ["double", "int"]},
        "humedad_suelo_pct": {"bsonType": ["double", "int"]},
        "humedad_aire_pct": {"bsonType": ["double", "int"]},
    },
}

ts = datetime(2026, 9, 14, 9, 0, tzinfo=timezone.utc)
meta = {"nodo_id": "N-SR-1-A", "parcela_id": "P-SR-1", "finca_id": "F-SR", "fuente": "simulado"}

# Los mismos siete casos de las pruebas anteriores. "caso" es una etiqueta que
# NO se manda a MongoDB: solo sirve para leer el resultado.
casos = [
    ("1. Válido", {"ts": ts, "meta": meta, "temperatura_c": -1.8, "humedad_suelo_pct": 23.4, "humedad_aire_pct": 81}),
    (
        "2. Campo de más (viento_kmh)",
        {
            "ts": ts,
            "meta": meta,
            "temperatura_c": -1.8,
            "humedad_suelo_pct": 23.4,
            "humedad_aire_pct": 81,
            "viento_kmh": 3,
        },
    ),
    (
        "3. Error de tipeo (temperatua_c)",
        {"ts": ts, "meta": meta, "temperatua_c": -1.8, "humedad_suelo_pct": 23.4, "humedad_aire_pct": 81},
    ),
    (
        "4. Campo de más dentro de meta (color)",
        {
            "ts": ts,
            "meta": {**meta, "color": "rojo"},
            "temperatura_c": -1.8,
            "humedad_suelo_pct": 23.4,
            "humedad_aire_pct": 81,
        },
    ),
    (
        "5. Tipo equivocado (temperatura_c como texto)",
        {"ts": ts, "meta": meta, "temperatura_c": "-1.8", "humedad_suelo_pct": 23.4, "humedad_aire_pct": 81},
    ),
    (
        "6. Falta un campo obligatorio (humedad_aire_pct)",
        {"ts": ts, "meta": meta, "temperatura_c": -1.8, "humedad_suelo_pct": 23.4},
    ),
    (
        "7. Simulación en vivo con escenario_id en meta",
        {
            "ts": ts,
            "meta": {**meta, "fuente": "simulacion_en_vivo", "escenario_id": "demo-1"},
            "temperatura_c": -3.0,
            "humedad_suelo_pct": 23.4,
            "humedad_aire_pct": 85,
        },
    ),
]

colecciones_antes = set(bd.list_collection_names())
print("Versión del servidor:", cliente.server_info()["version"], "| pymongo:", __import__("pymongo").version)
print("---")

# Para saber cuál documento es cuál, a cada uno se le agrega un índice "_i"
# antes de mandarlo, y se lo saca del esquema con $unset ANTES de validar.
documentos = [{**doc, "_i": i} for i, (_, doc) in enumerate(casos)]

try:
    validos = bd.aggregate(
        [
            {"$documents": documentos},  # documentos "en el aire", no se guardan
            {"$set": {"_tmp": "$_i"}},  # guardamos la etiqueta aparte
            {"$unset": "_i"},  # la sacamos para que no cuente como campo de más
            {"$match": {"$jsonSchema": {**esquema, "properties": {**esquema["properties"], "_tmp": {}}}}},
            {"$project": {"_tmp": 1}},
        ]
    )
    indices_validos = {d["_tmp"] for d in validos}
    for i, (descripcion, _) in enumerate(casos):
        print(("VÁLIDO   " if i in indices_validos else "INVÁLIDO ") + "| " + descripcion)
except Exception as e:  # noqa: BLE001 — en un spike queremos ver cualquier error
    print("ERROR | $documents + $jsonSchema |", str(e)[:200])

print("---")
# ¿Se guardó algo? $documents no debería crear ninguna colección.
nuevas = set(bd.list_collection_names()) - colecciones_antes
print("Colecciones nuevas creadas al validar:", sorted(nuevas) or "ninguna (no se guardó nada)")

# Rendimiento: validar un lote como el que va a insertar el simulador.

lote = [{**casos[0][1], "_i": i} for i in range(5000)]
inicio = time.perf_counter()
resultado = list(
    bd.aggregate(
        [
            {"$documents": lote},
            {"$unset": "_i"},
            {"$match": {"$jsonSchema": esquema}},
            {"$count": "validos"},
        ]
    )
)
duracion = time.perf_counter() - inicio
validas = resultado[0]["validos"] if resultado else 0
print(f"Lote de 5000 lecturas validado en {duracion:.2f} s: {validas} válidas")
