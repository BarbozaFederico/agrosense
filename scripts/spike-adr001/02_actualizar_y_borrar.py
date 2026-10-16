"""Spike ADR-001 · Prueba 2.

Pregunta: ¿qué se puede actualizar y qué se puede borrar en una serie temporal?
Importa para RF-15 ("Reiniciar demo"): hay que poder borrar lo que generó una
simulación en vivo.

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python scripts/spike-adr001/02_actualizar_y_borrar.py

Usa la base de PRUEBA `spike_agrosense`. No toca ninguna base real.
Cada caso arranca desde cero (preparar()) para que no se mezclen entre sí.
"""

import sys
from datetime import datetime, timezone

from pymongo import MongoClient

sys.stdout.reconfigure(encoding="utf-8")

cliente = MongoClient("mongodb://localhost:27017")
bd = cliente["spike_agrosense"]


def hora(h: int, m: int) -> datetime:
    return datetime(2026, 10, 13, h, m, tzinfo=timezone.utc)


def meta(nodo: str, **extra) -> dict:
    return {"nodo_id": nodo, "parcela_id": "P-1", "finca_id": "F-1", **extra}


def preparar() -> None:
    """Deja la colección en un estado conocido: 3 lecturas normales y 2 de una
    "simulación en vivo", marcadas con escenario_id DENTRO de meta."""
    cliente.drop_database("spike_agrosense")
    bd.create_collection(
        "lecturas",
        timeseries={"timeField": "ts", "metaField": "meta", "granularity": "minutes"},
    )
    bd.lecturas.insert_many([
        {"ts": hora(3, 0), "meta": meta("N-01"), "temperatura": -0.4},
        {"ts": hora(3, 5), "meta": meta("N-01"), "temperatura": -0.8},
        {"ts": hora(3, 0), "meta": meta("N-02"), "temperatura": -0.2},
        # Lecturas de una simulación en vivo (se marcan con escenario_id)
        {"ts": hora(4, 0), "meta": meta("N-01", escenario_id="demo-1"), "temperatura": -3.0},
        {"ts": hora(4, 5), "meta": meta("N-01", escenario_id="demo-1"), "temperatura": -3.2},
    ])


def probar(descripcion: str, accion) -> None:
    """Prepara la colección, corre la acción y muestra OK o ERROR.
    Si MongoDB rechaza la operación, se captura el error y se sigue con el próximo caso."""
    preparar()
    try:
        resultado = accion()
        print(f"OK    | {descripcion} | resultado: {resultado} | "
              f"quedan {bd.lecturas.count_documents({})} documentos")
    except Exception as e:  # noqa: BLE001 — en un spike queremos ver cualquier error
        # Los mensajes de pymongo traen detalles extra al final: mostramos la primera parte.
        print(f"ERROR | {descripcion} | {str(e).split(', full error')[0]}")


def actualizados(r) -> str:
    return f"coincidieron {r.matched_count}, modificados {r.modified_count}"


def borrados(r) -> str:
    return f"borrados {r.deleted_count}"


print("Versión del servidor:", cliente.server_info()["version"])
print("---")

# 1) Actualizar un valor medido de una lectura puntual (filtro: nodo + hora exacta)
probar("1. Actualizar temperatura de una lectura puntual (update_one)", lambda: actualizados(
    bd.lecturas.update_one({"meta.nodo_id": "N-01", "ts": hora(3, 0)}, {"$set": {"temperatura": -9.9}})))

# 1b) Lo mismo con update_many: separa "¿falla por usar update_one?" de
#     "¿falla por querer modificar un valor medido?".
probar("1b. Actualizar temperatura con update_many (nodo + hora exacta)", lambda: actualizados(
    bd.lecturas.update_many({"meta.nodo_id": "N-01", "ts": hora(3, 0)}, {"$set": {"temperatura": -9.9}})))

# 1c) Filtro SOLO por meta, pero lo que se modifica sigue siendo un valor medido.
probar("1c. Actualizar temperatura con filtro solo por meta (todo el nodo N-01)", lambda: actualizados(
    bd.lecturas.update_many({"meta.nodo_id": "N-01"}, {"$set": {"temperatura": -9.9}})))

# 2) Actualizar un campo dentro de meta, para todo un nodo
probar("2. Cambiar meta.parcela_id de todo el nodo N-02", lambda: actualizados(
    bd.lecturas.update_many({"meta.nodo_id": "N-02"}, {"$set": {"meta.parcela_id": "P-2"}})))

# 3) Borrar por un campo de meta: es lo que usaría "Reiniciar demo"
probar("3. Borrar por meta.escenario_id", lambda: borrados(
    bd.lecturas.delete_many({"meta.escenario_id": "demo-1"})))

# 4) Borrar por rango de fechas
probar("4. Borrar lecturas anteriores a las 03:05", lambda: borrados(
    bd.lecturas.delete_many({"ts": {"$lt": hora(3, 5)}})))

# 5) Borrar por un valor medido (un campo común, no meta ni ts)
probar("5. Borrar lecturas con temperatura menor a -1", lambda: borrados(
    bd.lecturas.delete_many({"temperatura": {"$lt": -1}})))

# 6) Borrar una sola lectura (nodo + hora exacta)
probar("6. Borrar una sola lectura (delete_one)", lambda: borrados(
    bd.lecturas.delete_one({"meta.nodo_id": "N-02", "ts": hora(3, 0)})))

# 7) Borrar todo con filtro vacío
probar("7. Borrar todo (delete_many con filtro vacío)", lambda: borrados(
    bd.lecturas.delete_many({})))
