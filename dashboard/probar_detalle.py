"""Prueba de "Detalle de parcela" (ADR-019): los datos, los textos, los gráficos y las consultas de apoyo.

Pregunta: ¿`armar_detalle` arma bien la curva y el estado, los textos dicen lo que pasó, los gráficos no se pueden
mover y las consultas de apoyo devuelven lo que dice la base?

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m dashboard.probar_detalle

Los casos de `armar_detalle`, de los textos y de los gráficos usan datos armados a mano (no tocan la base). Los de las
consultas de apoyo leen la base de PRUEBA `agrosense_tests` (si está vacía, corré antes
python -m db.queries.probar_consultas). No escribe nada.
"""

import logging
import sys
from datetime import date, datetime, timedelta, timezone

logging.getLogger("streamlit.runtime.caching.cache_data_api").setLevel(logging.ERROR)

from dashboard import data, formato, graficos, piezas  # noqa: E402
from db.conexion import obtener_base, preparar_consola  # noqa: E402
from db.queries import comun, detalle_parcela as dp  # noqa: E402
from db.schemas.probar_esquemas import Resumen  # noqa: E402

FECHA = date(2026, 10, 5)
INICIO_UTC = datetime(2026, 10, 4, 21, 0, tzinfo=timezone.utc)  # 18:00 de Argentina
CATALOGO = {
    "fincas": [{"_id": "F-A", "nombre": "Finca A", "departamento": "San Rafael"}],
    "parcelas": [{"_id": "P-A-1", "finca_id": "F-A", "nombre": "Cuartel <1>"}],
    "nodos": [
        {"_id": "N-A", "parcela_id": "P-A-1", "estado": "activo"},
        {"_id": "N-B", "parcela_id": "P-A-1", "estado": "mantenimiento"},
        {"_id": "N-OTRO", "parcela_id": "P-X", "estado": "activo"},
    ],
}


def lectura(minutos: int, nodo: str, temperatura: float) -> dict:
    return {"ts": INICIO_UTC + timedelta(minutes=minutos), "nodo_id": nodo, "temperatura_c": temperatura}


def riesgo(margen: float = -1.0) -> dict:
    return {
        "parcela_id": "P-A-1",
        "etapa": "Brotación",
        "umbral_helada_c": -3.9,
        "minima_brote_c": -3.9 + margen,
        "margen_c": margen,
        "nivel": "alto",
        "agravantes": ["duracion"],
    }


def armar(curva=None, **cambios) -> dict:
    curva = [lectura(0, "N-A", 5.0), lectura(5, "N-A", 3.0), lectura(5, "N-B", 4.0)] if curva is None else curva
    args = dict(
        riesgo=riesgo(),
        etapa={"etapa": "Brotación"},
        horas_bajo_cero={"horas_bajo_cero": 3.5, "minima_c": -2.0},
        curva=curva,
        humedad=[],
        riegos=[],
        semanas=[],
        alertas=[],
        umbral_riego=19.2,
        delta_c=2.0,
    )
    args.update(cambios)
    return data.armar_detalle(
        FECHA,
        "P-A-1",
        CATALOGO,
        args["riesgo"],
        args["etapa"],
        args["horas_bajo_cero"],
        args["curva"],
        args["humedad"],
        args["riegos"],
        args["semanas"],
        args["alertas"],
        args["umbral_riego"],
        args["delta_c"],
    )


def main() -> None:
    preparar_consola()
    r = Resumen()

    # ---- formato
    r.chequear(
        formato.grados(-8.3) == "−8,3 °C" and formato.grados(None) == "-",
        "los grados llevan coma decimal y signo menos",
    )
    r.chequear(
        formato.numero(1520000) == "1.520.000" and formato.numero(76, 1) == "76,0",
        "los números llevan punto de miles y coma decimal",
    )
    r.chequear(
        formato.duracion(6.5833) == "6 h 35 min" and formato.duracion(0.25) == "15 min",
        "las duraciones se escriben en horas y minutos",
    )

    # ---- con_cortes
    t0 = datetime(2026, 10, 5, 0, 0)
    xs, ys = data.con_cortes([(t0, 1.0), (t0 + timedelta(minutes=5), 2.0), (t0 + timedelta(minutes=30), 3.0)])
    r.chequear(
        ys == [1.0, 2.0, None, 3.0] and xs[2] == xs[3], "un hueco de más de 10 minutos corta la línea con un None"
    )
    r.chequear(
        data.con_cortes([(t0, 1.0), (t0 + timedelta(minutes=10), 2.0)])[1] == [1.0, 2.0], "10 minutos justos no cortan"
    )
    r.chequear(data.con_cortes([]) == ([], []), "una serie vacía da listas vacías")

    # ---- armar_detalle
    d = armar()
    r.chequear(d["brote"]["y"] == [3.0, 1.0], "el brote es el nodo más frío de cada instante menos 2 °C")
    r.chequear(
        [n["nodo_id"] for n in d["nodos"]] == ["N-A", "N-B"], "solo se listan los nodos de la parcela (no los de otra)"
    )
    r.chequear(
        d["nodos"][1]["estado"] == "mantenimiento" and d["nodos"][0]["lecturas"] == 2,
        "cada nodo lleva su estado y cuántas lecturas tiene",
    )
    r.chequear(d["brote"]["x"][0].hour == 18, "las horas de la curva están en hora de Argentina")
    r.chequear(d["estado"] == "helada" and d["umbral_c"] == -3.9, "con margen negativo la parcela está en helada")
    sin = armar(riesgo=None)
    r.chequear(
        sin["estado"] == "sin_umbral" and sin["umbral_c"] is None and sin["nivel"] is None,
        "sin fila de Q10 la parcela queda 'sin umbral'",
    )
    vacia = armar(curva=[])
    r.chequear(
        not vacia["hay_curva"]
        and vacia["brote"] == {"x": [], "y": []}
        and all(n["lecturas"] == 0 for n in vacia["nodos"]),
        "sin lecturas no hay curva ni se rompe",
    )
    corte = armar(curva=[lectura(0, "N-A", 1.0), lectura(60, "N-A", 2.0)])
    r.chequear(
        None in corte["brote"]["y"] and None in corte["nodos"][0]["y"],
        "un corte de reporte se ve como corte en el brote y en el sensor",
    )
    alertas = [
        {
            "parcela_id": "P-A-1",
            "inicio": INICIO_UTC + timedelta(hours=6),
            "fin": INICIO_UTC + timedelta(hours=8),
            "valor_extremo": -4.0,
        },
        {"parcela_id": "P-A-1", "inicio": INICIO_UTC + timedelta(hours=9), "fin": None, "valor_extremo": -6.0},
    ]
    con_alerta = armar(alertas=alertas)
    r.chequear(
        con_alerta["alerta"]["en_curso"] and con_alerta["alerta"]["fin"] is None,
        "con dos alertas vale la de mínima más extrema",
    )
    r.chequear(
        armar(horas_bajo_cero=None)["horas_bajo_cero"] is None, "sin fila de Q1 las horas bajo 0 °C quedan vacías"
    )
    riegos = [
        {
            "inicio": INICIO_UTC + timedelta(hours=1),
            "fin": INICIO_UTC + timedelta(hours=3),
            "lamina_mm": 1.5,
            "litros": 300.0,
            "origen": "turno",
            "sistema": "goteo",
        }
    ]
    r.chequear(
        armar(riegos=riegos)["riegos"][0]["inicio"].hour == 19, "los riegos también se pasan a hora de Argentina"
    )

    # ---- textos (piezas)
    f, det = piezas.frase_de_la_parcela(con_alerta)
    r.chequear(
        "bajó a −4,9 °C en el brote" in f and "1,0 °C bajo su umbral" in f,
        "la frase dice cuánto bajó el brote y por cuánto superó el umbral",
    )
    r.chequear(
        "sigue abierta" in det and "Riesgo alto (larga duración)" in det and "No se regó" in det,
        "el detalle dice la alerta, el riesgo y que no se regó",
    )
    regada = armar(alertas=alertas, riegos=riegos)
    r.chequear(
        "Se regó durante la noche" in piezas.frase_de_la_parcela(regada)[1],
        "si hubo un riego dentro de la noche lo dice",
    )
    r.chequear(
        "No hay una alerta registrada" in piezas.frase_de_la_parcela(armar())[1], "una helada sin alerta lo aclara"
    )
    f_sin, det_sin = piezas.frase_de_la_parcela(sin)
    r.chequear(
        "no hay umbral de helada" in f_sin and "no se evalúa" in f_sin and "−2,0 °C" in det_sin,
        "sin umbral lo explica y muestra la mínima del sensor",
    )
    normal = armar(riesgo={**riesgo(8.0), "umbral_helada_c": -3.9, "minima_brote_c": 4.1, "agravantes": []})
    r.chequear(
        piezas.frase_de_la_parcela(normal)[0].startswith("Cuartel <1> no bajó de su umbral"),
        "una noche sin helada lo dice",
    )
    r.chequear("No hay lecturas" in piezas.frase_de_la_parcela(vacia)[0], "sin lecturas la frase lo dice")
    aviso = piezas.aviso_de_nodos(d)
    r.chequear(
        "N-B está en mantenimiento" in aviso
        and piezas.aviso_de_nodos(armar(curva=[lectura(0, "N-A", 1.0), lectura(0, "N-B", 1.0)])) != "",
        "un nodo en mantenimiento se avisa",
    )
    sin_lect = armar(curva=[lectura(0, "N-B", 1.0)])
    r.chequear(
        "N-A no tiene lecturas en la noche" in piezas.aviso_de_nodos(sin_lect), "un nodo activo sin lecturas se avisa"
    )
    r.chequear(
        "&lt;1&gt;" not in piezas.cifras(d) and "Alto" in piezas.cifras(d) and "3 h 30 min" in piezas.cifras(d),
        "las cifras muestran riesgo y horas bajo 0 °C",
    )
    r.chequear("Sin riegos registrados" in piezas.tabla_de_riegos(d), "sin riegos la tabla lo dice")
    tabla = piezas.tabla_de_riegos(armar(riegos=riegos))
    r.chequear(
        "1,5 mm" in tabla and "300 L" in tabla and "esta noche" in tabla and "Turno" in tabla,
        "la tabla de riegos muestra lámina, litros, origen y 'esta noche'",
    )
    sem = piezas.semanas(armar(semanas=[{"semana": INICIO_UTC, "litros": 1520000.0, "riegos": 1}]))
    r.chequear(
        "1.520.000 L" in sem and "semana del 4 de oct" in sem and piezas.semanas(d) == "",
        "los litros por semana se resumen en una línea",
    )
    hostil = armar()
    hostil["nodos"][0]["nodo_id"] = "<script>"
    hostil["nodos"][0]["estado"] = "baja"
    r.chequear(
        "<script>" not in piezas.aviso_de_nodos(hostil), "el texto que viene de la base se escapa en el aviso de nodos"
    )

    # ---- gráficos: fijos, con todo dentro del cuadro
    fig = graficos.figura_curva(con_alerta)
    lay = fig.layout
    r.chequear(
        lay.dragmode is False and lay.xaxis.fixedrange is True and lay.yaxis.fixedrange is True,
        "la curva no se puede mover ni hacer zoom",
    )
    r.chequear(
        lay.xaxis.range[0] == d["inicio"] and lay.xaxis.range[1] == d["ahora"],
        "el eje horizontal va de las 18:00 a las 12:00",
    )
    ys = [v for t in fig.data for v in t.y if v is not None]
    r.chequear(
        lay.yaxis.range[0] < min(ys + [-3.9]) and max(ys + [-3.9]) < lay.yaxis.range[1],
        "todos los valores y el umbral caen dentro del eje vertical",
    )
    r.chequear(
        len(lay.shapes) == 2 and any(s.y0 == -3.9 for s in lay.shapes),
        "hay una línea de umbral y la franja de la alerta",
    )
    r.chequear(
        not any(t.name == "Bajo el umbral" for t in fig.data), "si el brote nunca baja del umbral no hay tramo rojo"
    )
    fria = graficos.figura_curva(
        armar(curva=[lectura(0, "N-A", -2.0), lectura(5, "N-A", -8.0), lectura(10, "N-A", 3.0)])
    )
    rojo = next(t for t in fria.data if t.name == "Bajo el umbral")
    r.chequear(
        [v for v in rojo.y if v is not None] == [-4.0, -10.0],
        "el tramo bajo el umbral se repinta aparte y solo donde baja",
    )
    r.chequear(
        len({t.line.dash for t in fig.data if t.name.startswith("Sensor")}) == 2,
        "cada sensor tiene una raya distinta (no solo color)",
    )
    r.chequear(
        "en mantenimiento" in [t.name for t in fig.data if t.name.startswith("Sensor")][1],
        "el sensor en mantenimiento se rotula en la leyenda",
    )
    sin_fig = graficos.figura_curva(sin)
    r.chequear(
        not any(s.y0 is not None and s.type == "line" and s.y0 == s.y1 and s.yref == "y" for s in sin_fig.layout.shapes)
        and not any(t.name == "Bajo el umbral" for t in sin_fig.data),
        "sin umbral no se dibuja línea de umbral ni tramo rojo",
    )
    r.chequear(
        graficos.figura_curva(vacia).layout.yaxis.range[0] < graficos.figura_curva(vacia).layout.yaxis.range[1],
        "una curva vacía igual da un eje válido",
    )
    hum = armar(
        humedad=[
            {"hora": INICIO_UTC, "humedad_suelo_pct": 23.5},
            {"hora": INICIO_UTC + timedelta(hours=1), "humedad_suelo_pct": 12.0},
        ]
    )
    figh = graficos.figura_humedad(hum)
    yh = [v for t in figh.data for v in t.y]
    r.chequear(
        figh.layout.dragmode is False
        and figh.layout.yaxis.range[0] < min(yh + [19.2])
        and max(yh + [19.2]) < figh.layout.yaxis.range[1],
        "la humedad es fija y el eje incluye el umbral de riego",
    )
    r.chequear(
        graficos.figura_humedad(armar()).layout.yaxis.range[0] < 19.2, "sin humedad igual se dibuja el umbral de riego"
    )

    # ---- consultas de apoyo contra la base de prueba
    bd = obtener_base("agrosense_tests")
    if bd.alertas.count_documents({}) == 0:
        print("(la base de prueba está vacía: se omiten las consultas de apoyo)")
    else:
        curva = dp.curva_de_la_noche(bd, FECHA, "P-SR-1")
        r.chequear(
            len(curva) == 432 and {c["nodo_id"] for c in curva} == {"N-SR-1-A", "N-SR-1-B"},
            "la noche de una parcela tiene 216 lecturas por cada uno de sus 2 nodos",
        )
        inicio, fin = comun.ventana_noche(FECHA)
        r.chequear(
            all(inicio <= comun.a_utc(c["ts"]) < fin for c in curva),
            "todas las lecturas están dentro de la noche (18:00 a 12:00)",
        )
        r.chequear(all(a["ts"] <= b["ts"] for a, b in zip(curva, curva[1:])), "la curva viene ordenada por hora")
        riegos_bd = dp.riegos_recientes(bd, FECHA, "P-SR-1", 3)
        r.chequear(
            len(riegos_bd) == 3
            and riegos_bd[0]["inicio"] > riegos_bd[1]["inicio"]
            and all(comun.a_utc(x["inicio"]) < fin for x in riegos_bd),
            "los riegos recientes vienen del más nuevo al más viejo y antes del cierre de la noche",
        )
        r.chequear(dp.curva_de_la_noche(bd, FECHA, "P-NO-EXISTE") == [], "una parcela que no existe no da lecturas")
        real = data.detalle.__wrapped__(FECHA, "P-SR-1")
        r.chequear(
            real["estado"] == "helada" and real["minima_brote_c"] == -8.3 and real["horas_bajo_cero"] == 8.17,
            "P-SR-1 el 5/10: helada, −8,3 °C en el brote y 8,17 h bajo 0 °C",
        )
        r.chequear(
            len(real["humedad"]) == 24 and len(real["nodos"]) == 2 and real["alerta"] is not None,
            "P-SR-1 tiene 24 horas de humedad, 2 nodos y su alerta",
        )
        sm = data.detalle.__wrapped__(FECHA, "P-SM-1")
        r.chequear(sm["estado"] == "sin_umbral" and sm["alerta"] is None, "P-SM-1 el 5/10 no tiene umbral en su etapa")
        tu = data.detalle.__wrapped__(FECHA, "P-TU-2")
        r.chequear(any(n["estado"] == "mantenimiento" for n in tu["nodos"]), "P-TU-2 muestra su nodo en mantenimiento")
        for parcela in ("P-SR-1", "P-SR-2", "P-SM-1", "P-SM-2", "P-TU-1", "P-TU-2"):
            for dia in (date(2026, 9, 1), date(2026, 10, 5), date(2027, 3, 31)):
                dd = data.detalle.__wrapped__(dia, parcela)
                graficos.figura_curva(dd), graficos.figura_humedad(dd), piezas.frase_de_la_parcela(dd), piezas.cifras(
                    dd
                )
        r.chequear(
            True, "las 6 parcelas se arman sin errores en 3 fechas (inicio, noche precargada y fin de la temporada)"
        )

    print(f"\n{r.total - r.fallas} de {r.total} casos pasaron.")
    sys.exit(1 if r.fallas else 0)


if __name__ == "__main__":
    main()
