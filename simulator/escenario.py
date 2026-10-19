"""Escenario de la temporada: temperatura y humedad del aire de cada nodo, y la etapa de cada parcela.

No toca la base: recibe los documentos de configuración, variedad, fincas, parcelas y nodos
(los que carga el seed) y devuelve arreglos de numpy. Es lo que usan `generar.py` y las pruebas.

La mínima de una noche de helada depende de la etapa de ese día (con el brote 2 °C más frío
que el sensor, solo hay alerta si cruza el umbral de la etapa), y la etapa depende de las
temperaturas, helada incluida. Se resuelve repitiendo hasta que coincidan ("punto fijo"):
    1. Etapa de cada día con el clima sin heladas.
    2. Con esas etapas se fijan las mínimas de las noches y se genera el clima completo.
    3. Se vuelve a calcular la etapa con ese clima; si cambió en alguna noche, se repite.
Todo el azar (ruido de los nodos, variación diaria) se sortea una sola vez antes de repetir.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

import numpy as np

from db.departamentos import clave_departamento
from simulator import calendario, clima, fenologia, parametros as P

MAX_VUELTAS = 5


@dataclass
class NodoSim:
    id: str
    parcela_id: str
    finca_id: str
    temperatura: np.ndarray         # °C, con NaN donde el nodo no reportó
    humedad_aire: np.ndarray        # %, con NaN donde el nodo no reportó
    desvio_suelo: float             # puntos de humedad de suelo respecto de su gemelo
    ruido_suelo: np.ndarray         # puntos de humedad de suelo, ruido de cada lectura
    sin_reporte: np.ndarray         # True donde el nodo no reportó


@dataclass
class ParcelaSim:
    id: str
    finca_id: str
    suelo: str
    sistema_riego: str
    nodos: list[str]
    gd_diarios: np.ndarray          # grados-día de cada día
    etapa: np.ndarray               # posición en variedad["etapas"] de cada día
    exceso_calor: np.ndarray        # °C de máxima sobre la normal de cada día
    rng_riego: np.random.Generator


@dataclass
class Noche:
    finca_id: str
    fecha: object                   # día de la mañana en que se alcanza la mínima
    dia: int
    resultado: str                  # "alerta", "medio", "bajo" o "extrema"
    minima_c: float                 # mínima del nodo más frío
    umbral_c: float | None          # umbral de la etapa de ese día
    etapa: str
    extrema: bool = False


@dataclass
class Escenario:
    nodos: dict[str, NodoSim]
    parcelas: dict[str, ParcelaSim]
    noches: list[Noche] = field(default_factory=list)
    variedad: dict = field(default_factory=dict)
    config: dict = field(default_factory=dict)
    vueltas: dict[str, int] = field(default_factory=dict)   # cuántas vueltas necesitó cada finca


# --------------------------------------------------------------------------- utilidades

def a_hora_local(momento_utc: datetime) -> datetime:
    """Instante UTC (con o sin zona) en hora de Argentina, sin zona."""
    return momento_utc.replace(tzinfo=None) + timedelta(hours=P.UTC_ARGENTINA_H)


def ventana_noche_extrema(config: dict) -> tuple[int, int]:
    """Posición (primer y último paso) de la ventana de la noche extrema en la grilla de 5 minutos."""
    noche = config["noche_extrema"]
    return clima.indice_de_paso(a_hora_local(noche["inicio"])), clima.indice_de_paso(a_hora_local(noche["fin"]))


def _sin_reporte(nodo_id: str) -> np.ndarray:
    """Pasos en que el nodo no reportó: cortes puntuales y, si corresponde, el mantenimiento."""
    mascara = np.zeros(P.PASOS, dtype=bool)
    for nodo, inicio, horas in calendario.CORTES_NODOS:
        if nodo == nodo_id:
            desde = clima.indice_de_paso(inicio)
            mascara[desde:desde + horas * 60 // P.PASO_MIN] = True
    if nodo_id == calendario.NODO_EN_MANTENIMIENTO:
        mascara[clima.indice_de_paso(calendario.MANTENIMIENTO_DESDE):] = True
    return mascara


def _noches_de_la_finca(finca_id: str, config: dict, heladas: list) -> list[tuple]:
    """(fecha, resultado) de las noches de la finca, incluida la extrema."""
    noches = [(f, r) for fid, f, r in heladas if fid == finca_id]
    extrema = config["noche_extrema"]
    if extrema["finca_id"] == finca_id:
        noches.append((a_hora_local(extrema["fin"]).date(), "extrema"))
    return sorted(noches)


# --------------------------------------------------------------------------- construcción

def construir(config: dict, variedad: dict, fincas: list[dict], parcelas: list[dict],
              nodos: list[dict], heladas: list | None = None) -> Escenario:
    """Arma el escenario completo. Determinista: la semilla es P.SEMILLA.

    `heladas` reemplaza a calendario.HELADAS (sirve para explorar el clima sin heladas)."""
    heladas = calendario.HELADAS if heladas is None else heladas
    ids_finca = sorted(f["_id"] for f in fincas)
    hijos = np.random.SeedSequence(P.SEMILLA).spawn(len(ids_finca))
    delta = config["delta_brote_c"]
    etapas = variedad["etapas"]
    escenario = Escenario(nodos={}, parcelas={}, variedad=variedad, config=config)
    primero, ultimo = ventana_noche_extrema(config)

    for finca_id, hijo in zip(ids_finca, hijos):
        finca = next(f for f in fincas if f["_id"] == finca_id)
        limite = config["sospechoso_minimo_c"][clave_departamento(finca["departamento"])]
        if limite is None:
            raise RuntimeError(
                f"Falta el límite de temperatura sospechosa de {finca['departamento']} "
                "(configuracion.sospechoso_minimo_c): el simulador no genera heladas sin él (ADR-009).")

        parcelas_f = sorted((p for p in parcelas if p["finca_id"] == finca_id), key=lambda p: p["_id"])
        nodos_de = {p["_id"]: sorted(n["_id"] for n in nodos if n["parcela_id"] == p["_id"]) for p in parcelas_f}
        n_nodos = sum(len(v) for v in nodos_de.values())
        flujos = [np.random.default_rng(s) for s in hijo.spawn(2 + n_nodos + len(parcelas_f))]
        rng_clima, rng_rocio = flujos[0], flujos[1]
        rngs_nodo, rngs_riego = iter(flujos[2:2 + n_nodos]), iter(flujos[2 + n_nodos:])

        # --- todo el azar, una sola vez ---
        tmax0, tmin0 = clima.temperaturas_diarias(rng_clima, finca_id)
        amanecer, atardecer = clima.astronomia(finca_id)
        maxima_normal = clima.maxima_normal(finca_id)
        signo = {p["_id"]: float(rng_clima.choice([-1.0, 1.0])) for p in parcelas_f}
        anomalia = clima.anomalia_rocio(rng_rocio)
        ruidos = {}
        for p in parcelas_f:
            for nodo_id in nodos_de[p["_id"]]:
                rng = next(rngs_nodo)
                ruidos[nodo_id] = (rng.normal(0, P.RUIDO_TEMPERATURA_C, P.PASOS),
                                   rng.normal(0, P.RUIDO_HUMEDAD_AIRE, P.PASOS),
                                   rng.normal(0, P.RUIDO_HUMEDAD_SUELO, P.PASOS))
        huecos = {nodo_id: _sin_reporte(nodo_id) for ids in nodos_de.values() for nodo_id in ids}
        piso = np.full(P.PASOS, float(limite))
        if config["noche_extrema"]["finca_id"] == finca_id:
            piso[primero:ultimo + 1] = config["noche_extrema"]["minimo_c"]
        lista_noches = _noches_de_la_finca(finca_id, config, heladas)

        def armar(etapa_dia: np.ndarray):
            """Clima completo de la finca para unas etapas dadas."""
            tmax, tmin = tmax0.copy(), tmin0.copy()
            noches = []
            for fecha, resultado in lista_noches:
                dia = clima.indice_dia(fecha)
                etapa = etapas[etapa_dia[dia]]
                extrema = resultado == "extrema"
                minima = (config["noche_extrema"]["minimo_c"] if extrema
                          else calendario.minima_objetivo(resultado, etapa["umbral_helada_c"], delta))
                noches.append(Noche(finca_id, fecha, dia, resultado, minima, etapa["umbral_helada_c"],
                                    etapa["nombre"], extrema))
                descenso = (calendario.DESCENSO_MAXIMA_PREVIA_EXTREMA_C if extrema
                            else calendario.DESCENSO_MAXIMA_PREVIA_C)
                tmin[dia] = minima + P.DESVIO_TEMPERATURA_C          # el nodo más frío queda en `minima`
                tmax[dia - 1] = maxima_normal[dia - 1] - descenso
            base = clima.perfil_5min(tmax, tmin, amanecer, atardecer)
            for noche in noches:
                d = noche.dia
                t_puesta = float(clima.temperatura_en_puesta(tmax[d - 1], tmin[d - 1], amanecer[d], atardecer[d]))
                base = clima.noche_de_helada(base, d, float(tmin[d]), t_puesta, amanecer, atardecer,
                                             noche.extrema, P.DESVIO_TEMPERATURA_C)
            humedad_base = clima.humedad_aire(finca_id, base, anomalia)

            temperaturas, humedades = {}, {}
            for p in parcelas_f:
                for j, nodo_id in enumerate(nodos_de[p["_id"]]):
                    s = signo[p["_id"]] * (1 if j == 0 else -1)
                    r_temp, r_hum, _ = ruidos[nodo_id]
                    t = np.maximum(base + s * P.DESVIO_TEMPERATURA_C + r_temp, piso)
                    h = np.clip(humedad_base + s * P.DESVIO_HUMEDAD_AIRE + r_hum, 0.0, 100.0)
                    temperaturas[nodo_id] = np.where(huecos[nodo_id], np.nan, t)
                    humedades[nodo_id] = np.where(huecos[nodo_id], np.nan, h)
            return noches, tmax, temperaturas, humedades

        # --- punto fijo: etapas -> mínimas -> clima -> etapas ---
        p1 = parcelas_f[0]["_id"]
        base0 = clima.perfil_5min(tmax0, tmin0, amanecer, atardecer)
        sin_helada = [base0 + signo[p1] * P.DESVIO_TEMPERATURA_C, base0 - signo[p1] * P.DESVIO_TEMPERATURA_C]
        _, etapa_dia = fenologia.etapas_de_parcela(sin_helada, variedad)
        for vuelta in range(1, MAX_VUELTAS + 1):
            noches, tmax, temperaturas, humedades = armar(etapa_dia)
            _, etapa_nueva = fenologia.etapas_de_parcela([temperaturas[n] for n in nodos_de[p1]], variedad)
            if all(etapa_nueva[n.dia] == etapa_dia[n.dia] for n in noches):
                break
            etapa_dia = etapa_nueva
        else:
            raise RuntimeError(f"Las etapas de las noches de {finca_id} no se estabilizan tras {MAX_VUELTAS} "
                               "vueltas: hay que mover alguna fecha de calendario.HELADAS lejos de un cambio de etapa.")
        escenario.vueltas[finca_id] = vuelta
        escenario.noches += noches

        # --- resultado: nodos y parcelas de la finca ---
        for p in parcelas_f:
            for j, nodo_id in enumerate(nodos_de[p["_id"]]):
                s = signo[p["_id"]] * (1 if j == 0 else -1)
                escenario.nodos[nodo_id] = NodoSim(
                    nodo_id, p["_id"], finca_id, temperaturas[nodo_id], humedades[nodo_id],
                    s * P.DESVIO_HUMEDAD_SUELO, ruidos[nodo_id][2], huecos[nodo_id])
            gd, etapa = fenologia.etapas_de_parcela([temperaturas[n] for n in nodos_de[p["_id"]]], variedad)
            escenario.parcelas[p["_id"]] = ParcelaSim(
                p["_id"], finca_id, finca["tipo_suelo"], finca["sistema_riego"], nodos_de[p["_id"]],
                gd, etapa, tmax - maxima_normal, next(rngs_riego))
    return escenario
