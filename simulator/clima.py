"""Clima de una finca: temperatura y humedad del aire cada 5 minutos (ADR-012).

Pasos (todo con arreglos de numpy, sin bucles sobre las 61.056 lecturas):
    1. astronomia()           hora del amanecer y de la puesta del sol de cada día.
    2. temperaturas_diarias() máxima y mínima de cada día: normal del mes + variación al azar.
    3. perfil_5min()          curva de Parton y Logan dentro del día, cada 5 minutos.
    4. noche_de_helada()      reemplaza una noche por la curva de helada (enfriamiento lento).
    5. humedad_aire()         humedad relativa con punto de rocío fijo por mes (Magnus).

Las horas son hora de Argentina (UTC-3). Un "día" es el día local: la mínima del amanecer
pertenece al día en que ocurre.
"""

import math
from datetime import date, datetime, timedelta, timezone

import numpy as np

from db.seeds.ubicaciones import CENTROS_FINCA
from simulator import parametros as P


# --------------------------------------------------------------------------- calendario

def fechas() -> list[date]:
    """Los 212 días de la temporada."""
    return [P.INICIO + timedelta(days=i) for i in range(P.DIAS)]


def meses() -> np.ndarray:
    """Mes (1 a 12) de cada día."""
    return np.array([f.month for f in fechas()])


def indice_dia(f: date) -> int:
    return (f - P.INICIO).days


def marcas_de_tiempo_utc() -> list[datetime]:
    """Fecha y hora UTC de cada una de las 61.056 lecturas (la misma lista sirve para todos los nodos)."""
    inicio_local = datetime(P.INICIO.year, P.INICIO.month, P.INICIO.day)
    inicio_utc = (inicio_local - timedelta(hours=P.UTC_ARGENTINA_H)).replace(tzinfo=timezone.utc)
    paso = timedelta(minutes=P.PASO_MIN)
    return [inicio_utc + paso * i for i in range(P.PASOS)]


def indice_de_paso(momento_local: datetime) -> int:
    """Posición de un instante local (naive, hora de Argentina) en la grilla de 5 minutos."""
    inicio = datetime(P.INICIO.year, P.INICIO.month, P.INICIO.day)
    return int((momento_local - inicio).total_seconds() // (P.PASO_MIN * 60))


def horas_del_dia() -> np.ndarray:
    """Hora local (0 a 24) de cada paso."""
    return np.tile(np.arange(P.PASOS_DIA) * P.PASO_MIN / 60, P.DIAS)


def dia_de_cada_paso() -> np.ndarray:
    return np.repeat(np.arange(P.DIAS), P.PASOS_DIA)


# --------------------------------------------------------------------------- astronomía

def astronomia(finca_id: str) -> tuple[np.ndarray, np.ndarray]:
    """Hora local del amanecer y de la puesta del sol de cada día (incluye un día de margen
    a cada lado, para la noche que empieza antes del 1/9 y la que termina después del 31/3).

    Devuelve dos arreglos de largo DIAS + 2: la posición k + 1 es el día k.
    Fórmulas astronómicas estándar (declinación solar, ecuación del tiempo); el amanecer sale
    de la longitud de la finca respecto del meridiano de UTC-3.
    """
    longitud, latitud = CENTROS_FINCA[finca_id]
    lat = math.radians(latitud)
    amanecer, atardecer = [], []
    for k in range(-1, P.DIAS + 1):
        f = P.INICIO + timedelta(days=k)
        n = f.timetuple().tm_yday
        decl = math.radians(23.45) * math.sin(2 * math.pi * (284 + n) / 365)
        horaria = math.acos(max(-1.0, min(1.0, -math.tan(lat) * math.tan(decl))))
        duracion = math.degrees(horaria) * 2 / 15 + 0.13          # +8 min: refracción y disco solar
        b = 2 * math.pi * (n - 81) / 364
        ecuacion_tiempo = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)   # minutos
        mediodia = 12 + (P.MERIDIANO_ARGENTINA - longitud) / 15 - ecuacion_tiempo / 60
        amanecer.append(mediodia - duracion / 2)
        atardecer.append(mediodia + duracion / 2)
    return np.array(amanecer), np.array(atardecer)


# --------------------------------------------------------------------------- temperaturas diarias

def _ar1(rng: np.random.Generator, n: int, sigma: float, phi: float) -> np.ndarray:
    """Serie con memoria: cada día se parece al anterior (AR(1) con desvío `sigma`)."""
    ruido = rng.normal(0, sigma * math.sqrt(1 - phi ** 2), n)
    serie = np.empty(n)
    serie[0] = rng.normal(0, sigma)
    for i in range(1, n):
        serie[i] = phi * serie[i - 1] + ruido[i]
    return serie


def temperaturas_diarias(rng: np.random.Generator, finca_id: str) -> tuple[np.ndarray, np.ndarray]:
    """(máxima, mínima) de cada día: normal del mes + anomalía común + variación propia.

    Los días comunes nunca bajan de PISO_MINIMA_COMUN_C: las heladas son solo las 8 noches
    designadas en calendario.py (ADR-012, decisión 6).
    """
    mes = meses()
    normal_max = np.array([P.NORMALES_C[finca_id][m][0] for m in mes])
    normal_min = np.array([P.NORMALES_C[finca_id][m][1] for m in mes])
    anomalia = _ar1(rng, P.DIAS, P.SIGMA_SINOPTICA_C, P.PERSISTENCIA)
    tmax = normal_max + anomalia + rng.normal(0, P.SIGMA_PROPIA_C, P.DIAS)
    tmin = normal_min + anomalia + rng.normal(0, P.SIGMA_PROPIA_C, P.DIAS)
    tmin = np.maximum(tmin, P.PISO_MINIMA_COMUN_C)
    tmax = np.maximum(tmax, tmin + 6.0)                          # amplitud mínima razonable
    return tmax, tmin


def maxima_normal(finca_id: str) -> np.ndarray:
    """Máxima normal de cada día (para medir cuánto más caluroso fue el día)."""
    return np.array([P.NORMALES_C[finca_id][m][0] for m in meses()])


# --------------------------------------------------------------------------- curva dentro del día

def _noche_normalizada(x: np.ndarray) -> np.ndarray:
    """Curva exponencial que va de 1 (puesta del sol) a 0 (amanecer), con x entre 0 y 1."""
    b = P.COEF_NOCHE
    return (np.exp(-b * x) - math.exp(-b)) / (1 - math.exp(-b))


def temperatura_en_puesta(tmax: float | np.ndarray, tmin: float | np.ndarray,
                          amanecer: float | np.ndarray, atardecer: float | np.ndarray):
    """Temperatura a la puesta del sol del día (Parton y Logan)."""
    duracion = atardecer - amanecer
    return tmin + (tmax - tmin) * np.sin(np.pi * duracion / (duracion + 2 * P.RETRASO_H))


def perfil_5min(tmax: np.ndarray, tmin: np.ndarray, amanecer: np.ndarray, atardecer: np.ndarray) -> np.ndarray:
    """Temperatura cada 5 minutos de toda la temporada (Parton y Logan, 1981).

    De día: seno que sube desde la mínima (amanecer) hacia la máxima.
    De noche: exponencial que baja desde la temperatura de la puesta del sol hasta la mínima
    del día siguiente, que se alcanza justo al amanecer.
    """
    def ext(a):                       # un día de margen a cada lado
        return np.concatenate([a[:1], a, a[-1:]])
    tx, tn = ext(tmax), ext(tmin)
    sr, ss = amanecer, atardecer      # ya vienen con margen
    duracion = ss - sr
    t_puesta = tn + (tx - tn) * np.sin(np.pi * duracion / (duracion + 2 * P.RETRASO_H))

    k = dia_de_cada_paso() + 1        # posición en los arreglos con margen
    h = horas_del_dia()

    de_dia = (h >= sr[k]) & (h < ss[k])
    madrugada = h < sr[k]

    m = h - sr[k]
    t_dia = tn[k] + (tx[k] - tn[k]) * np.sin(np.pi * m / (duracion[k] + 2 * P.RETRASO_H))

    x = (h + 24 - ss[k - 1]) / (24 - ss[k - 1] + sr[k])
    t_madrugada = tn[k] + (t_puesta[k - 1] - tn[k]) * _noche_normalizada(x)

    x = (h - ss[k]) / (24 - ss[k] + sr[k + 1])
    t_noche = tn[k + 1] + (t_puesta[k] - tn[k + 1]) * _noche_normalizada(x)

    return np.where(de_dia, t_dia, np.where(madrugada, t_madrugada, t_noche))


# --------------------------------------------------------------------------- noche de helada

def horas_bajo_cero(minima_c: float, extrema: bool = False) -> float:
    """Cuántas horas dura una helada según su profundidad (ADR-012, decisión 13).

    Normal: entre 3 y 5 horas, las que hagan falta para enfriar a menos de ~0,95 °C/h.
    Extrema: 7 horas (con -6,3 °C no cabe en 5 h a menos de 1 °C/h; ver ADR-013)."""
    if extrema:
        return P.HORAS_BAJO_CERO_EXTREMA
    return float(min(P.HORAS_BAJO_CERO_MAX, max(P.HORAS_BAJO_CERO_MIN, abs(minima_c) / P.VELOCIDAD_MAX_ENFRIAMIENTO)))


def noche_de_helada(temp: np.ndarray, dia_manana: int, minima_c: float, t_puesta_c: float,
                    amanecer: np.ndarray, atardecer: np.ndarray, extrema: bool = False,
                    nivel_cero_c: float = 0.0) -> np.ndarray:
    """Reemplaza, en `temp`, la noche que termina en el amanecer del día `dia_manana`.

    La curva tiene tres tramos (horas desde la puesta del sol):
        1. 0 a 2 h:        enfriamiento rápido, de la temperatura de la puesta a T2.
        2. 2 h hasta t0:   enfriamiento lento hasta `nivel_cero_c` (menos de 0,9 °C/h).
        3. t0 hasta el amanecer: baja de `nivel_cero_c` hasta la mínima, que se alcanza al amanecer.
    t0 se elige para que haya `horas_bajo_cero` horas bajo cero.

    `nivel_cero_c` es la temperatura de esta curva a la que el nodo MÁS FRÍO marca 0 °C: el nodo
    más frío está `nivel_cero_c` bajo la curva (desvío fijo del nodo), así que cruza 0 °C
    justo en t0 y las horas bajo cero se miden en él, no en la curva.
    """
    k = dia_manana + 1                                           # posición con margen
    puesta_previa = atardecer[k - 1]
    largo = 24 - puesta_previa + amanecer[k]                    # horas de noche
    # la profundidad que cuenta es la del nodo más frío: de `nivel_cero_c` (su 0 °C) a la mínima
    duracion_bajo_cero = horas_bajo_cero(minima_c - nivel_cero_c, extrema)
    t0 = largo - duracion_bajo_cero
    t2 = P.PRIMERAS_HORAS
    if t0 - t2 < 1.0:
        raise ValueError(f"La noche del día {dia_manana} es demasiado corta para una helada de {minima_c} °C")
    t_dos_horas = max(nivel_cero_c + 0.5, min(t_puesta_c - 3.0, nivel_cero_c + 0.9 * (t0 - t2)))

    paso_h = P.PASO_MIN / 60
    primero = int(math.ceil(((dia_manana - 1) * 24 + puesta_previa) / paso_h))
    ultimo = int(math.floor((dia_manana * 24 + amanecer[k]) / paso_h))
    indices = np.arange(max(primero, 0), min(ultimo, len(temp) - 1) + 1)
    t = indices * paso_h - ((dia_manana - 1) * 24 + puesta_previa)  # horas desde la puesta

    c = 1.5
    tramo1 = t_dos_horas + (t_puesta_c - t_dos_horas) * (np.exp(-c * t / t2) - math.exp(-c)) / (1 - math.exp(-c))
    tramo2 = nivel_cero_c + (t_dos_horas - nivel_cero_c) * (1 - (t - t2) / (t0 - t2))
    tramo3 = nivel_cero_c + (minima_c - nivel_cero_c) * (t - t0) / (largo - t0)
    nueva = np.where(t < t2, tramo1, np.where(t < t0, tramo2, tramo3))

    resultado = temp.copy()
    resultado[indices] = nueva
    return resultado


# --------------------------------------------------------------------------- humedad del aire

def presion_vapor(t):
    """Presión de vapor de saturación (hPa) a la temperatura `t` (Magnus)."""
    return 6.112 * np.exp(17.62 * t / (243.12 + t))


def punto_rocio_desde_humedad(t_c: float, humedad_pct: float) -> float:
    """Punto de rocío (°C) que da esa humedad relativa a esa temperatura (Magnus inverso)."""
    gamma = math.log(humedad_pct / 100) + 17.62 * t_c / (243.12 + t_c)
    return 243.12 * gamma / (17.62 - gamma)


def punto_rocio_mensual(finca_id: str) -> dict[int, float]:
    """Punto de rocío medio de cada mes: medido (SMN) o derivado (Tupungato)."""
    if finca_id in P.PUNTO_ROCIO_C:
        return P.PUNTO_ROCIO_C[finca_id]
    return {m: punto_rocio_desde_humedad(P.NORMALES_C[finca_id][m][1], P.HUMEDAD_NOCHE_TUPUNGATO_PCT[m])
            for m in P.MESES_TEMPORADA}


def anomalia_rocio(rng: np.random.Generator) -> np.ndarray:
    """Variación diaria del punto de rocío (se sortea una sola vez por finca)."""
    return _ar1(rng, P.DIAS, P.SIGMA_ROCIO_C, P.PERSISTENCIA_ROCIO)


def humedad_aire(finca_id: str, temp: np.ndarray, anomalia: np.ndarray) -> np.ndarray:
    """Humedad relativa (%) cada 5 minutos con el punto de rocío del mes fijo en cada día.

    El punto de rocío no puede superar la temperatura menos 2 °C: en una noche de helada el
    aire se seca y la humedad queda alta pero no en 100 % (ADR-012, decisión 5)."""
    mensual = punto_rocio_mensual(finca_id)
    base = np.array([mensual[m] for m in meses()])
    rocio = np.minimum(np.repeat(base + anomalia, P.PASOS_DIA), temp - 2.0)
    return np.clip(100 * presion_vapor(rocio) / presion_vapor(temp), 5.0, 100.0)
