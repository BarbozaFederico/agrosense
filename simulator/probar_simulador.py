"""Prueba del simulador.

Pregunta: ¿la temporada simulada cumple lo decidido en ADR-012?

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m simulator.probar_simulador

Usa la base de PRUEBA `agrosense_tests` (carga el seed y genera la temporada ahí, dos veces).
No toca la base real `agrosense`. Tarda unos 2 minutos.

Tres partes:
    1. Reglas puras (sin base de datos): grados-día, detector de alertas, riesgo, curva de helada.
    2. El escenario (sin base de datos): clima, etapas y las 8 noches de helada.
    3. La base: lo que quedó guardado, y que cargar dos veces da lo mismo.
"""

import contextlib
import io
import math
import sys
import warnings
from datetime import date, datetime, timedelta, timezone

import numpy as np

from db.conexion import obtener_base, preparar_consola
from db.departamentos import clave_departamento
from db.queries.auditoria_lecturas import auditar
from db.schemas.probar_esquemas import Resumen
from db.seeds import cargar as cargar_seed
from simulator import alertas, calendario, clima, fenologia, generar, parametros as P
from simulator.alertas import Detector, nivel_riesgo
from simulator.escenario import ventana_noche_extrema

BASE_DE_PRUEBA = "agrosense_tests"
PASO_H = P.PASO_MIN / 60


def silencio(funcion, *args):
    """Corre una función ocultando lo que imprime (el seed y el cargador son muy verbosos)."""
    with contextlib.redirect_stdout(io.StringIO()):
        return funcion(*args)


# --------------------------------------------------------------------------- 1. reglas puras


def probar_reglas(r: Resumen, config: dict) -> None:
    print("--- 1. Reglas puras")
    # Grados-día (misma regla que Q9): (Tmáx + Tmín)/2, tope 32 °C, base 10 °C, nunca negativos
    gd = fenologia.grados_dia_diarios(np.array([30.0, 5.0, 40.0, 16.0]), np.array([10.0, 3.0, 26.0, 4.0]), 10, 32)
    r.chequear(
        gd.tolist() == [10.0, 0.0, 22.0, 0.0],
        f"grados-día | día templado, día frío, día con tope de 32 °C y día justo en la base | {gd.tolist()}",
    )

    # Detector de alertas con histéresis
    def eventos(valores, cierre):
        d, salida = Detector(cierre), []
        for i, v in enumerate(valores):
            e = d.paso(i, v, 0.0)
            if e:
                salida.append((i, e))
        return salida

    r.chequear(
        eventos([5, 5, -1, -1, 0, 2, 2, 2, 2], 3) == [(2, "abre"), (6, "cierra")],
        "detector | abre al cruzar y cierra tras 3 lecturas seguidas por encima",
    )
    r.chequear(
        eventos([-1, 1, -1, 1, 1, 1], 3) == [(0, "abre"), (5, "cierra")],
        "detector | con el valor oscilando alrededor del umbral queda una sola alerta",
    )
    r.chequear(
        eventos([5, float("nan"), -1, float("nan"), 3], 1) == [(2, "abre"), (4, "cierra")],
        "detector | las lecturas faltantes (NaN) no cambian nada",
    )

    # Índice de riesgo (ADR-005)
    riesgo = config["riesgo"]
    casos = [
        (-0.4, [], "alto"),
        (1.3, [], "medio"),
        (2.6, [], "bajo"),
        (2.6, ["aire_seco"], "medio"),
        (2.6, ["duracion", "aire_seco"], "alto"),
        (1.3, ["duracion"], "alto"),
        (2.6, ["suelo_seco"], "medio"),
        (1.3, ["suelo_seco"], "medio"),
    ]
    mal = [
        (m, a, esperado, nivel_riesgo(m, a, riesgo))
        for m, a, esperado in casos
        if nivel_riesgo(m, a, riesgo) != esperado
    ]
    r.chequear(
        not mal,
        f"riesgo | {len(casos)} casos de margen y agravantes dan el nivel esperado"
        + (f" (fallan: {mal})" if mal else ""),
    )

    # Astronomía
    sr, ss = clima.astronomia("F-SR")
    r.chequear(
        6.8 <= sr[22] <= 7.7 and 6.8 <= sr[35] <= 7.4 and sr[35] < sr[22],
        f"astronomía | amanecer de San Rafael: {sr[22]:.2f} h el 22/9 y {sr[35]:.2f} h el 5/10",
    )

    # Curva de una noche de helada, sin ruido
    tmax, tmin = np.full(P.DIAS, 18.0), np.full(P.DIAS, 8.0)
    base = clima.perfil_5min(tmax, tmin, sr, ss)
    for objetivo, extrema in ((-1.5, False), (-2.8, False), (-4.5, False), (-6.3, True)):
        dia = 20
        t_puesta = float(clima.temperatura_en_puesta(tmax[dia - 1], tmin[dia - 1], sr[dia], ss[dia]))
        curva = clima.noche_de_helada(
            base, dia, objetivo + P.DESVIO_TEMPERATURA_C, t_puesta, sr, ss, extrema, P.DESVIO_TEMPERATURA_C
        )
        # se mide desde media hora después de las primeras 2 h: la ventana de 1 h no tiene que
        # incluir minutos del tramo rápido
        primero = int((ss[dia] + P.PRIMERAS_HORAS + 0.5) / PASO_H) + (dia - 1) * P.PASOS_DIA
        amanecer_paso = int(sr[dia + 1] / PASO_H) + dia * P.PASOS_DIA
        tramo = curva[primero:amanecer_paso]
        por_hora = -(tramo[12:] - tramo[:-12])  # °C perdidos en 1 h
        frio = curva[(dia - 1) * P.PASOS_DIA + 15 * 12 : amanecer_paso + 1] - P.DESVIO_TEMPERATURA_C
        horas = float((frio < 0).sum() * PASO_H)
        esperado = (
            P.HORAS_BAJO_CERO_EXTREMA
            if extrema
            else float(
                min(P.HORAS_BAJO_CERO_MAX, max(P.HORAS_BAJO_CERO_MIN, abs(objetivo) / P.VELOCIDAD_MAX_ENFRIAMIENTO))
            )
        )
        r.chequear(
            por_hora.max() <= P.VELOCIDAD_MAX_ENFRIAMIENTO + 0.02
            and abs(horas - esperado) <= 0.3
            and abs(float(frio.min()) - objetivo) <= 0.1,
            f"curva de helada | mínima {objetivo:>5} °C{' (extrema)' if extrema else ''}: enfría como máximo "
            f"{por_hora.max():.2f} °C/h tras las primeras 2 h, {horas:.1f} h bajo cero (diseño {esperado:.1f}), "
            f"mínima {frio.min():.2f} °C al amanecer",
        )


# --------------------------------------------------------------------------- 2. el escenario


def horas_de(paso: int) -> float:
    return (paso % P.PASOS_DIA) * PASO_H


def probar_escenario(r: Resumen, contexto: generar.Contexto) -> generar.Temporada:
    print("--- 2. Escenario (clima, etapas y las 8 noches de helada)")
    temporada = silencio(generar.simular, contexto)
    esc, config, variedad = temporada.escenario, contexto.config, contexto.variedad
    etapas = variedad["etapas"]
    fechas = clima.fechas()
    meses = clima.meses()

    # Determinismo: la misma semilla da exactamente lo mismo
    otra = silencio(generar.simular, contexto)
    igual = temporada.resumen == otra.resumen and all(
        np.array_equal(esc.nodos[n].temperatura, otra.escenario.nodos[n].temperatura, equal_nan=True) for n in esc.nodos
    )
    r.chequear(igual, f"determinismo | dos simulaciones con la semilla {P.SEMILLA} dan las mismas lecturas y conteos")

    # Clima: promedios mensuales contra las normales
    peor = 0.0
    for pid in ("P-SR-1", "P-SM-1", "P-TU-1"):
        parcela = esc.parcelas[pid]
        t = esc.nodos[parcela.nodos[0]].temperatura.reshape(P.DIAS, P.PASOS_DIA)
        for m in P.MESES_TEMPORADA:
            sel = meses == m
            for valor, normal in (
                (np.nanmax(t, axis=1)[sel].mean(), P.NORMALES_C[parcela.finca_id][m][0]),
                (np.nanmin(t, axis=1)[sel].mean(), P.NORMALES_C[parcela.finca_id][m][1]),
            ):
                peor = max(peor, abs(valor - normal))
    r.chequear(
        peor <= 2.0,
        f"clima | máxima y mínima mensuales a ±{peor:.1f} °C como máximo de las normales del SMN/DACC "
        f"(tolerancia 2 °C: la variación diaria es de ~2 °C)",
    )

    # Etapas: brotación aproximada por finca y requisito de la noche extrema
    brotacion = {}
    for pid in ("P-SR-1", "P-SM-1", "P-TU-1"):
        brotacion[pid] = fechas[fenologia.dia_de_brotacion(esc.parcelas[pid].gd_diarios, variedad)]
    r.chequear(
        date(2026, 9, 14) <= brotacion["P-SM-1"] <= date(2026, 9, 24)
        and date(2026, 9, 20) <= brotacion["P-SR-1"] <= date(2026, 10, 2)
        and date(2026, 9, 28) <= brotacion["P-TU-1"] <= date(2026, 10, 8),
        "etapas | brotación estimada: San Martín {}, San Rafael {}, Tupungato {}".format(
            *(brotacion[p].strftime("%d/%m") for p in ("P-SM-1", "P-SR-1", "P-TU-1"))
        ),
    )
    extrema = next(n for n in esc.noches if n.extrema)
    for pid in ("P-SR-1", "P-SR-2"):
        e = etapas[esc.parcelas[pid].etapa[extrema.dia]]
        r.chequear(
            e["bbch_desde"] >= 7,
            f"noche extrema | {pid} está en BBCH {e['bbch_desde']} ({e['nombre']}) el {extrema.fecha:%d/%m} (>= 7)",
        )

    # Las 8 noches: resultado buscado, medido con las lecturas del nodo más frío
    delta = config["delta_brote_c"]
    cuenta = {"alerta": 0, "medio": 0, "bajo": 0}
    r.chequear(
        len(esc.noches) == 8,
        f"noches | {len(esc.noches)} noches de helada (esperado 8: San Rafael 3, San Martín 2, Tupungato 3)",
    )
    for n in sorted(esc.noches, key=lambda n: n.fecha):
        margenes, horas_min, horas_cero, minima_real = [], [], [], []
        for pid in (f"P-{n.finca_id[2:]}-1", f"P-{n.finca_id[2:]}-2"):
            parcela = esc.parcelas[pid]
            frio = np.fmin(*(esc.nodos[x].temperatura for x in parcela.nodos))
            desde, hasta = (n.dia - 1) * P.PASOS_DIA + 18 * 12, n.dia * P.PASOS_DIA + 12 * 12
            v = frio[desde:hasta]
            imin = int(np.nanargmin(v))
            horas_min.append(horas_de(desde + imin))
            amanecer_paso = n.dia * P.PASOS_DIA + int(clima.astronomia(n.finca_id)[0][n.dia + 1] / PASO_H)
            horas_cero.append(
                float((v[: amanecer_paso - desde] < 0).sum() * PASO_H)
            )  # horas bajo cero hasta el amanecer
            minima_real.append(float(np.nanmin(v)))
            umbral = etapas[parcela.etapa[n.dia]]["umbral_helada_c"]
            margenes.append(None if umbral is None else float(np.nanmin(v)) - delta - umbral)
        if n.resultado in ("alerta", "extrema"):
            ok_resultado = all(m is not None and m < 0 for m in margenes)
            cuenta["alerta"] += ok_resultado
        elif n.resultado == "medio":
            ok_resultado = all(m is not None and 0 < m <= 2 for m in margenes)
            cuenta["medio"] += ok_resultado
        else:
            ok_resultado = all(m is None or m > 2 for m in margenes)
            cuenta["bajo"] += ok_resultado
        profunda = abs(n.minima_c) >= 2
        ok_hora = all((6.0 if profunda else 4.5) <= h <= 8.0 for h in horas_min)
        limites_horas = (6.5, 8.5) if n.extrema else (2.5, 6.0)
        ok_horas = all(limites_horas[0] <= h <= limites_horas[1] for h in horas_cero)
        r.chequear(
            ok_resultado and ok_hora and ok_horas,
            f"noche | {n.finca_id} {n.fecha:%d/%m} {n.resultado:<8} mínima {min(minima_real):>5.2f} °C a las "
            f"{np.mean(horas_min):.1f} h, {np.mean(horas_cero):.1f} h bajo cero, margen del brote "
            f"{', '.join('-' if m is None else f'{m:+.2f}' for m in margenes)} ({n.etapa})",
        )
    r.chequear(
        cuenta == {"alerta": 5, "medio": 2, "bajo": 1},
        f"noches | 5 cruzan el umbral, 2 quedan en riesgo medio y 1 en bajo: {cuenta}",
    )

    # Fuera de esas noches no hay heladas ni lecturas más frías que el límite del departamento
    for finca_id in ("F-SR", "F-SM", "F-TU"):
        dias_frios = set()
        for pid, parcela in esc.parcelas.items():
            if parcela.finca_id != finca_id:
                continue
            for nodo_id in parcela.nodos:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)  # nodo sin lecturas todo un día
                    minimos = np.nanmin(esc.nodos[nodo_id].temperatura.reshape(P.DIAS, P.PASOS_DIA), axis=1)
                dias_frios |= {fechas[d] for d in np.nonzero(minimos < 0)[0]}
        designados = {n.fecha for n in esc.noches if n.finca_id == finca_id}
        # la noche extrema empieza a enfriarse antes de medianoche: el día anterior también marca bajo cero
        dias_frios = {d for d in dias_frios if d + timedelta(days=1) not in designados}
        r.chequear(
            dias_frios == designados,
            f"heladas | {finca_id}: días con temperatura bajo cero {sorted(d.strftime('%d/%m') for d in dias_frios)} "
            f"= las noches designadas",
        )
    primero, ultimo = ventana_noche_extrema(config)
    for finca in contexto.fincas:
        limite = config["sospechoso_minimo_c"][clave_departamento(finca["departamento"])]
        minimo = min(
            float(np.nanmin(esc.nodos[n].temperatura)) for n in esc.nodos if esc.nodos[n].finca_id == finca["_id"]
        )
        if finca["_id"] == config["noche_extrema"]["finca_id"]:
            fuera = [
                np.nanmin(np.concatenate([esc.nodos[n].temperatura[:primero], esc.nodos[n].temperatura[ultimo + 1 :]]))
                for n in esc.nodos
                if esc.nodos[n].finca_id == finca["_id"]
            ]
            r.chequear(
                min(fuera) >= limite and abs(minimo - config["noche_extrema"]["minimo_c"]) < 1e-9,
                f"límite | {finca['_id']}: fuera de la ventana extrema no baja de {limite} °C ({min(fuera):.2f}) y el piso es {minimo:.2f} °C",
            )
        else:
            r.chequear(
                minimo >= limite, f"límite | {finca['_id']}: mínima {minimo:.2f} °C, no más fría que {limite} °C"
            )

    # Humedades
    sueloMin = min(float(h.min()) for h in temporada.humedad_suelo.values())
    sueloMax = max(float(h.max()) for h in temporada.humedad_suelo.values())
    aire = [esc.nodos[n].humedad_aire for n in esc.nodos]
    r.chequear(
        P.HUMEDAD_SUELO_MINIMA <= sueloMin
        and sueloMax <= 26
        and 0 <= min(float(np.nanmin(a)) for a in aire)
        and max(float(np.nanmax(a)) for a in aire) <= 100,
        f"humedades | suelo entre {sueloMin:.1f} y {sueloMax:.1f} %, aire entre "
        f"{min(float(np.nanmin(a)) for a in aire):.0f} y {max(float(np.nanmax(a)) for a in aire):.0f} %",
    )
    return temporada


# --------------------------------------------------------------------------- 3. la base


def grados_dia_desde_la_base(bd, parcela_id: str, variedad: dict) -> tuple[np.ndarray, np.ndarray]:
    """Recalcula grados-día y etapa de una parcela con una consulta a `lecturas` (lo que hará Q9)."""
    filas = bd.lecturas.aggregate(
        [
            {"$match": {"meta.parcela_id": parcela_id}},
            {
                "$group": {
                    "_id": {
                        "nodo": "$meta.nodo_id",
                        "dia": {"$dateTrunc": {"date": "$ts", "unit": "day", "timezone": "-03:00"}},
                    },
                    "max": {"$max": "$temperatura_c"},
                    "min": {"$min": "$temperatura_c"},
                }
            },
        ]
    )
    maximos, minimos = {}, {}
    for fila in filas:
        dia = (
            fila["_id"]["dia"].replace(tzinfo=None)
            + timedelta(hours=P.UTC_ARGENTINA_H)
            - datetime(P.INICIO.year, P.INICIO.month, P.INICIO.day)
        ).days
        maximos.setdefault(dia, []).append(fila["max"])
        minimos.setdefault(dia, []).append(fila["min"])
    tmax = np.array([np.mean(maximos[d]) for d in range(P.DIAS)])
    tmin = np.array([np.mean(minimos[d]) for d in range(P.DIAS)])
    gd = fenologia.grados_dia_diarios(tmax, tmin, variedad["grados_dia"]["base_c"], variedad["grados_dia"]["tope_c"])
    return gd, fenologia.etapa_de_cada_dia(gd, variedad)


def probar_base(r: Resumen, bd, contexto: generar.Contexto, temporada: generar.Temporada) -> None:
    print("--- 3. Base de datos (agrosense_tests)")
    esc, config, variedad = temporada.escenario, contexto.config, contexto.variedad
    resumen = temporada.resumen

    lecturas = bd.lecturas.count_documents({})
    r.chequear(
        lecturas == resumen["lecturas"] and lecturas > 700_000,
        f"lecturas | {lecturas} guardadas = {resumen['lecturas']} simuladas (12 nodos x 61.056 menos los cortes de reporte)",
    )
    a = auditar(bd)
    r.chequear(
        a["aprobada"] and a["mal_formadas"] == 0 and a["inesperadas"] == 0,
        f"auditoría | mal formadas {a['mal_formadas']}, sospechosas inesperadas {a['inesperadas']} (esperado: 0 y 0)",
    )
    r.chequear(
        a["esperadas"] > 0 and a["minima_esperada"] == config["noche_extrema"]["minimo_c"],
        f"auditoría | {a['esperadas']} lecturas sospechosas esperadas (noche extrema), la más fría {a['minima_esperada']} °C",
    )
    r.chequear(
        not a["sin_limite"], f"auditoría | todas las fincas tienen límite de sospechoso (sin límite: {a['sin_limite']})"
    )

    # Heladas
    heladas = list(bd.alertas.find({"tipo": "helada"}))
    por_noche = sorted({(h["parcela_id"][2:4], h["inicio"].date()) for h in heladas})
    r.chequear(
        len(heladas) == 10 and all(h["estado"] == "cerrada" and h["riesgo"]["nivel"] == "alto" for h in heladas),
        f"alertas de helada | {len(heladas)} (5 noches x 2 parcelas), todas cerradas y con riesgo alto",
    )
    r.chequear(
        all(h["inicio"] < h["fin"] and h["valor_extremo"] < h["umbral"] for h in heladas),
        "alertas de helada | cada una empieza antes de cerrar y su mínima del brote está bajo el umbral",
    )
    sr = [h for h in heladas if h["parcela_id"] == "P-SR-1" and h["inicio"].month == 10 and h["inicio"].day == 5]
    r.chequear(
        len(sr) == 1
        and abs(sr[0]["valor_extremo"] - (config["noche_extrema"]["minimo_c"] - config["delta_brote_c"])) < 0.01,
        f"alertas de helada | la noche extrema de P-SR-1 llega a {sr[0]['valor_extremo'] if sr else None} °C en el brote "
        f"(piso {config['noche_extrema']['minimo_c']} − Δ {config['delta_brote_c']})",
    )

    # Riego
    por_parcela = {pid: bd.alertas.count_documents({"tipo": "riego", "parcela_id": pid}) for pid in esc.parcelas}
    surco = [v for pid, v in por_parcela.items() if esc.parcelas[pid].sistema_riego == "surco"]
    goteo = [v for pid, v in por_parcela.items() if esc.parcelas[pid].sistema_riego == "goteo"]
    r.chequear(
        all(3 <= v <= 8 for v in surco) and all(1 <= v <= 6 for v in goteo),
        f"alertas de riego | por parcela: {por_parcela} (surco entre 3 y 8, goteo entre 1 y 6)",
    )
    ok_extras = True
    for extra in bd.riegos.find({"origen": "alerta"}):
        alerta = bd.alertas.find_one({"_id": extra["alerta_id"], "tipo": "riego", "parcela_id": extra["parcela_id"]})
        ok_extras &= alerta is not None and extra["inicio"] - alerta["inicio"] >= timedelta(hours=P.DEMORA_EXTRA_H)
    n_extra = bd.riegos.count_documents({"origen": "alerta"})
    r.chequear(
        ok_extras and n_extra > 0,
        f"riegos | los {n_extra} riegos extra apuntan a una alerta de riego de su parcela y empiezan 3 h o más después",
    )
    r.chequear(
        bd.riegos.count_documents({"$expr": {"$ne": ["$litros", {"$multiply": ["$lamina_mm", 2, 10000]}]}}) == 0,
        "riegos | litros = lámina (mm) x 2 ha x 10.000 en todos",
    )
    turnos_surco = sorted(x["inicio"] for x in bd.riegos.find({"parcela_id": "P-SR-1", "origen": "turno"}))
    r.chequear(
        len(turnos_surco) >= 30
        and all(b - a == timedelta(days=7) for a, b in zip(turnos_surco, turnos_surco[1:]))
        and bd.riegos.count_documents({"parcela_id": "P-SR-1", "origen": "turno", "lamina_mm": 76})
        == len(turnos_surco),
        f"riegos | P-SR-1: {len(turnos_surco)} turnos de 76 mm, uno cada 7 días",
    )
    r.chequear(
        bd.riegos.count_documents({"parcela_id": "P-TU-1", "origen": "turno"}) == P.DIAS,
        f"riegos | P-TU-1 (goteo): {bd.riegos.count_documents({'parcela_id': 'P-TU-1', 'origen': 'turno'})} riegos diarios (esperado {P.DIAS})",
    )

    # Nodos
    nodo = bd.nodos.find_one({"_id": calendario.NODO_EN_MANTENIMIENTO})
    ultima = next(bd.lecturas.find({"meta.nodo_id": calendario.NODO_EN_MANTENIMIENTO}).sort("ts", -1).limit(1))
    desde = calendario.MANTENIMIENTO_DESDE - timedelta(hours=P.UTC_ARGENTINA_H)
    r.chequear(
        nodo["estado"] == "mantenimiento" and ultima["ts"].replace(tzinfo=None) < desde,
        f"nodos | {nodo['_id']} en mantenimiento, su última lectura es del {ultima['ts']:%d/%m %H:%M} UTC",
    )
    nodo_id, inicio, horas = calendario.CORTES_NODOS[0]
    desde_utc = inicio - timedelta(hours=P.UTC_ARGENTINA_H)
    en_corte = bd.lecturas.count_documents(
        {"meta.nodo_id": nodo_id, "ts": {"$gte": desde_utc, "$lt": desde_utc + timedelta(hours=horas)}}
    )
    r.chequear(
        en_corte == 0,
        f"nodos | {nodo_id} no tiene lecturas durante su corte de {horas} h del {inicio:%d/%m} ({en_corte} encontradas)",
    )

    # Observaciones
    obs = list(bd.observaciones_fenologicas.find())
    etapas = variedad["etapas"]
    difieren = 0
    for o in obs:
        parcela = esc.parcelas[o["parcela_id"]]
        dia = clima.indice_dia((o["fecha"].replace(tzinfo=None) + timedelta(hours=P.UTC_ARGENTINA_H)).date())
        difieren += o["etapa_bbch"] != etapas[parcela.etapa[dia]]["bbch_desde"]
    r.chequear(
        len(obs) == 42 and difieren == 2 and {o["observador"] for o in obs} == {"tecnico", "encargado"},
        f"observaciones | {len(obs)} (una por parcela por mes), {difieren} difieren de la etapa estimada (esperado 2)",
    )

    # Cruce con la base: la etapa que se calcularía con una consulta a `lecturas` (como Q9)
    for pid in ("P-SR-1", "P-SM-2", "P-TU-1"):
        gd, etapa = grados_dia_desde_la_base(bd, pid, variedad)
        propios = esc.parcelas[pid]
        iguales = int((etapa == propios.etapa).sum())
        r.chequear(
            np.abs(gd - propios.gd_diarios).max() < 0.02 and iguales == P.DIAS,
            f"cruce con la base | {pid}: grados-día y etapa recalculados desde `lecturas` coinciden "
            f"(diferencia máxima {np.abs(gd - propios.gd_diarios).max():.3f} GD, etapa igual {iguales}/{P.DIAS} días)",
        )

    # Repetible: una segunda carga deja exactamente lo mismo
    suma_antes = next(
        bd.lecturas.aggregate([{"$group": {"_id": None, "t": {"$sum": "$temperatura_c"}, "n": {"$sum": 1}}}])
    )
    ids_antes = sorted(x["_id"] for x in bd.alertas.find({}, {"_id": 1}))
    silencio(generar.escribir, bd, generar.simular(contexto))
    suma_despues = next(
        bd.lecturas.aggregate([{"$group": {"_id": None, "t": {"$sum": "$temperatura_c"}, "n": {"$sum": 1}}}])
    )
    ids_despues = sorted(x["_id"] for x in bd.alertas.find({}, {"_id": 1}))
    r.chequear(
        suma_antes["n"] == suma_despues["n"]
        and math.isclose(suma_antes["t"], suma_despues["t"], rel_tol=1e-9)
        and ids_antes == ids_despues,
        f"repetible | la segunda carga deja {suma_despues['n']} lecturas, la misma suma de temperaturas y las mismas alertas",
    )


def main() -> None:
    preparar_consola()
    r = Resumen()
    bd = obtener_base(BASE_DE_PRUEBA)
    print(f"Base de prueba: {bd.name} (el seed y la temporada se cargan acá; la base real no se toca)")
    contexto_seed = generar.contexto_desde_seed()
    probar_reglas(r, contexto_seed.config)
    temporada = probar_escenario(r, contexto_seed)
    silencio(cargar_seed.cargar, bd)
    contexto = generar.cargar_contexto(bd)
    silencio(generar.escribir, bd, generar.simular(contexto))
    probar_base(r, bd, contexto, temporada)
    print("---")
    print(
        f"RESULTADO: todos los casos dieron lo esperado ({r.total} casos)"
        if r.fallas == 0
        else f"RESULTADO: {r.fallas} de {r.total} casos NO dieron lo esperado"
    )
    if r.fallas:
        sys.exit(1)


if __name__ == "__main__":
    main()
