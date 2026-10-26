"""Prueba de "Estado de nodos" (ADR-021): los datos, los textos y la consulta de apoyo.

Pregunta: ¿`armar_nodos` decide bien qué nodo reporta y los ordena, los textos dicen lo que pasó, y la consulta de apoyo
coincide con Q5 (los que no reportan) para cualquier "ahora"?

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m dashboard.probar_nodos

Los casos de `armar_nodos` y de los textos usan datos armados a mano (no tocan la base). Los de la consulta de apoyo
leen la base de PRUEBA `agrosense_tests` (si está vacía, corré antes  python -m db.queries.probar_consultas).
No escribe nada.
"""

import logging
import sys
from datetime import date, datetime, timedelta, timezone

logging.getLogger("streamlit.runtime.caching.cache_data_api").setLevel(logging.ERROR)

from dashboard import data, formato, piezas_nodos as pn  # noqa: E402
from db.conexion import obtener_base, preparar_consola  # noqa: E402
from db.queries import comun, estado_nodos as en, q5_nodos_sin_reportar as q5  # noqa: E402
from db.schemas.probar_esquemas import Resumen  # noqa: E402

FECHA = date(2026, 10, 5)
CIERRE_UTC = datetime(2026, 10, 5, 15, 0, tzinfo=timezone.utc)  # 12:00 de Argentina
CATALOGO = {
    "fincas": [
        {"_id": "F-A", "nombre": "Finca <A>", "departamento": "San Rafael"},
        {"_id": "F-B", "nombre": "Finca B", "departamento": "Tupungato"},
    ],
    "parcelas": [
        {"_id": "P-A-1", "finca_id": "F-A", "nombre": "Cuartel 1"},
        {"_id": "P-B-1", "finca_id": "F-B", "nombre": "Cuartel 1"},
    ],
    "nodos": [],
}


def nodo(nid: str, minutos: float | None, parcela: str = "P-A-1", finca: str = "F-A", estado: str = "activo") -> dict:
    return {
        "nodo_id": nid,
        "parcela_id": parcela,
        "finca_id": finca,
        "estado": estado,
        "ultima_lectura": None if minutos is None else (CIERRE_UTC - timedelta(minutes=minutos)).replace(tzinfo=None),
        "minutos_sin_reportar": minutos,
    }


def armar(*nodos, limite=30) -> dict:
    return data.armar_nodos(FECHA, list(nodos), CATALOGO, limite)


def main() -> None:
    preparar_consola()
    r = Resumen()

    # ---- formato
    f = formato.duracion_larga
    r.chequear(
        [f(0), f(5), f(59.6)] == ["0 min", "5 min", "1 h 00 min"],
        "los minutos se escriben como minutos (59,6 redondea a 1 h)",
    )
    r.chequear(
        [f(65), f(725), f(1439)] == ["1 h 05 min", "12 h 05 min", "23 h 59 min"],
        "menos de un día se escribe en horas y minutos",
    )
    r.chequear(
        [f(1440), f(1500), f(2880), f(20885)] == ["1 día", "1 día 1 h", "2 días", "14 días 12 h"],
        "desde un día se escribe en días (con singular) y horas",
    )
    r.chequear(
        "Reporta" in formato.marca_reporte(True) and "normal" in formato.marca_reporte(True),
        "reportar lleva el círculo verde y la palabra",
    )
    r.chequear(
        "Sin reportar" in formato.marca_reporte(False) and "atencion" in formato.marca_reporte(False),
        "no reportar lleva el triángulo ámbar y la palabra",
    )

    # ---- armar_nodos
    d = armar(
        nodo("N-1", 5), nodo("N-2", 30), nodo("N-3", 31), nodo("N-4", None), nodo("N-5", 600, estado="mantenimiento")
    )
    estados = {n["nodo_id"]: n["reporta"] for n in d["filas"]}
    r.chequear(
        estados == {"N-1": True, "N-2": True, "N-3": False, "N-4": False, "N-5": False},
        "reporta hasta el límite (30 min justos todavía reporta); más, o sin lecturas, no reporta",
    )
    r.chequear(
        [n["nodo_id"] for n in d["filas"]] == ["N-4", "N-5", "N-3", "N-1", "N-2"],
        "primero los que no reportan (sin lecturas, luego el de más tiempo) y después los demás por nombre",
    )
    r.chequear(
        d["ahora"].hour == 12 and d["limite_min"] == 30, "el 'ahora' es el cierre de la noche en hora de Argentina"
    )
    r.chequear(
        d["filas"][3]["ultima"].hour == 11 and d["filas"][3]["ultima"].minute == 55,
        "el último reporte se pasa a hora de Argentina",
    )
    r.chequear(
        d["ultima_de_la_red"] == max(n["ultima"] for n in d["filas"] if n["ultima"]),
        "el último dato de la red es el más reciente de todos",
    )
    r.chequear(
        armar(nodo("N-1", None))["ultima_de_la_red"] is None and armar()["filas"] == [],
        "sin lecturas ni nodos no se rompe",
    )
    r.chequear(armar(nodo("N-1", 10), limite=5)["filas"][0]["reporta"] is False, "el límite sale de la configuración")
    r.chequear(
        armar(nodo("N-1", 0))["filas"][0]["parcela"] == "Cuartel 1"
        and armar(nodo("N-9", 0, "P-B-1", "F-B"))["filas"][0]["departamento"] == "Tupungato",
        "cada nodo lleva el nombre de su parcela, su finca y su departamento",
    )

    # ---- textos
    filas = d["filas"]
    ok = armar(nodo("N-1", 0), nodo("N-2", 5))["filas"]
    r.chequear(
        pn.frase_de_nodos(ok, 30)
        == ("Los 2 nodos reportan.", "Un nodo se marca como sin reportar cuando pasan más de 30 minutos sin lecturas."),
        "si todos reportan lo dice y explica el límite",
    )
    frase, det = pn.frase_de_nodos(armar(nodo("N-1", 0), nodo("N-5", 20885, estado="mantenimiento"))["filas"], 30)
    r.chequear(
        frase == "1 de 2 nodos sin reportar: N-5."
        and "lleva 14 días 12 h sin datos" in det
        and "Cuartel 1 de Finca <A>" in det,
        "con uno sin reportar dice cuál, desde hace cuánto y de qué parcela",
    )
    frase, det = pn.frase_de_nodos(filas, 30)
    r.chequear(
        frase == "3 de 5 nodos sin reportar: N-4, N-5, N-3." and "N-4" in det and "no tiene ninguna lectura" in det,
        "con varios sin reportar los lista y el detalle cuenta el peor (el que no tiene lecturas)",
    )
    r.chequear(pn.frase_de_nodos([], 30)[0] == "No hay nodos para mostrar.", "sin nodos la frase lo dice")
    r.chequear(
        pn.hace(filas[0]) == "-"
        and pn.hace(filas[3]) == "5 min"
        and pn.hace(armar(nodo("N-1", 0))["filas"][0]) == "al cierre",
        "'hace' escribe '-', los minutos o 'al cierre'",
    )
    tabla = pn.tabla_de_nodos(filas, FECHA)
    r.chequear(
        "detalle?parcela=P-A-1&fecha=2026-10-05" in tabla and "Finca &lt;A&gt;" in tabla and "<A>" not in tabla,
        "la tabla enlaza al detalle con la fecha y escapa el texto de la base",
    )
    r.chequear(
        tabla.count("sin-reporte") == 3 and "Sin lecturas" in tabla and "Sin reportar" in tabla,
        "los 3 nodos que no reportan van resaltados y el que no tiene lecturas lo dice",
    )
    mant = pn.tabla_de_nodos(
        armar(nodo("N-1", 5, estado="mantenimiento"), nodo("N-2", 99, estado="activo"), nodo("N-3", 5, estado="baja"))[
            "filas"
        ],
        FECHA,
    )
    r.chequear(
        "sigue reportando" in mant and "activo, pero no reporta" in mant and mant.count("sigue reportando") == 2,
        "cuando el estado administrativo contradice al reporte real, la celda lo aclara",
    )
    r.chequear("chip atencion" in mant and "chip neutro" in mant, "mantenimiento va ámbar y baja va gris")
    hostil = pn.tabla_de_nodos(armar(nodo("<script>", 0))["filas"], FECHA)
    r.chequear("<script>" not in hostil, "el nombre de un nodo se escapa")
    r.chequear(
        [n["nodo_id"] for n in pn.filtrar(filas, "F-B")] == [] and len(pn.filtrar(filas, None)) == 5,
        "el filtro de finca filtra",
    )

    # ---- consulta de apoyo contra la base de prueba
    bd = obtener_base("agrosense_tests")
    if bd.nodos.count_documents({}) == 0:
        print("(la base de prueba está vacía: se omite la consulta de apoyo)")
    else:
        todos = en.ultimo_reporte(bd, CIERRE_UTC)
        r.chequear(
            len(todos) == 12 and [n["nodo_id"] for n in todos] == sorted(n["nodo_id"] for n in todos),
            "devuelve los 12 nodos, ordenados por nombre",
        )
        r.chequear(
            all(n["minutos_sin_reportar"] is not None and n["minutos_sin_reportar"] <= 5 for n in todos),
            "el 5/10 a las 12:00 todos reportaron hace 5 minutos o menos",
        )
        diferencias = []
        for dia in [date(2026, 9, 1) + timedelta(days=i) for i in range(0, 212, 3)] + [
            date(2026, 12, 3),
            date(2027, 3, 2),
            date(2027, 3, 17),
            date(2027, 3, 31),
        ]:
            ahora = comun.ventana_noche(dia)[1]
            sin_q5 = sorted(x["nodo_id"] for x in q5.consultar(bd, ahora))
            sin_mia = sorted(
                x["nodo_id"]
                for x in data.armar_nodos(dia, en.ultimo_reporte(bd, ahora), CATALOGO_REAL(bd), 30)["filas"]
                if not x["reporta"]
            )
            if sin_q5 != sin_mia:
                diferencias.append(dia)
        r.chequear(
            not diferencias,
            "los nodos sin reportar de la pantalla coinciden con los de Q5 en 75 fechas de la temporada (incluidas 3/12, 2/3 y 17/3)",
        )
        r.chequear(
            sorted(x["nodo_id"] for x in q5.consultar(bd, comun.ventana_noche(date(2027, 3, 31))[1])) == ["N-TU-2-B"],
            "el último día de la temporada solo N-TU-2-B no reporta",
        )
        real = data.nodos.__wrapped__(date(2027, 3, 31))
        r.chequear(
            real["filas"][0]["nodo_id"] == "N-TU-2-B"
            and not real["filas"][0]["reporta"]
            and real["filas"][0]["estado_nodo"] == "mantenimiento"
            and abs(real["filas"][0]["minutos"] - 20885) < 1,
            "el 31/3 la pantalla pone primero a N-TU-2-B, en mantenimiento y con 20.885 minutos",
        )
        ok_real = data.nodos.__wrapped__(FECHA)
        r.chequear(
            all(x["reporta"] for x in ok_real["filas"])
            and len(ok_real["filas"]) == 12
            and ok_real["ultima_de_la_red"].hour == 12,
            "el 5/10 los 12 nodos reportan y el último dato es de las 12:00",
        )
        mantenimiento = [x for x in ok_real["filas"] if x["estado_nodo"] == "mantenimiento"]
        r.chequear(
            len(mantenimiento) == 1 and mantenimiento[0]["nodo_id"] == "N-TU-2-B" and mantenimiento[0]["reporta"],
            "N-TU-2-B figura en mantenimiento pero el 5/10 sigue reportando",
        )
        pn.tabla_de_nodos(real["filas"], date(2027, 3, 31)), pn.frase_de_nodos(real["filas"], 30)

    print(f"\n{r.total - r.fallas} de {r.total} casos pasaron.")
    sys.exit(1 if r.fallas else 0)


def CATALOGO_REAL(bd) -> dict:
    from db.queries import resumen_manana as rm

    return rm.catalogo(bd)


if __name__ == "__main__":
    main()
