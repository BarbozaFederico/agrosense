"""Datos compartidos por las pruebas 1 a 3 del spike de esquemas.

Se importa con `from _comun import ...`: funciona porque Python busca primero
en la carpeta del script que se está corriendo (scripts/spike-esquemas/).
"""

from datetime import datetime, timezone


def esquema_lectura(incluir_id: bool) -> dict:
    """Esquema de una lectura (simplificado de modelo-datos.md, sección 3.4).

    incluir_id: si es True, declara _id en properties; si es False, no lo declara.
    """
    properties = {
        "ts": {"bsonType": "date"},
        "meta": {
            "bsonType": "object",
            "required": ["nodo_id", "parcela_id", "finca_id", "fuente"],
            "additionalProperties": False,          # meta también cerrado
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
    }
    if incluir_id:
        properties["_id"] = {"bsonType": "objectId"}
    return {
        "bsonType": "object",
        "required": ["ts", "meta", "temperatura_c", "humedad_suelo_pct", "humedad_aire_pct"],
        "additionalProperties": False,
        "properties": properties,
    }


META = {"nodo_id": "N-SR-1-A", "parcela_id": "P-SR-1", "finca_id": "F-SR", "fuente": "simulado"}


def casos(ts: datetime) -> list[tuple[str, dict]]:
    """Los siete documentos de prueba, con la fecha indicada."""
    return [
        ("1. Documento válido",
         {"ts": ts, "meta": META, "temperatura_c": -1.8, "humedad_suelo_pct": 23.4, "humedad_aire_pct": 81}),
        ("2. Campo de más (viento_kmh)",
         {"ts": ts, "meta": META, "temperatura_c": -1.8, "humedad_suelo_pct": 23.4, "humedad_aire_pct": 81, "viento_kmh": 3}),
        ("3. Error de tipeo (temperatua_c)",
         {"ts": ts, "meta": META, "temperatua_c": -1.8, "humedad_suelo_pct": 23.4, "humedad_aire_pct": 81}),
        ("4. Campo de más dentro de meta (color)",
         {"ts": ts, "meta": {**META, "color": "rojo"}, "temperatura_c": -1.8, "humedad_suelo_pct": 23.4, "humedad_aire_pct": 81}),
        ("5. Tipo equivocado (temperatura_c como texto)",
         {"ts": ts, "meta": META, "temperatura_c": "-1.8", "humedad_suelo_pct": 23.4, "humedad_aire_pct": 81}),
        ("6. Falta un campo obligatorio (humedad_aire_pct)",
         {"ts": ts, "meta": META, "temperatura_c": -1.8, "humedad_suelo_pct": 23.4}),
        ("7. Simulación en vivo con escenario_id en meta",
         {"ts": ts, "meta": {**META, "fuente": "simulacion_en_vivo", "escenario_id": "demo-1"},
          "temperatura_c": -3.0, "humedad_suelo_pct": 23.4, "humedad_aire_pct": 85}),
    ]


TS = datetime(2026, 9, 14, 9, 0, tzinfo=timezone.utc)


def probar_insercion(coleccion, descripcion: str, doc: dict) -> None:
    """Inserta una copia del documento y muestra si entró o fue rechazado."""
    try:
        coleccion.insert_one(dict(doc))
        print(f"ENTRA     | {coleccion.name} | {descripcion}")
    except Exception as e:  # noqa: BLE001 — en un spike queremos ver cualquier error
        print(f"RECHAZADO | {coleccion.name} | {descripcion} | {str(e).split(', full error')[0]}")
