"""Crea las 10 colecciones con sus esquemas y comprueba que quedaron bien.

La usan crear_colecciones.py (base real) y probar_esquemas.py (base de prueba).

Reglas (ADR-006 y ADR-007, spike de esquemas del 15/10/2026):
    - Colecciones comunes: validador $jsonSchema con validationLevel "strict"
      (valida todos los inserts y updates) y validationAction "error" (rechaza).
    - lecturas: serie temporal SIN validador (MongoDB 9.0.2 no lo permite).
    - Ante cualquier error se DETIENE (lanza una excepción). Si siguiera, el primer
      insert crearía la colección como común y sin validación, y el error quedaría
      oculto (spike de esquemas, prueba 1).
"""

from pymongo.database import Database

from db.schemas import ESQUEMAS


def crear_coleccion(bd: Database, modulo) -> str:
    """Crea (o actualiza) una colección y devuelve un texto con lo que hizo."""
    existe = modulo.NOMBRE in bd.list_collection_names()

    if modulo.SERIE_TEMPORAL:
        if not existe:
            bd.create_collection(modulo.NOMBRE, timeseries=modulo.OPCIONES_SERIE_TEMPORAL)
        info = next(bd.list_collections(filter={"name": modulo.NOMBRE}))
        if info["type"] != "timeseries":
            raise RuntimeError(f"{modulo.NOMBRE} existe pero no es serie temporal (tipo: {info['type']})")
        estado = "ya existía" if existe else "creada"
        return (
            f"{modulo.NOMBRE} | serie temporal {estado} | sin validador: "
            "se valida con db/schemas/validar.py y se audita (ADR-007)"
        )

    opciones = {
        "validator": {"$jsonSchema": modulo.ESQUEMA},
        "validationLevel": "strict",
        "validationAction": "error",
    }
    if existe:
        # collMod cambia las opciones de una colección existente sin borrar sus datos.
        bd.command("collMod", modulo.NOMBRE, **opciones)
    else:
        bd.create_collection(modulo.NOMBRE, **opciones)

    info = next(bd.list_collections(filter={"name": modulo.NOMBRE}))
    if "validator" not in info["options"] or info["options"].get("validationAction") != "error":
        raise RuntimeError(f"{modulo.NOMBRE} quedó sin validador")
    estado = "actualizada" if existe else "creada"
    return f"{modulo.NOMBRE} | colección común {estado} | validador instalado"


def crear_colecciones(bd: Database) -> None:
    """Crea las 10 colecciones en la base indicada, mostrando cada paso."""
    for modulo in ESQUEMAS:
        print("OK | " + crear_coleccion(bd, modulo))
