"""Mide cuántos documentos examina MongoDB con y sin cada uno de los 4 índices (RNF-01, ADR-015 y ADR-022).

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m db.indexes.medir_indices

Usa la base de PRUEBA `agrosense_tests` (si está vacía, carga el seed y la temporada ahí). No toca la base
real `agrosense`: este script BORRA y CREA índices, y no corresponde hacerlo sobre la base real.

Qué hace:
    1. Borra los 4 índices y mide cada búsqueda SIN índice.
    2. Crea los 4 índices y mide cada búsqueda CON índice.
    3. Imprime una tabla de 4 filas y los comandos de mongosh que dan esos mismos números.

La cifra es `totalDocsExamined` del `explain("executionStats")`: los documentos que MongoDB tuvo que leer.
En `lecturas` (serie temporal) cuenta grupos de lecturas ("buckets"), no lecturas sueltas.
"""

import contextlib
import io
from datetime import date

from pymongo.errors import OperationFailure

from db.conexion import obtener_base, preparar_consola
from db.indexes.crear_indices import (
    INDICES_DESCARTADOS,
    INDICES_GEOESPACIALES,
    INDICES_RENDIMIENTO,
    crear_indices,
    crear_indices_rendimiento,
    nombre_de_indice,
)
from db.queries import (
    q1_horas_bajo_cero as q1,
    q2_minima_bajo_umbral as q2,
    q3_nodos_cercanos as q3,
    q4_parcelas_en_evento as q4,
    q5_nodos_sin_reportar as q5,
    q6_humedad_suelo_horaria as q6,
    q7_litros_por_semana as q7,
    q8_heladas_por_departamento as q8,
    q9_etapa_por_grados_dia as q9,
    q10_riesgo_de_helada as q10,
)

BASE_DE_PRUEBA = "agrosense_tests"
INDICE_AUTOMATICO = "meta_1_ts_1"  # lo crea MongoDB solo en la serie temporal `lecturas`
FECHA = date(2026, 10, 5)


def funciones(bd) -> dict:
    """Cada consulta Q1 a Q10 con los parámetros de las pruebas (la noche del 5/10 y el 'ahora' por defecto)."""
    return {
        "Q1": lambda: q1.consultar(bd, FECHA),
        "Q2": lambda: q2.consultar(bd, FECHA),
        "Q3": lambda: q3.consultar(bd),
        "Q4": lambda: q4.consultar(bd),
        "Q5": lambda: q5.consultar(bd),
        "Q6": lambda: q6.consultar(bd),
        "Q7": lambda: q7.consultar(bd, "P-SR-1"),
        "Q8": lambda: q8.consultar(bd),
        "Q9": lambda: q9.consultar(bd, FECHA),
        "Q10": lambda: q10.consultar(bd, FECHA),
    }


def quitar_indices(bd) -> None:
    """Borra los índices de este proyecto (no toca el automático de las series temporales)."""
    todos = (
        [(c, f"{campo}_2dsphere") for c, campo in INDICES_GEOESPACIALES]
        + [(c, nombre_de_indice(claves)) for c, claves, _ in INDICES_RENDIMIENTO]
        + [(c, nombre_de_indice(claves)) for c, claves, _ in INDICES_DESCARTADOS]
    )
    for coleccion, nombre in todos:
        if nombre in {i["name"] for i in bd[coleccion].list_indexes()}:
            bd[coleccion].drop_index(nombre)


def casos(bd) -> list[dict]:
    """Los 4 casos: la búsqueda que usa cada índice, en Python (`busqueda`) y en mongosh (`mongosh`)."""
    lon, lat = q3.PUNTO
    area = q4.buscar_evento(bd)["area"]  # el evento más reciente, igual que Q4
    return [
        {
            "indice": "nodos { ubicacion: 2dsphere }",
            "consulta": "Q3",
            "coleccion": "nodos",
            "busqueda": {
                "filter": {"ubicacion": {"$near": {"$geometry": {"type": "Point", "coordinates": [lon, lat]}}}},
                "limit": 4,
            },
            "mongosh": "db.nodos.find({ ubicacion: { $near: { $geometry: "
            f'{{ type: "Point", coordinates: [{lon}, {lat}] }} }} }} }}).limit(4)',
        },
        {
            "indice": "parcelas { geometria: 2dsphere }",
            "consulta": "Q4",
            "coleccion": "parcelas",
            "busqueda": {"filter": {"geometria": {"$geoIntersects": {"$geometry": area}}}},
            "previo": "const area = db.eventos_climaticos.find().sort({ inicio: -1 }).limit(1).next().area",
            "mongosh": "db.parcelas.find({ geometria: { $geoIntersects: { $geometry: area } } })",
        },
        {
            "indice": "lecturas { meta.nodo_id: 1, ts: -1 }",
            "consulta": "Q5",
            "coleccion": "lecturas",
            "busqueda": {"filter": {"meta.nodo_id": "N-SR-1-A"}, "sort": {"ts": -1}, "limit": 1},
            "mongosh": 'db.lecturas.find({ "meta.nodo_id": "N-SR-1-A" }).sort({ ts: -1 }).limit(1)',
        },
        {
            "indice": "riegos { parcela_id: 1, inicio: 1 }",
            "consulta": "Q7",
            "coleccion": "riegos",
            "busqueda": {"filter": {"parcela_id": "P-SR-1"}},
            "mongosh": 'db.riegos.find({ parcela_id: "P-SR-1" })',
        },
    ]


def documentos_examinados(bd, caso: dict) -> int | None:
    """`totalDocsExamined` del explain de la búsqueda; None si MongoDB no puede resolverla (Q3 sin índice)."""
    comando = {"explain": {"find": caso["coleccion"], **caso["busqueda"]}, "verbosity": "executionStats"}
    try:
        plan = bd.command(comando)
    except OperationFailure:
        return None
    # En una serie temporal (lecturas) el explain viene dentro de stages[0].$cursor
    estadisticas = plan.get("executionStats") or plan["stages"][0]["$cursor"]["executionStats"]
    return estadisticas["totalDocsExamined"]


def medir(bd) -> list[dict]:
    """Para cada caso: documentos examinados sin índice y con índice (deja los 4 índices creados)."""
    lista = casos(bd)
    quitar_indices(bd)
    sin = [documentos_examinados(bd, c) for c in lista]
    crear_indices(bd)
    crear_indices_rendimiento(bd)
    con = [documentos_examinados(bd, c) for c in lista]
    return [{**c, "sin": s, "con": n} for c, s, n in zip(lista, sin, con)]


def tabla(filas: list[dict]) -> str:
    entero = lambda v: f"{v:,}".replace(",", ".")
    salida = [
        "| Índice | Consulta | Documentos examinados sin índice | Documentos examinados con índice | Reducción |",
        "|---|---|---|---|---|",
    ]
    for f in filas:
        if f["sin"] is None:
            sin, reduccion = "no funciona", "-"
        else:
            sin, reduccion = entero(f["sin"]), f"{(f['sin'] - f['con']) / f['sin']:.0%}"
        salida.append(f"| `{f['indice']}` | {f['consulta']} | {sin} | {entero(f['con'])} | {reduccion} |")
    return "\n".join(salida)


def comandos(filas: list[dict]) -> str:
    """Los comandos de mongosh para repetir cada medición a mano."""
    salida = []
    for f in filas:
        salida.append(f"// {f['consulta']}: {f['indice']}")
        if "previo" in f:
            salida.append(f["previo"])
        salida.append(f'{f["mongosh"]}.explain("executionStats")')
        if f["sin"] is None:
            salida.append("// sin índice no funciona: para verlo, db.nodos.dropIndex('ubicacion_2dsphere') y repetir")
        else:
            salida.append("// sin borrar el índice:")
            salida.append(f'{f["mongosh"]}.hint({{ $natural: 1 }}).explain("executionStats")')
        salida.append("")
    return "\n".join(salida)


def main() -> None:
    preparar_consola()
    bd = obtener_base(BASE_DE_PRUEBA)
    if bd.lecturas.estimated_document_count() == 0:
        from db.seeds import cargar as cargar_seed
        from simulator import generar

        print("Cargando el seed y la temporada en la base de prueba...")
        with contextlib.redirect_stdout(io.StringIO()):
            cargar_seed.cargar(bd)
            generar.escribir(bd, generar.simular(generar.cargar_contexto(bd)))

    filas = medir(bd)
    print(f"Base: {bd.name} (MongoDB {bd.client.server_info()['version']})\n")
    print(tabla(filas))
    print("\nComandos de mongosh (en la base agrosense_tests: use agrosense_tests):\n")
    print(comandos(filas))


if __name__ == "__main__":
    main()
