"""Reglas de alerta de helada y de riego (ADR-003, ADR-005, ADR-012).

`Detector` es la regla en sí, sin saber de bases de datos: recibe un valor por paso y dice si
abre o cierra una alerta. La simulación en vivo (RF-14, opcional) puede usar la misma clase.

Alerta de helada, por parcela:
    - Valor: temperatura del brote = temperatura del nodo más frío - Δ (2 °C).
    - Se abre cuando queda por debajo del umbral de la etapa de ese día.
    - Se cierra después de 3 lecturas seguidas (15 min) por encima.
    - Guarda la etapa y el umbral con que se abrió, la mínima y, al cerrar, el riesgo.
Alerta de riego, por parcela: ver riego.py.
"""

import math
import warnings
from dataclasses import dataclass

import numpy as np

from simulator import clima, parametros as P
from simulator.escenario import NodoSim, ParcelaSim

NIVELES = ["bajo", "medio", "alto"]


class Detector:
    """Abre una alerta cuando el valor baja del umbral y la cierra tras N lecturas seguidas por encima.

    El umbral que cuenta es el del momento en que se abrió. Las lecturas faltantes (NaN)
    no cambian nada."""

    def __init__(self, lecturas_para_cerrar: int = 1):
        self.lecturas_para_cerrar = lecturas_para_cerrar
        self.abierto = False
        self.umbral: float | None = None
        self._recuperadas = 0

    def paso(self, i: int, valor: float, umbral: float | None) -> str | None:
        """Devuelve "abre", "cierra" o None."""
        if math.isnan(valor):
            return None
        if not self.abierto:
            if umbral is not None and not math.isnan(umbral) and valor < umbral:
                self.abierto, self.umbral, self._recuperadas = True, umbral, 0
                return "abre"
            return None
        if valor >= self.umbral:
            self._recuperadas += 1
            if self._recuperadas >= self.lecturas_para_cerrar:
                self.abierto = False
                return "cierra"
        else:
            self._recuperadas = 0
        return None


def nivel_riesgo(margen_c: float, agravantes: list[str], riesgo: dict) -> str:
    """Índice de riesgo de helada (ADR-005). `riesgo` es `configuracion.riesgo`.

    Nivel base por el margen entre la mínima del brote y el umbral: alto si margen <= 0,
    medio si <= 2, bajo si más. Cada agravante de duración o de aire seco sube un nivel; el de
    suelo seco sube de bajo a medio. Nunca supera "alto". No es un porcentaje de daño.
    """
    if margen_c <= riesgo["margen_alto_c"]:
        nivel = 2
    elif margen_c <= riesgo["margen_bajo_c"]:
        nivel = 1
    else:
        nivel = 0
    nivel += ("duracion" in agravantes) + ("aire_seco" in agravantes)
    if "suelo_seco" in agravantes and nivel == 0:
        nivel = 1
    return NIVELES[min(nivel, 2)]


@dataclass
class AlertaHeladaSim:
    parcela_id: str
    inicio: int                      # paso en que se abrió
    fin: int | None                  # paso en que se cerró
    posicion_etapa: int              # posición en variedad["etapas"] al abrirse
    umbral_c: float                  # umbral del brote con que se abrió
    valor_extremo_c: float           # mínima de la temperatura del brote
    riesgo: dict | None = None       # {nivel, margen_c, agravantes} al cerrar


def temperatura_del_brote(parcela: ParcelaSim, nodos: dict[str, NodoSim], delta_c: float) -> np.ndarray:
    """Temperatura del brote de la parcela: la del nodo más frío menos Δ."""
    a, b = (nodos[n].temperatura for n in parcela.nodos)
    return np.fmin(a, b) - delta_c


def detectar_heladas(parcela: ParcelaSim, nodos: dict[str, NodoSim], humedad_suelo: np.ndarray,
                     config: dict, variedad: dict) -> list[AlertaHeladaSim]:
    """Alertas de helada de una parcela en toda la temporada, con su riesgo al cerrar."""
    brote = temperatura_del_brote(parcela, nodos, config["delta_brote_c"])
    etapas = variedad["etapas"]
    umbral_etapa = np.array([np.nan if e["umbral_helada_c"] is None else e["umbral_helada_c"] for e in etapas])
    umbral_dia = umbral_etapa[parcela.etapa]

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)           # nodos sin reportar: NaN
        aire = np.nanmean([nodos[n].humedad_aire for n in parcela.nodos], axis=0)
    a, b = (nodos[n] for n in parcela.nodos)
    suelo = humedad_suelo + (a.desvio_suelo + b.desvio_suelo) / 2

    detector = Detector(P.CIERRE_HELADA_LECTURAS)
    alertas: list[AlertaHeladaSim] = []
    for i in range(P.PASOS):
        d = i // P.PASOS_DIA
        u = umbral_dia[d]
        evento = detector.paso(i, brote[i], None if math.isnan(u) else float(u))
        if evento == "abre":
            alertas.append(AlertaHeladaSim(parcela.id, i, None, int(parcela.etapa[d]), float(u), float(brote[i])))
        elif evento == "cierra":
            alertas[-1].fin = i
            alertas[-1].riesgo = _riesgo_al_cerrar(alertas[-1], brote, aire, suelo, parcela, config)
        if detector.abierto:
            alertas[-1].valor_extremo_c = min(alertas[-1].valor_extremo_c, float(brote[i]))
    return alertas


def _riesgo_al_cerrar(alerta: AlertaHeladaSim, brote: np.ndarray, aire: np.ndarray, suelo: np.ndarray,
                      parcela: ParcelaSim, config: dict) -> dict:
    """Riesgo de la alerta (ADR-005): margen entre la mínima del brote y el umbral, más agravantes."""
    cortes = config["riesgo"]
    tramo = slice(alerta.inicio, alerta.fin + 1)
    margen = alerta.valor_extremo_c - alerta.umbral_c
    agravantes = []
    cerca = np.nansum(brote[tramo] < alerta.umbral_c + cortes["margen_duracion_c"])
    if cerca * P.PASO_MIN >= cortes["horas_duracion"] * 60:
        agravantes.append("duracion")
    if np.nanmean(aire[tramo]) < cortes["aire_seco_pct"]:
        agravantes.append("aire_seco")
    mes = clima.meses()[alerta.inicio // P.PASOS_DIA]
    umbral_riego = config["umbrales_riego"][parcela.suelo][P.PERIODO_RIEGO[mes]]
    if suelo[alerta.inicio] < umbral_riego:
        agravantes.append("suelo_seco")
    return {"nivel": nivel_riesgo(margen, agravantes, cortes), "margen_c": round(margen, 2),
            "agravantes": agravantes}
