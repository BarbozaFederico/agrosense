"""Prueba de "Alertas" (ADR-020): los datos, los textos y las consultas de apoyo.

Pregunta: ¿`armar_alertas` arma bien la noche, el historial y las semanas, los textos dicen lo que pasó, los filtros
filtran y las consultas de apoyo devuelven lo que dice la base?

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m dashboard.probar_alertas

Los casos de `armar_alertas` y de los textos usan datos armados a mano (no tocan la base). Los de las consultas de
apoyo leen la base de PRUEBA `agrosense_tests` (si está vacía, corré antes  python -m db.queries.probar_consultas).
No escribe nada.
"""

import logging
import sys
from datetime import date, datetime, timedelta, timezone

logging.getLogger("streamlit.runtime.caching.cache_data_api").setLevel(logging.ERROR)

from dashboard import data, formato, piezas_alertas as pa  # noqa: E402
from db.conexion import obtener_base, preparar_consola  # noqa: E402
from db.queries import alertas_pantalla as ap, comun  # noqa: E402
from db.schemas.probar_esquemas import Resumen  # noqa: E402

FECHA = date(2026, 10, 5)
INICIO_UTC = datetime(2026, 10, 4, 21, 0, tzinfo=timezone.utc)  # 18:00 de Argentina
CATALOGO = {
    "fincas": [
        {"_id": "F-A", "nombre": "Finca <A>", "departamento": "San Rafael"},
        {"_id": "F-B", "nombre": "Finca B", "departamento": "Tupungato"},
    ],
    "parcelas": [
        {"_id": "P-A-1", "finca_id": "F-A", "nombre": "Cuartel 1"},
        {"_id": "P-A-2", "finca_id": "F-A", "nombre": "Cuartel 2"},
        {"_id": "P-B-1", "finca_id": "F-B", "nombre": "Cuartel 1"},
    ],
    "nodos": [],
}
ETAPAS = [
    {"bbch_desde": 0, "bbch_hasta": 0, "nombre": "Yema dormida"},
    {"bbch_desde": 7, "bbch_hasta": 10, "nombre": "Brotación"},
    {"bbch_desde": 60, "bbch_hasta": 71, "nombre": "Floración y cuaje"},
]


def alerta(
    parcela="P-A-1", tipo="helada", desde_h=6, hasta_h=9, extremo=-5.0, umbral=-3.9, bbch=7, riesgo=None
) -> dict:
    return {
        "tipo": tipo,
        "parcela_id": parcela,
        "estado": "cerrada",
        "inicio": INICIO_UTC + timedelta(hours=desde_h),
        "fin": None if hasta_h is None else INICIO_UTC + timedelta(hours=hasta_h),
        "etapa_bbch": bbch,
        "umbral": umbral,
        "valor_extremo": extremo,
        "riesgo": riesgo,
    }


def riesgo(nivel="alto", agravantes=()) -> dict:
    return {"nivel": nivel, "margen_c": -1.1, "agravantes": list(agravantes)}


def armar(noche=(), historial=(), semanas=()) -> dict:
    return data.armar_alertas(FECHA, list(noche), list(historial), list(semanas), CATALOGO, ETAPAS)


def semana(dia: date, depto: str, alertas: int = 2, minima: float = -4.0) -> dict:
    return {
        "semana": comun.medianoche_local(dia),
        "departamento": depto,
        "alertas": alertas,
        "parcelas_afectadas": alertas,
        "minima_brote_c": minima,
    }


def main() -> None:
    preparar_consola()
    r = Resumen()

    # ---- nombre_de_etapa
    r.chequear(
        data.nombre_de_etapa(8, ETAPAS) == "Brotación" and data.nombre_de_etapa(0, ETAPAS) == "Yema dormida",
        "el número BBCH se traduce al nombre de su etapa (en el borde del rango también)",
    )
    r.chequear(
        data.nombre_de_etapa(30, ETAPAS) == "BBCH 30" and data.nombre_de_etapa(5, []) == "BBCH 5",
        "un BBCH sin etapa conocida se muestra como número, sin romper",
    )

    # ---- armar_alertas
    helada = alerta(riesgo=riesgo("alto", ["duracion"]))
    riego = alerta("P-B-1", "riego", 2, 4, extremo=7.76, umbral=7.8, bbch=60)
    d = armar(noche=[helada, riego], historial=[riego, helada])
    f0 = d["noche"][0]
    r.chequear(
        f0["parcela"] == "Cuartel 1"
        and f0["finca"] == "Finca <A>"
        and f0["departamento"] == "San Rafael"
        and f0["etapa"] == "Brotación",
        "cada alerta lleva su parcela, finca, departamento y la etapa por nombre",
    )
    r.chequear(f0["inicio"].hour == 0 and f0["fin"].hour == 3, "los horarios de la alerta están en hora de Argentina")
    r.chequear(
        abs(f0["horas"] - 3) < 1e-9 and abs(f0["alerta"]["desde"] - 6 / 18) < 1e-9,
        "la duración y la posición de la barra salen de la alerta",
    )
    r.chequear(
        f0["nivel"] == "alto" and f0["agravantes"] == ["duracion"] and d["noche"][1]["nivel"] is None,
        "el riesgo solo existe en las de helada",
    )
    r.chequear(
        [f["tipo"] for f in d["historial"]] == ["riego", "helada"],
        "el historial conserva el orden que trae la consulta",
    )
    abierta = armar(noche=[alerta(hasta_h=None)])["noche"][0]
    r.chequear(
        abierta["fin"] is None and abierta["alerta"]["en_curso"] and abs(abierta["horas"] - 12) < 1e-9,
        "una alerta sin fin sigue en curso hasta el cierre de la noche",
    )
    r.chequear(d["departamentos"] == ["San Rafael", "Tupungato"], "los departamentos salen del catálogo, ordenados")
    sem = armar(
        semanas=[
            semana(date(2026, 9, 28), "San Rafael"),
            semana(date(2026, 10, 5), "Tupungato", 1, -3.0),
            semana(date(2026, 10, 5), "San Rafael"),
        ]
    )["semanas"]
    r.chequear(
        [s["semana"].date() for s in sem] == [date(2026, 9, 28), date(2026, 10, 5)],
        "las semanas de Q8 se agrupan y quedan ordenadas",
    )
    r.chequear(
        set(sem[1]["por_departamento"]) == {"San Rafael", "Tupungato"} and sem[1]["actual"] and not sem[0]["actual"],
        "la semana de la fecha elegida (lunes 5/10) queda marcada",
    )
    r.chequear(
        armar(semanas=[semana(date(2026, 10, 7), "San Rafael")])["semanas"][0]["actual"] is False,
        "una semana que empieza otro día no se marca como la elegida",
    )
    vacio = armar()
    r.chequear(
        vacio["noche"] == [] and vacio["historial"] == [] and vacio["semanas"] == [],
        "sin alertas todo queda vacío sin romper",
    )

    # ---- filtros y orden
    filas = d["noche"]
    r.chequear(
        len(pa.filtrar(filas, None, None)) == 2 and [f["tipo"] for f in pa.filtrar(filas, "riego", None)] == ["riego"],
        "el filtro de tipo filtra",
    )
    r.chequear(
        [f["finca_id"] for f in pa.filtrar(filas, None, "F-B")] == ["F-B"] and pa.filtrar(filas, "helada", "F-B") == [],
        "el filtro de finca filtra y se combina con el de tipo",
    )
    peor = alerta("P-A-2", extremo=-8.0)
    orden = pa.ordenar_por_gravedad(armar(noche=[riego, helada, peor])["noche"])
    r.chequear(
        [f["parcela_id"] for f in orden] == ["P-A-2", "P-A-1", "P-B-1"],
        "primero la helada que más pasó el umbral, después la otra helada y al final el riego",
    )

    # ---- textos
    f, det = pa.frase_de_alertas(armar(noche=[helada, peor])["noche"])
    r.chequear(
        f == "2 alertas de helada esta noche, en Finca <A> (San Rafael).",
        "la frase cuenta las alertas y dice en qué finca",
    )
    r.chequear(
        "La más fuerte: Cuartel 2 de Finca <A>, −8,0 °C en el brote (umbral −3,9 °C), 3 h 00 min." in det,
        "el detalle dice la más fuerte con su umbral y duración",
    )
    f, det = pa.frase_de_alertas(filas)
    r.chequear(
        f == "1 alerta de helada y 1 de riego esta noche, en 2 fincas." and "Cuartel 1 de Finca <A>" in det,
        "con helada y riego en dos fincas lo dice",
    )
    f, det = pa.frase_de_alertas([f for f in filas if f["tipo"] == "riego"])
    r.chequear(
        f.startswith("1 alerta de riego") and "llegó a 7,76 % de humedad de suelo (umbral 7,80 %)" in det,
        "una de riego muestra humedad contra umbral con 2 decimales",
    )
    f, det = pa.frase_de_alertas([], None)
    r.chequear(
        f == "No hubo alertas esta noche." and "barra lateral" in det, "sin alertas lo dice y manda a la barra lateral"
    )
    r.chequear(
        pa.frase_de_alertas([], "riego") == ("No hubo alertas de riego esta noche.", ""),
        "sin alertas de riego, la frase nombra el filtro",
    )
    tabla = pa.tabla_de_la_noche(filas, FECHA)
    r.chequear(
        "detalle?parcela=P-A-1&fecha=2026-10-05" in tabla and "Finca &lt;A&gt;" in tabla and "<A>" not in tabla,
        "la tabla enlaza al detalle con la fecha y escapa el texto de la base",
    )
    r.chequear(
        'class="riego"' in tabla
        and "−5,0 °C" in tabla
        and "7,76 %" in tabla
        and "Alto" in tabla
        and "larga duración" in tabla,
        "la tabla dibuja la barra de riego aparte y muestra valores con su unidad y el riesgo",
    )
    r.chequear(tabla.index("Cuartel 1") < tabla.index("Riego"), "la helada va antes que el riego")
    en_curso = pa.tabla_de_la_noche(armar(noche=[alerta(hasta_h=None)])["noche"], FECHA)
    r.chequear(
        "12 h 00 min+" in en_curso and "abierta" in en_curso, "una alerta en curso lo marca con + y barra abierta"
    )

    # ---- historial
    h = pa.filas_de_historial(d["historial"])
    r.chequear(
        h[0]["Tipo"] == "Riego"
        and h[0]["Valor extremo"] == "7,76 %"
        and h[0]["Umbral"] == "7,80 %"
        and h[1]["Valor extremo"] == "−5,0 °C",
        "el historial trae el valor extremo y el umbral como texto con su unidad",
    )
    r.chequear(
        h[0]["Estado"] == "Cerrada"
        and pa.filas_de_historial(armar(historial=[alerta(hasta_h=None)])["historial"])[0]["Estado"] == "En curso",
        "el historial distingue cerradas y en curso",
    )
    r.chequear(
        all(isinstance(x["Duración (h)"], float) for x in h) and h[0]["Parcela"] == "Cuartel 1 · Finca B",
        "la duración es numérica (ordenable) y la parcela lleva su finca",
    )

    # ---- semanas (Q8)
    semanas = armar(
        semanas=[semana(date(2026, 10, 5), "San Rafael", 2, -8.3), semana(date(2026, 9, 28), "Tupungato", 1, -6.7)]
    )["semanas"]
    t = pa.tabla_de_semanas(semanas, ["San Rafael", "Tupungato"])
    r.chequear(
        "<b>2</b> alertas" in t and "<b>1</b> alerta<" in t and "mín. −8,3 °C" in t and ">-</td>" in t,
        "la tabla de semanas muestra cantidad y mínima, con guion donde no hubo",
    )
    r.chequear(
        "semana elegida" in t and t.index("28 de sep") < t.index("5 de oct"),
        "marca la semana elegida y va de la más vieja a la más nueva",
    )
    r.chequear(t.count('<th class="num">') == 2 and "Tupungato" in t, "las columnas son los departamentos pedidos")
    r.chequear("Sin heladas registradas" in pa.tabla_de_semanas([], ["San Rafael"]), "sin semanas con helada lo dice")
    r.chequear(
        formato.marca_tipo("helada").count("helada") >= 1
        and "Riego" in formato.marca_tipo("riego")
        and "atencion" in formato.marca_tipo("riego"),
        "cada tipo de alerta lleva su forma y su palabra",
    )

    # ---- consultas de apoyo contra la base de prueba
    bd = obtener_base("agrosense_tests")
    if bd.alertas.count_documents({}) == 0:
        print("(la base de prueba está vacía: se omiten las consultas de apoyo)")
    else:
        inicio, fin = comun.ventana_noche(FECHA)
        noche = ap.alertas_de_la_noche(bd, FECHA)
        r.chequear(
            sorted(a["parcela_id"] for a in noche) == ["P-SR-1", "P-SR-2"] and {a["tipo"] for a in noche} == {"helada"},
            "la noche del 5/10 tiene las 2 alertas de helada de San Rafael",
        )
        r.chequear(
            [a["tipo"] for a in ap.alertas_de_la_noche(bd, date(2026, 11, 17))] == ["riego"],
            "la noche del 17/11 tiene una alerta de riego (el otro tipo)",
        )
        r.chequear(
            ap.alertas_de_la_noche(bd, date(2026, 10, 8)) == [], "una noche sin alertas devuelve una lista vacía"
        )
        todo = ap.historial(bd, date(2027, 3, 31))
        r.chequear(
            len(todo) == 35 and sum(a["tipo"] == "helada" for a in todo) == 10,
            "al final de la temporada el historial tiene las 35 alertas (10 de helada y 25 de riego)",
        )
        r.chequear(
            all(a["inicio"] <= b["inicio"] for b, a in zip(todo, todo[1:])),
            "el historial viene de la más reciente a la más antigua",
        )
        r.chequear(
            len(ap.historial(bd, date(2027, 3, 31), 5)) == 5 and ap.historial(bd, date(2026, 9, 1)) == [],
            "el límite recorta y antes de la primera alerta no hay historial",
        )
        r.chequear(
            all(comun.a_utc(a["inicio"]) < fin for a in ap.historial(bd, FECHA)) and len(ap.historial(bd, FECHA)) == 8,
            "el historial del 5/10 solo incluye alertas que empezaron antes del cierre de esa noche (8)",
        )
        etapas = ap.etapas_del_malbec(bd)
        r.chequear(
            len(etapas) == 13 and data.nombre_de_etapa(7, etapas) == "Brotación",
            "las 13 etapas del Malbec traducen el BBCH",
        )
        real = data.alertas.__wrapped__(FECHA)
        r.chequear(
            len(real["noche"]) == 2
            and len(real["historial"]) == 8
            and len(real["semanas"]) == 3
            and real["semanas"][-1]["actual"],
            "el 5/10 hay 2 alertas en la noche, 8 en el historial y 3 semanas con helada (la última, la elegida)",
        )
        for dia in (date(2026, 9, 1), date(2026, 9, 22), date(2026, 10, 8), date(2026, 11, 17), date(2027, 3, 31)):
            dd = data.alertas.__wrapped__(dia)
            pa.tabla_de_la_noche(dd["noche"], dia), pa.filas_de_historial(dd["historial"]), pa.tabla_de_semanas(
                dd["semanas"], dd["departamentos"]
            )
            pa.frase_de_alertas(dd["noche"])
        r.chequear(
            True,
            "la pantalla se arma sin errores en 5 fechas (inicio, helada, noche tranquila, riego y fin de la temporada)",
        )

    print(f"\n{r.total - r.fallas} de {r.total} casos pasaron.")
    sys.exit(1 if r.fallas else 0)


if __name__ == "__main__":
    main()
