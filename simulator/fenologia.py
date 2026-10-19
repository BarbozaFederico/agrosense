"""Fenología: grados-día y etapa BBCH de cada parcela (ADR-004, ADR-010, ADR-012).

Es la MISMA regla que va a usar la consulta Q9, así los dos resultados coinciden:

    - Grados-día de un día = max(0, min((Tmáx + Tmín) / 2, tope) - base), con base 10 °C y
      tope 32 °C (Zapata et al. 2017). Se cuentan desde el 1/9.
    - Tmáx y Tmín del día de una parcela = promedio de las de sus 2 nodos, sobre el día
      local (hora de Argentina).
    - La etapa de un día usa los grados-día acumulados hasta el día ANTERIOR (lo que se
      sabe al empezar el día), menos los 70 grados-día hasta la brotación.
    - De ahí sale una de las etapas de `variedades.etapas`: la última cuyo
      `gd_desde_brotacion` no supera esos grados-día.
"""

import warnings

import numpy as np

from simulator import parametros as P


def extremos_diarios(temperaturas_nodos: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """(Tmáx, Tmín) de cada día de una parcela: promedio de los máximos y mínimos de sus nodos.
    Los huecos (NaN, nodo sin reportar) no cuentan."""
    por_dia = [t.reshape(P.DIAS, P.PASOS_DIA) for t in temperaturas_nodos]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)       # un día sin lecturas de un nodo da NaN
        maximos = np.nanmean([np.nanmax(t, axis=1) for t in por_dia], axis=0)
        minimos = np.nanmean([np.nanmin(t, axis=1) for t in por_dia], axis=0)
    return maximos, minimos


def grados_dia_diarios(tmax: np.ndarray, tmin: np.ndarray, base_c: float, tope_c: float) -> np.ndarray:
    """Grados-día de cada día."""
    return np.maximum(0.0, np.minimum((tmax + tmin) / 2, tope_c) - base_c)


def acumulados_hasta_ayer(gd_diarios: np.ndarray) -> np.ndarray:
    """Grados-día acumulados desde el 1/9 hasta el día anterior a cada día."""
    return np.concatenate([[0.0], np.cumsum(gd_diarios)[:-1]])


def etapa_de_cada_dia(gd_diarios: np.ndarray, variedad: dict) -> np.ndarray:
    """Posición (en `variedad["etapas"]`) de la etapa de cada día."""
    desde_brotacion = acumulados_hasta_ayer(gd_diarios) - variedad["grados_dia"]["hasta_brotacion"]
    umbrales = np.array([e["gd_desde_brotacion"] for e in variedad["etapas"]], dtype=float)
    posicion = np.searchsorted(umbrales, desde_brotacion, side="right") - 1
    return np.clip(posicion, 0, len(umbrales) - 1)


def etapas_de_parcela(temperaturas_nodos: list[np.ndarray], variedad: dict) -> tuple[np.ndarray, np.ndarray]:
    """(gd_diarios, posicion_de_etapa_por_dia) de una parcela, a partir de las lecturas de sus nodos."""
    tmax, tmin = extremos_diarios(temperaturas_nodos)
    gd = grados_dia_diarios(tmax, tmin, variedad["grados_dia"]["base_c"], variedad["grados_dia"]["tope_c"])
    return gd, etapa_de_cada_dia(gd, variedad)


def dia_de_brotacion(gd_diarios: np.ndarray, variedad: dict) -> int | None:
    """Primer día (posición) en que la parcela está en brotación o después; None si nunca."""
    brotacion = variedad["grados_dia"]["hasta_brotacion"]
    acumulado = acumulados_hasta_ayer(gd_diarios)
    dias = np.nonzero(acumulado >= brotacion)[0]
    return int(dias[0]) if len(dias) else None
