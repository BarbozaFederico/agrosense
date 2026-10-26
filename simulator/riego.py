"""Riego y humedad de suelo de una parcela (ADR-005, ADR-011, ADR-012).

Modelo de la humedad de suelo (puntos de % volumétrico):
    - Entre riegos baja una cantidad de puntos por día que depende del mes, del suelo y del calor
      de ese día (más seco en las olas de calor).
    - Un riego la sube linealmente hasta la capacidad de campo del suelo durante el riego.
      Goteo: cada día repone casi todo lo que perdió el día anterior, así que oscila cerca
      de la capacidad de campo y solo se aleja en las olas de calor.
    - Cuando el promedio de los dos nodos baja del umbral de riego se abre una alerta de
      riego y, 3 h después, empieza un riego extra (76 mm en surco, 4 mm en goteo). La alerta
      se cierra cuando la humedad vuelve a superar el umbral.
Los mm de cada riego son la lámina bruta que informan las fuentes; el modelo de humedad lleva
el suelo a capacidad de campo con cada riego (ADR-012).

Es un bucle sobre los 61.056 pasos de la parcela porque el riego extra depende de la alerta.
"""

from dataclasses import dataclass, field

import numpy as np

from db.seeds.umbrales_riego import SUELOS
from simulator import clima, parametros as P
from simulator.alertas import Detector
from simulator.escenario import NodoSim, ParcelaSim


@dataclass
class RiegoSim:
    inicio: int  # paso de inicio
    fin: int  # paso de fin (exclusivo)
    origen: str  # "turno" o "alerta"
    lamina_mm: float
    alerta: int | None = None  # posición de la alerta de riego que lo originó


@dataclass
class AlertaRiegoSim:
    inicio: int
    fin: int | None
    umbral: float
    minimo: float


@dataclass
class ResultadoRiego:
    humedad_suelo: np.ndarray  # % volumétrico de la parcela, cada 5 minutos
    riegos: list[RiegoSim] = field(default_factory=list)
    alertas: list[AlertaRiegoSim] = field(default_factory=list)


def capacidad_de_campo_pct(suelo: str) -> float:
    """Capacidad de campo del suelo en % (ADR-011): θFC × 100."""
    return float(SUELOS[suelo][0] * 100)


def _programados(parcela: ParcelaSim) -> dict[int, tuple[int, float]]:
    """Riegos de turno: {paso de inicio: (paso de fin, lámina mm)}."""
    meses = clima.meses()
    programados = {}
    if parcela.sistema_riego == "surco":
        numero = parcela.id.split("-")[2]
        primero = P.DESFASE_FINCA_DIAS[parcela.finca_id] + P.DESFASE_SURCO_DIAS[numero]
        for dia in range(primero, P.DIAS, P.INTERVALO_SURCO_DIAS):
            inicio = dia * P.PASOS_DIA + P.HORA_SURCO * 60 // P.PASO_MIN
            programados[inicio] = (inicio + P.DURACION_SURCO_H * 60 // P.PASO_MIN, float(P.LAMINA_SURCO_MM))
    else:
        for dia in range(P.DIAS):
            inicio = dia * P.PASOS_DIA + P.HORA_GOTEO * 60 // P.PASO_MIN
            programados[inicio] = (inicio + P.DURACION_GOTEO_H * 60 // P.PASO_MIN, float(P.GOTEO_MM_DIA[meses[dia]]))
    return programados


def simular_parcela(parcela: ParcelaSim, nodos: dict[str, NodoSim], config: dict) -> ResultadoRiego:
    """Humedad de suelo, riegos y alertas de riego de una parcela."""
    cc = capacidad_de_campo_pct(parcela.suelo)
    meses = clima.meses()
    # pérdida de puntos por día (según mes, suelo y calor) y umbral de riego de cada día
    calor = np.clip(1 + P.CALOR_PENDIENTE * parcela.exceso_calor, P.CALOR_MIN, P.CALOR_MAX)
    perdida_dia = np.array([P.TASA_SECADO_PTS_DIA[m] for m in meses]) * P.FACTOR_SUELO[parcela.suelo] * calor
    umbral_dia = np.array([config["umbrales_riego"][parcela.suelo][P.PERIODO_RIEGO[m]] for m in meses])

    a, b = (nodos[n] for n in parcela.nodos)
    desvio_medio = (a.desvio_suelo + b.desvio_suelo) / 2
    ruido_medio = (a.ruido_suelo + b.ruido_suelo) / 2
    # La alerta usa el promedio móvil de la última hora (12 lecturas) de los dos nodos: con el
    # valor instantáneo, el ruido del sensor cruzaría el umbral varias veces por episodio.
    ventana = P.CIERRE_RIEGO_LECTURAS
    ruido_medio = np.concatenate([np.zeros(ventana - 1), ruido_medio])
    ruido_medio = np.convolve(ruido_medio, np.ones(ventana) / ventana, mode="valid")

    programados = _programados(parcela)
    ocupado = np.zeros(P.PASOS + 1, dtype=bool)  # pasos cubiertos por un riego de turno
    for inicio, (fin, _) in programados.items():
        ocupado[inicio:fin] = True
    lamina_extra = P.LAMINA_EXTRA_SURCO_MM if parcela.sistema_riego == "surco" else P.LAMINA_EXTRA_GOTEO_MM

    resultado = ResultadoRiego(humedad_suelo=np.empty(P.PASOS))
    detector = Detector(P.CIERRE_RIEGO_LECTURAS)
    extras: dict[int, tuple[int, int]] = {}  # {inicio: (fin, posición de la alerta)}
    activo = None  # riego en curso
    h = cc - 1.0  # arranca un punto bajo la capacidad de campo

    for i in range(P.PASOS):
        d = i // P.PASOS_DIA
        # --- ¿empieza un riego? (los de turno tienen prioridad sobre un extra) ---
        if activo is None:
            if i in programados:
                fin, lamina = programados[i]
                if parcela.sistema_riego == "surco":
                    objetivo = cc
                else:  # goteo: repone casi todo lo perdido ayer
                    repone = perdida_dia[max(d - 1, 0)] * parcela.rng_riego.uniform(*P.RECARGA_GOTEO)
                    objetivo = min(cc, h + repone)
                activo = (i, fin, h, objetivo, "turno", lamina, None)
            elif i in extras:
                fin, posicion = extras.pop(i)
                activo = (i, fin, h, cc, "alerta", float(lamina_extra), posicion)

        # --- evolución de la humedad ---
        if activo is not None:
            inicio, fin, h0, objetivo, origen, lamina, posicion = activo
            h = h0 + (objetivo - h0) * (i - inicio + 1) / (fin - inicio)
            if i == fin - 1:
                resultado.riegos.append(RiegoSim(inicio, fin, origen, lamina, posicion))
                activo = None
        else:
            h -= perdida_dia[d] / P.PASOS_DIA
        h = max(h, P.HUMEDAD_SUELO_MINIMA)
        resultado.humedad_suelo[i] = h

        # --- alerta de riego: promedio de los dos nodos bajo el umbral del día ---
        promedio = h + desvio_medio + ruido_medio[i]
        evento = detector.paso(i, promedio, umbral_dia[d])
        if evento == "abre":
            resultado.alertas.append(AlertaRiegoSim(i, None, float(umbral_dia[d]), promedio))
            largo = P.DURACION_EXTRA_H * 60 // P.PASO_MIN
            inicio_extra = i + P.DEMORA_EXTRA_H * 60 // P.PASO_MIN
            if parcela.sistema_riego == "goteo":
                # el goteo riega todos los días: el extra espera al primer hueco libre
                while inicio_extra + largo < P.PASOS and ocupado[inicio_extra : inicio_extra + largo].any():
                    inicio_extra += 1
            # en surco, si un turno está por empezar ya resuelve la alerta: no se agrega otro riego
            if inicio_extra + largo < P.PASOS and not ocupado[inicio_extra : inicio_extra + largo].any():
                extras[inicio_extra] = (inicio_extra + largo, len(resultado.alertas) - 1)
        elif evento == "cierra":
            resultado.alertas[-1].fin = i
        if detector.abierto:
            resultado.alertas[-1].minimo = min(resultado.alertas[-1].minimo, promedio)
    return resultado
