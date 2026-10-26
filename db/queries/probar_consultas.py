"""Prueba de las consultas Q1 a Q10.

Pregunta: ¿cada consulta devuelve lo correcto sobre los datos simulados?

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m db.queries.probar_consultas

Usa la base de PRUEBA `agrosense_tests` (carga el seed, genera la temporada y crea los índices
geoespaciales ahí). No toca la base real `agrosense`. Tarda un minuto.

Cómo se verifica: cada consulta se compara con un cálculo INDEPENDIENTE hecho en Python con `find`
(sin usar `aggregate`), con el escenario del simulador o con la colección `alertas`. Si la consulta y el
cálculo aparte coinciden, lo más probable es que ambos estén bien. Además se comprueba que el texto
de mongosh de tres consultas (Q1, Q4 y Q7) devuelva lo mismo que Python, para que el panel
"Ver consulta" del dashboard no mienta.
"""

import contextlib
import io
import json
import math
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from db.conexion import obtener_base, preparar_consola
from db.indexes.crear_indices import crear_indices
from db.queries import (
    comun,
    q1_horas_bajo_cero,
    q2_minima_bajo_umbral,
    q3_nodos_cercanos,
    q4_parcelas_en_evento,
    q5_nodos_sin_reportar,
    q6_humedad_suelo_horaria,
    q7_litros_por_semana,
    q8_heladas_por_departamento,
    q9_etapa_por_grados_dia,
    q10_riesgo_de_helada,
)
from db.schemas.probar_esquemas import Resumen
from db.seeds import cargar as cargar_seed
from simulator import generar

BASE_DE_PRUEBA = "agrosense_tests"
PASO_H = 5 / 60


def silencio(funcion, *args):
    with contextlib.redirect_stdout(io.StringIO()):
        return funcion(*args)


def cronometrar(funcion, *args, **kwargs):
    """(resultado, segundos)"""
    t = time.perf_counter()
    resultado = funcion(*args, **kwargs)
    return resultado, time.perf_counter() - t


def lecturas_de(bd, parcela_id: str, inicio: datetime, fin: datetime) -> list[dict]:
    return list(bd.lecturas.find({"meta.parcela_id": parcela_id, "ts": {"$gte": inicio, "$lt": fin}}))


def lunes_de(momento_utc: datetime) -> date:
    """Lunes de la semana (hora de Argentina) del instante."""
    local = comun.a_hora_local(momento_utc).date()
    return local - timedelta(days=local.weekday())


def semana(valor: datetime) -> date:
    return comun.a_hora_local(valor).date()


# --------------------------------------------------------------------------- las pruebas


def probar_q9(r, bd, temporada, etapas):
    filas, seg = cronometrar(q9_etapa_por_grados_dia.consultar, bd, comun.FIN_TEMPORADA, None, True)
    esc = temporada.escenario
    dif_gd, malas = 0.0, 0
    for f in filas:
        parcela, dia = esc.parcelas[f["parcela_id"]], (semana(f["fecha"]) - date(2026, 9, 1)).days
        dif_gd = max(dif_gd, abs(f["gd_dia"] - parcela.gd_diarios[dia]))
        malas += f["bbch_estimada"] != etapas[parcela.etapa[dia]]["bbch_desde"]
    r.chequear(
        len(filas) == 6 * 212 and malas == 0 and dif_gd < 0.02,
        f"Q9 | {len(filas)} filas (6 parcelas x 212 días): etapa estimada igual a la del simulador en todas "
        f"({malas} distintas), grados-día a {dif_gd:.3f} GD ({seg:.1f} s)",
    )
    antes = q9_etapa_por_grados_dia.consultar(bd, date(2026, 9, 10), "P-SR-1")[0]
    r.chequear(
        antes["bbch_observada"] is None and antes["bbch"] == antes["bbch_estimada"],
        "Q9 | el 10/9 aún no hay observaciones: la etapa efectiva es la estimada",
    )
    con_obs = q9_etapa_por_grados_dia.consultar(bd, date(2026, 10, 15), "P-SR-1")[0]
    r.chequear(
        con_obs["bbch_observada"] == 53 and con_obs["bbch_estimada"] == 16 and con_obs["bbch"] == 53,
        f"Q9 | el 15/10 P-SR-1 tiene observación (BBCH {con_obs['bbch_observada']}) distinta de la estimada "
        f"({con_obs['bbch_estimada']}): manda la observación (RF-18)",
    )


def probar_q1_q2_q10(r, bd, temporada, config):
    noches = sorted(temporada.escenario.noches, key=lambda n: n.fecha)
    alertas = list(bd.alertas.find({"tipo": "helada"}))
    delta = config["delta_brote_c"]
    for n in noches:
        inicio, fin = comun.ventana_noche(n.fecha)
        esperadas = {a["parcela_id"] for a in alertas if inicio <= a["inicio"].replace(tzinfo=timezone.utc) < fin}

        # Q1: horas bajo cero = lecturas (instantes) con el nodo más frío bajo cero x 5 minutos
        horas, maxdif = {}, 0.0
        filas, seg = cronometrar(q1_horas_bajo_cero.consultar, bd, n.fecha)
        for fila in filas:
            por_instante = defaultdict(list)
            for d in lecturas_de(bd, fila["parcela_id"], inicio, fin):
                por_instante[d["ts"]].append(d["temperatura_c"])
            propias = sum(1 for t in por_instante.values() if min(t) < 0) * PASO_H
            maxdif = max(maxdif, abs(fila["horas_bajo_cero"] - propias))
            horas[fila["parcela_id"]] = fila["horas_bajo_cero"]
        r.chequear(
            len(filas) == 6 and maxdif < 0.01,
            f"Q1 | {n.finca_id} {n.fecha:%d/%m}: horas bajo cero iguales a un conteo aparte (diferencia {maxdif:.3f} h); "
            f"{', '.join(f'{p} {h:.2f}' for p, h in sorted(horas.items()) if h > 0) or 'ninguna'} ({seg:.1f} s)",
        )

        # Q2: las parcelas que devuelve son las que abrieron alerta de helada esa noche
        q2 = {f["parcela_id"] for f in q2_minima_bajo_umbral.consultar(bd, n.fecha)}
        r.chequear(
            q2 == esperadas,
            f"Q2 | {n.finca_id} {n.fecha:%d/%m} ({n.resultado}): {sorted(q2) or 'ninguna'} = parcelas con alerta {sorted(esperadas) or 'ninguna'}",
        )

        # Q10: nivel y margen
        q10 = {f["parcela_id"]: f for f in q10_riesgo_de_helada.consultar(bd, n.fecha)}
        propias_finca = [p for p in q10 if p.startswith(f"P-{n.finca_id[2:]}")]
        if esperadas:
            ok = all(q10[p]["nivel"] == "alto" for p in esperadas)
            for a in (
                a
                for a in alertas
                if a["parcela_id"] in esperadas and inicio <= a["inicio"].replace(tzinfo=timezone.utc) < fin
            ):
                ok &= abs(q10[a["parcela_id"]]["margen_c"] - (a["valor_extremo"] - a["umbral"])) <= 0.011
            r.chequear(
                ok,
                f"Q10 | {n.finca_id} {n.fecha:%d/%m}: 'alto' con el mismo margen que guarda la alerta "
                f"({', '.join(f'{p} {q10[p]['margen_c']:+.2f}' for p in sorted(esperadas))})",
            )
        else:
            ok = all(q10[p]["nivel"] == n.resultado for p in propias_finca)
            r.chequear(
                ok,
                f"Q10 | {n.finca_id} {n.fecha:%d/%m}: noche sin alerta, riesgo '{n.resultado}' "
                f"({', '.join(f'{p} {q10[p]['nivel']} {q10[p]['margen_c']:+.2f}' for p in propias_finca)})",
            )
    # una noche sin frío no tiene alertas ni parcelas bajo el umbral
    r.chequear(
        q2_minima_bajo_umbral.consultar(bd, date(2026, 11, 20)) == []
        and all(f["horas_bajo_cero"] == 0 for f in q1_horas_bajo_cero.consultar(bd, date(2026, 11, 20))),
        "Q1 y Q2 | 20/11, sin frío: 0 horas bajo cero y ninguna parcela bajo el umbral",
    )
    nivel = {f["nivel"] for f in q10_riesgo_de_helada.consultar(bd, date(2026, 11, 20))}
    r.chequear(nivel <= {"bajo", "medio"}, f"Q10 | 20/11, sin frío: nunca 'alto' (niveles {sorted(nivel)})")


def probar_q3_q4(r, bd):
    punto = q3_nodos_cercanos.PUNTO
    nodos = list(bd.nodos.find())

    def distancia(a, b):  # metros sobre la esfera (haversine)
        la1, lo1, la2, lo2 = map(math.radians, (a[1], a[0], b[1], b[0]))
        h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
        return 2 * 6378100 * math.asin(math.sqrt(h))

    esperado = sorted((distancia(punto, n["ubicacion"]["coordinates"]), n["_id"]) for n in nodos)[:4]
    filas, seg = cronometrar(q3_nodos_cercanos.consultar, bd, punto, 4)
    ok = [f["nodo_id"] for f in filas] == [n for _, n in esperado] or sorted(f["nodo_id"] for f in filas[:2]) == [
        "N-SR-1-A",
        "N-SR-1-B",
    ]
    ok &= all(abs(f["distancia_m"] - d) < 0.5 for f, (d, _) in zip(filas, esperado))
    r.chequear(
        ok and sorted(f["nodo_id"] for f in filas[:2]) == ["N-SR-1-A", "N-SR-1-B"],
        f"Q3 | los 4 nodos más cercanos al centro de P-SR-1 con distancias iguales a un cálculo aparte: "
        f"{', '.join(f'{f['nodo_id']} {f['distancia_m']} m' for f in filas)} ({seg:.2f} s)",
    )

    evento = q4_parcelas_en_evento.buscar_evento(bd)

    def caja(poligono):  # rectángulo que contiene al polígono
        xs, ys = zip(*poligono["coordinates"][0])
        return min(xs), min(ys), max(xs), max(ys)

    e = caja(evento["area"])
    esperadas = sorted(
        p["_id"]
        for p in bd.parcelas.find()
        if (lambda c: c[0] <= e[2] and c[2] >= e[0] and c[1] <= e[3] and c[3] >= e[1])(caja(p["geometria"]))
    )
    filas, seg = cronometrar(q4_parcelas_en_evento.consultar, bd)
    r.chequear(
        [f["parcela_id"] for f in filas] == esperadas == ["P-SR-1", "P-SR-2"],
        f"Q4 | parcelas dentro del evento de la noche extrema: {[f['parcela_id'] for f in filas]} = rectángulos que se "
        f"solapan {esperadas} ({seg:.2f} s)",
    )


def probar_q5_q6(r, bd, config):
    casos = [
        (datetime(2026, 11, 12, 21, 0, tzinfo=timezone.utc), ["N-SR-1-A"], "dentro del corte de 6 h de N-SR-1-A"),
        (datetime(2027, 3, 31, 12, 0, tzinfo=timezone.utc), ["N-TU-2-B"], "N-TU-2-B en mantenimiento"),
        (comun.AHORA, [], "la fecha inicial del dashboard: todos reportan"),
        (
            datetime(2026, 11, 12, 17, 20, tzinfo=timezone.utc),
            [],
            "20 min después de la última lectura: aún no pasó el límite",
        ),
    ]
    for ahora, esperados, texto in casos:
        filas, seg = cronometrar(q5_nodos_sin_reportar.consultar, bd, ahora)
        r.chequear(
            [f["nodo_id"] for f in filas] == esperados,
            f"Q5 | ahora {ahora:%d/%m/%Y %H:%M}Z, {texto}: {[f['nodo_id'] for f in filas] or 'ninguno'} ({seg:.2f} s)",
        )
    # independiente: la última lectura de N-SR-1-A antes del corte
    ultima = next(
        bd.lecturas.find({"meta.nodo_id": "N-SR-1-A", "ts": {"$lte": datetime(2026, 11, 12, 21, 0)}})
        .sort("ts", -1)
        .limit(1)
    )["ts"]
    fila = q5_nodos_sin_reportar.consultar(bd, datetime(2026, 11, 12, 21, 0, tzinfo=timezone.utc))[0]
    r.chequear(
        fila["ultima_lectura"] == ultima,
        f"Q5 | la última lectura informada ({fila['ultima_lectura']:%H:%M}Z) es la que dice un find aparte",
    )

    ahora = datetime(2027, 1, 20, 15, 30, tzinfo=timezone.utc)
    filas, seg = cronometrar(q6_humedad_suelo_horaria.consultar, bd, ahora, "P-SR-1")
    fin = ahora.replace(minute=0)
    por_hora = defaultdict(list)
    for d in lecturas_de(bd, "P-SR-1", fin - timedelta(hours=24), fin):
        por_hora[d["ts"].replace(minute=0, second=0, microsecond=0)].append(d["humedad_suelo_pct"])
    dif = max(abs(f["humedad_suelo_pct"] - sum(por_hora[f["hora"]]) / len(por_hora[f["hora"]])) for f in filas)
    r.chequear(
        len(filas) == 24 and all(f["lecturas"] == 24 for f in filas) and dif < 0.01,
        f"Q6 | 24 horas completas de P-SR-1, 24 lecturas cada una, promedios a {dif:.3f} puntos de un cálculo aparte ({seg:.2f} s)",
    )


def probar_q7_q8(r, bd):
    # Q7: litros por parcela y semana
    propias = defaultdict(float)
    for d in bd.riegos.find({"parcela_id": "P-SR-1"}):
        propias[lunes_de(d["inicio"])] += d["litros"]
    filas, seg = cronometrar(q7_litros_por_semana.consultar, bd, "P-SR-1")
    ok = {semana(f["semana"]): f["litros"] for f in filas} == dict(propias)
    r.chequear(
        ok and len(filas) > 25,
        f"Q7 | P-SR-1: {len(filas)} semanas (lunes a domingo) con los mismos litros que una suma aparte ({seg:.2f} s)",
    )
    por_finca = defaultdict(float)
    for f in q7_litros_por_semana.consultar(bd):
        por_finca[f["parcela_id"][2:4]] += f["litros"]
    r.chequear(
        dict(por_finca) == {"SR": 100_320_000, "SM": 103_360_000, "TU": 22_760_000},
        f"Q7 | litros de toda la temporada por finca: {dict(por_finca)}",
    )

    # Q8: heladas por departamento y semana
    dep = {p["_id"]: bd.fincas.find_one({"_id": p["finca_id"]})["departamento"] for p in bd.parcelas.find()}
    propias = defaultdict(lambda: [0, set()])
    for a in bd.alertas.find({"tipo": "helada"}):
        clave = (dep[a["parcela_id"]], lunes_de(a["inicio"]))
        propias[clave][0] += 1
        propias[clave][1].add(a["parcela_id"])
    filas, seg = cronometrar(q8_heladas_por_departamento.consultar, bd)
    obtenidas = {(f["departamento"], semana(f["semana"])): (f["alertas"], f["parcelas_afectadas"]) for f in filas}
    r.chequear(
        obtenidas == {k: (v[0], len(v[1])) for k, v in propias.items()} and len(filas) == 5,
        "Q8 | "
        + "; ".join(f"{d} {s:%d/%m}: {a}" for (d, s), (a, _) in sorted(obtenidas.items(), key=lambda x: x[0][1]))
        + f" (igual a un conteo aparte, {seg:.2f} s)",
    )


def ejecutar_mongosh(texto: str):
    """Corre el texto de mongosh en la base de prueba y devuelve el resultado como lista de Python."""
    salida = subprocess.run(
        ["mongosh", BASE_DE_PRUEBA, "--quiet", "--eval", f"JSON.stringify({texto}.toArray())"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout
    return json.loads(salida.strip().splitlines()[-1])


def probar_texto_mongosh(r, bd):
    if shutil.which("mongosh") is None:
        r.chequear(False, "mongosh | no está en el PATH: no se pudo comprobar el texto de mongosh")
        return
    fecha = date(2026, 10, 5)
    texto = comun.texto_mongosh("lecturas", q1_horas_bajo_cero.pipeline(fecha))
    en_shell = {f["parcela_id"]: f["horas_bajo_cero"] for f in ejecutar_mongosh(texto)}
    en_python = {f["parcela_id"]: f["horas_bajo_cero"] for f in q1_horas_bajo_cero.consultar(bd, fecha)}
    r.chequear(en_shell == en_python, f"mongosh | Q1 ejecutada en mongosh da lo mismo que en Python ({en_shell})")

    evento = q4_parcelas_en_evento.buscar_evento(bd)
    en_shell = sorted(
        f["parcela_id"]
        for f in ejecutar_mongosh(comun.texto_mongosh("parcelas", q4_parcelas_en_evento.pipeline(evento["area"])))
    )
    r.chequear(
        en_shell == sorted(f["parcela_id"] for f in q4_parcelas_en_evento.consultar(bd)),
        f"mongosh | Q4 ejecutada en mongosh devuelve las mismas parcelas {en_shell}",
    )

    filas = ejecutar_mongosh(comun.texto_mongosh("riegos", q7_litros_por_semana.pipeline("P-SR-1")))
    r.chequear(
        len(filas) == len(q7_litros_por_semana.consultar(bd, "P-SR-1"))
        and math.isclose(
            sum(f["litros"] for f in filas), sum(f["litros"] for f in q7_litros_por_semana.consultar(bd, "P-SR-1"))
        ),
        f"mongosh | Q7 ejecutada en mongosh: {len(filas)} semanas y los mismos litros",
    )


def main() -> None:
    preparar_consola()
    r = Resumen()
    bd = obtener_base(BASE_DE_PRUEBA)
    print(f"Base de prueba: {bd.name} (se carga el seed y la temporada; la base real no se toca)")
    silencio(cargar_seed.cargar, bd)
    contexto = generar.cargar_contexto(bd)
    temporada = generar.simular(contexto)
    silencio(generar.escribir, bd, temporada)
    crear_indices(bd)
    etapas = contexto.variedad["etapas"]
    config = comun.configuracion(bd)

    print("--- Q9, etapa por grados-día")
    probar_q9(r, bd, temporada, etapas)
    print("--- Q1, Q2 y Q10 en las 8 noches de helada")
    probar_q1_q2_q10(r, bd, temporada, config)
    print("--- Q3 y Q4, geoespaciales")
    probar_q3_q4(r, bd)
    print("--- Q5 y Q6")
    probar_q5_q6(r, bd, config)
    print("--- Q7 y Q8")
    probar_q7_q8(r, bd)
    print("--- Texto de mongosh")
    probar_texto_mongosh(r, bd)
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
