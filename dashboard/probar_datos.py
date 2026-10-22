"""Prueba de los datos de la pantalla "Resumen de la mañana" (ADR-018).

Pregunta: ¿`armar_resumen` clasifica bien cada parcela, calcula la barra de tiempo y el riego, y las consultas
de apoyo devuelven lo que dice la base?

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m dashboard.probar_datos

Los casos de `armar_resumen` usan datos armados a mano (no tocan la base). Los de las consultas de apoyo
leen la base de PRUEBA `agrosense_tests` (si está vacía, corré antes  python -m db.queries.probar_consultas).
No escribe nada.
"""

import logging
import sys
from datetime import date, datetime, timezone

logging.getLogger("streamlit.runtime.caching.cache_data_api").setLevel(logging.ERROR)     # sin los avisos de "no hay runtime" fuera de Streamlit

from dashboard import data                                  # noqa: E402
from db.conexion import obtener_base, preparar_consola       # noqa: E402
from db.queries import comun, resumen_manana as rm           # noqa: E402
from db.schemas.probar_esquemas import Resumen               # noqa: E402

FECHA = date(2026, 10, 5)
CONFIG = {"riesgo": {"margen_bajo_c": 2, "margen_alto_c": 0}}
CATALOGO = {
    "fincas": [{"_id": "F-A", "nombre": "Finca A", "departamento": "San Rafael"}],
    "parcelas": [{"_id": f"P-A-{i}", "finca_id": "F-A", "nombre": f"Cuartel {i}"} for i in (1, 2, 3, 4)],
    "nodos": [{"_id": "N-1"}, {"_id": "N-2"}],
}


def utc(dia: int, h: int, m: int = 0) -> datetime:
    return datetime(2026, 10, dia, h, m, tzinfo=timezone.utc)


def riesgo(parcela: str, margen: float) -> dict:
    return {"parcela_id": parcela, "etapa": "Brotación", "umbral_helada_c": -3.9, "minima_brote_c": -3.9 + margen,
            "margen_c": margen, "nivel": "alto", "agravantes": []}


def armar(riesgos, alertas=(), riegos=None, inactivos=(), ultima=None) -> dict:
    etapas = {r["parcela_id"]: {"etapa": "Brotación", "umbral_helada_c": -3.9} for r in riesgos}
    etapas["P-A-4"] = {"etapa": "Hojas desplegadas", "umbral_helada_c": None}     # sin umbral: no está en Q10
    return data.armar_resumen(FECHA, list(riesgos), etapas, list(alertas), riegos or {}, list(inactivos), ultima,
                              CATALOGO, CONFIG)


def cuadrado(x: float, y: float, lado: float = 0.0015) -> dict:
    anillo = [[x, y], [x + lado, y], [x + lado, y + lado], [x, y + lado], [x, y]]
    return {"type": "Polygon", "coordinates": [anillo]}


def probar_mapa(r: Resumen) -> None:
    """El mapa no se puede mover (arrastrar lo deformaba y sacaba los nodos) y muestra todo lo que tiene que mostrar."""
    from dashboard import mapa

    finca = {"_id": "F-A", "nombre": "Finca A"}
    catalogo = {
        "parcelas": [{"_id": "P-A-1", "finca_id": "F-A", "nombre": "Cuartel 1", "geometria": cuadrado(-68.33, -34.61)},
                     {"_id": "P-A-2", "finca_id": "F-A", "nombre": "Cuartel <2>", "geometria": cuadrado(-68.32, -34.61)},
                     {"_id": "P-B-1", "finca_id": "F-B", "nombre": "Otra", "geometria": cuadrado(-69.0, -33.0)}],
        "nodos": [{"_id": "N-A-1", "finca_id": "F-A", "ubicacion": {"type": "Point", "coordinates": [-68.3295, -34.6095]}},
                  {"_id": "N-A-2", "finca_id": "F-A", "ubicacion": {"type": "Point", "coordinates": [-68.3185, -34.6105]}},
                  {"_id": "N-B-1", "finca_id": "F-B", "ubicacion": {"type": "Point", "coordinates": [-69.0, -33.0]}}],
    }
    filas = [{"parcela_id": "P-A-1", "estado": "helada"}, {"parcela_id": "P-A-2", "estado": "normal"}]
    fig = mapa.figura_finca(finca, filas, catalogo, {"N-A-2"})
    lay = fig.layout

    r.chequear(lay.dragmode is False, "el mapa no tiene modo de arrastre ni de zoom")
    r.chequear(lay.xaxis.fixedrange is True and lay.yaxis.fixedrange is True, "los dos ejes tienen el rango bloqueado")
    r.chequear(mapa.CONFIG["scrollZoom"] is False and mapa.CONFIG["doubleClick"] is False
               and mapa.CONFIG["displayModeBar"] is False, "sin zoom con la rueda, sin doble clic y sin barra de herramientas")
    xs = [v for t in fig.data for v in t.x]
    ys = [v for t in fig.data for v in t.y]
    r.chequear(lay.xaxis.range[0] < min(xs) and max(xs) < lay.xaxis.range[1], "todos los puntos caen dentro del rango horizontal")
    r.chequear(lay.yaxis.range[0] < min(ys) and max(ys) < lay.yaxis.range[1], "todos los puntos caen dentro del rango vertical")
    nodos = [t for t in fig.data if t.mode == "markers"]
    r.chequear(sum(len(t.x) for t in nodos) == 2 and {t.name for t in nodos} == {"nodos que reportan", "nodos sin reportar"},
               "se dibujan los 2 nodos de la finca, separando los que no reportan")
    r.chequear(len([t for t in fig.data if t.fill == "toself"]) == 2, "se dibujan solo las 2 parcelas de esa finca")
    r.chequear(all("-33" not in str(t.y) for t in fig.data), "no se cuelan parcelas ni nodos de otra finca")
    r.chequear(len(fig.layout.annotations) == 2 and "&lt;2&gt;" in fig.layout.annotations[1].text,
               "cada parcela lleva su rótulo, con el texto escapado")
    r.chequear(abs(lay.yaxis.scaleratio - 1 / 0.8228) < 0.01, "la proporción corrige la latitud (1 / cos 34,6°)")
    r.chequear(mapa.rango([5.0, 5.0])[0] < 5.0 < mapa.rango([5.0, 5.0])[1], "un solo valor abre un rango mínimo")
    sin_parcelas = False
    try:
        mapa.figura_finca({"_id": "F-X"}, [], catalogo, set())
    except ValueError:
        sin_parcelas = True
    r.chequear(sin_parcelas, "una finca sin parcelas da un error claro")
    sin_filas = mapa.figura_finca(finca, [], catalogo, set())
    r.chequear(all(t.fillcolor == mapa.RELLENO["sin_umbral"] for t in sin_filas.data if t.fill == "toself"),
               "una parcela sin fila de estado se dibuja como 'sin umbral'")


def main() -> None:
    preparar_consola()
    r = Resumen()

    # ---- clasificación y orden
    res = armar([riesgo("P-A-1", 5.0), riesgo("P-A-2", -1.0), riesgo("P-A-3", 1.5)])
    estados = {f["parcela_id"]: f["estado"] for f in res["filas"]}
    r.chequear(estados == {"P-A-1": "normal", "P-A-2": "helada", "P-A-3": "atencion", "P-A-4": "sin_umbral"},
               "margen <= 0 es helada, <= 2 atención, mayor es normal; sin umbral no se evalúa")
    r.chequear([f["parcela_id"] for f in res["filas"]] == ["P-A-2", "P-A-3", "P-A-1", "P-A-4"],
               "orden: helada, atención, normal y sin umbral al final")
    r.chequear(armar([riesgo("P-A-1", 0.0)])["filas"][0]["estado"] == "helada", "margen exacto 0 cuenta como helada")

    # ---- barra de tiempo (la noche empieza a las 21:00Z y termina a las 15:00Z del 5/10: 18 h)
    alerta = {"parcela_id": "P-A-2", "inicio": utc(5, 6), "fin": utc(5, 9), "valor_extremo": -5.0}
    a = armar([riesgo("P-A-2", -1.0)], [alerta])["filas"][0]["alerta"]
    r.chequear(abs(a["horas"] - 3) < 1e-9 and not a["en_curso"], "una alerta de 06:00Z a 09:00Z dura 3 h y está cerrada")
    r.chequear(abs(a["desde"] - 9 / 18) < 1e-9 and abs(a["hasta"] - 12 / 18) < 1e-9,
               "la barra va del 50 % al 66,7 % de la noche")
    r.chequear(a["inicio"].hour == 3, "los horarios se muestran en hora de Argentina (UTC-3)")
    abierta = {**alerta, "fin": None}
    a = armar([riesgo("P-A-2", -1.0)], [abierta])["filas"][0]["alerta"]
    r.chequear(a["en_curso"] and abs(a["hasta"] - 1.0) < 1e-9 and abs(a["horas"] - 9) < 1e-9,
               "una alerta sin fin sigue en curso hasta el cierre de la noche")
    previa = {**alerta, "inicio": utc(4, 20), "fin": utc(4, 22)}
    a = armar([riesgo("P-A-2", -1.0)], [previa])["filas"][0]["alerta"]
    r.chequear(abs(a["horas"] - 1) < 1e-9 and a["desde"] == 0.0,
               "una alerta que empezó antes de las 18:00 se recorta al comienzo de la noche")
    dos = armar([riesgo("P-A-2", -1.0)], [alerta, {**alerta, "inicio": utc(5, 10), "fin": utc(5, 11), "valor_extremo": -7.0}])
    r.chequear(abs(dos["filas"][0]["alerta"]["horas"] - 1) < 1e-9, "con dos alertas en la noche vale la de mínima más extrema")

    # ---- riego
    riegos = {"P-A-1": {"inicio": utc(5, 11), "lamina_mm": 1.5, "parcela_id": "P-A-1"},
              "P-A-2": {"inicio": utc(1, 13), "lamina_mm": 76.0, "parcela_id": "P-A-2"}}
    filas = {f["parcela_id"]: f for f in armar([riesgo("P-A-1", 5), riesgo("P-A-2", -1), riesgo("P-A-3", 5)], riegos=riegos)["filas"]}
    r.chequear(filas["P-A-1"]["riego"]["estado"] == "esta_noche", "un riego dentro de la noche es 'esta_noche'")
    r.chequear(filas["P-A-2"]["riego"] == {"estado": "antes", "hace_dias": 4, "lamina_mm": 76.0, "inicio": datetime(2026, 10, 1, 10, 0)},
               "un riego anterior informa hace cuántos días fue (4 días antes del cierre)")
    r.chequear(filas["P-A-3"]["riego"]["estado"] == "nunca", "sin riegos registrados es 'nunca'")

    # ---- frescura de los datos
    res = armar([riesgo("P-A-1", 5)], ultima=utc(5, 14, 55))
    r.chequear(res["minutos_desde_ultima"] == 5, "los minutos desde la última lectura se miden contra el cierre")
    r.chequear(armar([riesgo("P-A-1", 5)])["ultima_lectura"] is None, "sin lecturas, la última lectura es None")

    # ---- mapa de la finca (ver dashboard/mapa.py): fijo, con todo dentro del cuadro
    probar_mapa(r)

    # ---- consultas de apoyo contra la base de prueba
    bd = obtener_base("agrosense_tests")
    if bd.alertas.count_documents({}) == 0:
        print("(la base de prueba está vacía: se omiten las consultas de apoyo)")
    else:
        al = rm.alertas_de_helada(bd, FECHA)
        r.chequear(sorted(x["parcela_id"] for x in al) == ["P-SR-1", "P-SR-2"], "la noche del 5/10 tiene alertas de P-SR-1 y P-SR-2")
        r.chequear(rm.alertas_de_helada(bd, date(2026, 10, 8)) == [], "una noche sin helada no devuelve alertas")
        r.chequear(rm.noches_con_helada(bd) == [date(2026, 9, 22), date(2026, 9, 29), date(2026, 10, 2),
                                                date(2026, 10, 5), date(2026, 10, 10)],
                   "las 5 mañanas con alerta de helada de la temporada")
        riegos_bd = rm.ultimo_riego(bd, FECHA)
        r.chequear(set(riegos_bd) == {"P-SR-1", "P-SR-2", "P-SM-1", "P-SM-2", "P-TU-1", "P-TU-2"},
                   "hay un último riego para cada una de las 6 parcelas")
        r.chequear(all(comun.a_utc(x["inicio"]) < comun.ventana_noche(FECHA)[1] for x in riegos_bd.values()),
                   "ningún riego empieza después del cierre de la noche")
        from dashboard import mapa
        cat = rm.catalogo(bd)
        for finca in cat["fincas"]:
            fig = mapa.figura_finca(finca, [], cat, set())
            n_nodos = sum(len(t.x) for t in fig.data if t.mode == "markers")
            fuera = [v for t in fig.data for v in t.x if not fig.layout.xaxis.range[0] < v < fig.layout.xaxis.range[1]]
            fuera += [v for t in fig.data for v in t.y if not fig.layout.yaxis.range[0] < v < fig.layout.yaxis.range[1]]
            r.chequear(n_nodos == 4 and not fuera, f"mapa real de {finca['_id']}: 4 nodos y todo dentro del cuadro")
        ahora = rm.ahora_de_la_noche(FECHA)
        r.chequear(rm.ultima_lectura(bd, ahora) == ahora, "la última lectura a las 12:00 es de las 12:00")
        r.chequear(rm.ultima_lectura(bd, datetime(2025, 1, 1, tzinfo=timezone.utc)) is None, "antes de la temporada no hay lecturas")

    print(f"\n{r.total - r.fallas} de {r.total} casos pasaron.")
    sys.exit(1 if r.fallas else 0)


if __name__ == "__main__":
    main()
