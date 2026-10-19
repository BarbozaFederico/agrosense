"""Lo que está fijado de antemano en la temporada: las noches de helada, las fallas de nodos
y las observaciones que corrigen al modelo (ADR-012).

Las fechas de las heladas se eligieron mirando la etapa de cada finca: con el brote 2 °C más
frío que el sensor, solo hay alerta si la mínima cruza el umbral de la etapa de ese día. Cada
fecha cae a 2 días o más del cambio de etapa, porque las propias heladas corren unos
grados-día esos cambios (el escenario repite hasta estabilizarse, ver escenario.py).

Ventanas de etapa del clima simulado, aproximadas (se imprimen con probar_simulador.py):

    San Rafael   dormida hasta 16/9 · hinchada 17/9-28/9 · brotación 29/9-6/10 · 2 a 5 hojas 8/10-12/10
    San Martín   dormida hasta 12/9 · hinchada 13/9-18/9 · brotación 19/9-22/9 · 2 a 5 hojas 25/9-3/10
    Tupungato    dormida hasta 12/9 · hinchada 13/9-2/10 · brotación 3/10-5/10 · 2 a 5 hojas 8/10-12/10

En San Martín no puede haber alerta con la yema hinchada: su límite de temperatura sospechosa
(-2,8 °C) deja el brote en -4,8 °C, que no cruza el umbral de -6,1 °C.
"""

from datetime import date, datetime

# Resultado buscado de cada noche, medido con el brote 2 °C más frío que el sensor:
#   "alerta": la mínima cruza el umbral de la etapa y se abre una alerta de helada (riesgo alto).
#   "medio":  no cruza, pero queda a menos de 2 °C del umbral (Q10: riesgo medio).
#   "bajo":   no cruza y queda a más de 2 °C del umbral (Q10: riesgo bajo).
# (finca, día de la mañana en que se alcanza la mínima, resultado)
HELADAS = [
    ("F-SR", date(2026, 9, 21), "medio"),     # yema hinchada
    ("F-SR", date(2026, 10, 2), "alerta"),    # brotación
    # San Rafael, 5/10: la noche extrema se toma de `configuracion.noche_extrema` (ADR-009)
    ("F-SM", date(2026, 9, 15), "medio"),     # yema hinchada
    ("F-SM", date(2026, 9, 29), "alerta"),    # 2 a 5 hojas
    ("F-TU", date(2026, 9, 8), "bajo"),       # yema dormida
    ("F-TU", date(2026, 9, 22), "alerta"),    # yema hinchada
    ("F-TU", date(2026, 10, 10), "alerta"),   # 2 a 5 hojas
]

MARGEN_ALERTA_C = -0.4         # la mínima del brote queda 0,4 °C bajo el umbral
MARGEN_MEDIO_C = 1.3           # ... 1,3 °C sobre el umbral (entre 0 y 2: riesgo medio)
MINIMA_BAJO_C = -1.5           # noche "bajo": mínima fija del sensor
DESCENSO_MAXIMA_PREVIA_C = 3.0      # el día anterior a una helada es más fresco que lo normal
DESCENSO_MAXIMA_PREVIA_EXTREMA_C = 6.0


def minima_objetivo(resultado: str, umbral_c: float | None, delta_c: float) -> float:
    """Mínima que tiene que alcanzar el nodo más frío para lograr el resultado buscado."""
    if resultado == "bajo":
        return MINIMA_BAJO_C
    if umbral_c is None:
        raise ValueError(f"Una noche '{resultado}' necesita una etapa con umbral de helada")
    margen = MARGEN_ALERTA_C if resultado == "alerta" else MARGEN_MEDIO_C
    return round(umbral_c + delta_c + margen, 1)


# Cortes de reporte (Q5, pantalla de estado): (nodo, inicio local, horas sin reportar).
# Ninguno cae en una noche de helada.
CORTES_NODOS = [
    ("N-SR-1-A", datetime(2026, 11, 12, 14, 0), 6),
    ("N-SM-2-B", datetime(2026, 12, 3, 2, 0), 12),
    ("N-TU-1-A", datetime(2027, 1, 20, 9, 0), 3),
    ("N-SR-2-A", datetime(2027, 2, 8, 20, 0), 1),
    ("N-SM-1-B", datetime(2027, 3, 2, 11, 0), 9),
]

# Un nodo en mantenimiento: sin lecturas durante dos semanas a fin de temporada, y su estado
# en `nodos` queda en "mantenimiento" (el estado actual al cierre de la temporada).
NODO_EN_MANTENIMIENTO = "N-TU-2-B"
MANTENIMIENTO_DESDE = datetime(2027, 3, 17, 0, 0)      # hasta el final de la temporada

# Observaciones fenológicas (ADR-012, decisión 14): una por parcela el día 15 de cada mes.
# Estas dos difieren de la etapa que da el modelo, en +1 o -1 etapa, para mostrar que cuando
# hay observación manda la observación (ADR-004).
DIA_OBSERVACION = 15
OBSERVACIONES_QUE_CORRIGEN = {
    ("P-SR-1", date(2026, 10, 15)): +1,
    ("P-SM-2", date(2026, 11, 15)): -1,
}
