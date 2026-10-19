"""Parámetros del simulador. Todos están decididos en ADR-012 (supuestos adoptados) salvo
donde se indica una fuente.

Convención: las horas del día son hora de Argentina (UTC-3); se guardan en UTC.
"""

from datetime import date

# --- Calendario de la temporada (ADR-004) ---
SEMILLA = 2026                       # la temporada sale igual en cada corrida (ADR-012, decisión 10)
INICIO = date(2026, 9, 1)
FIN = date(2027, 3, 31)
DIAS = (FIN - INICIO).days + 1       # 212
PASO_MIN = 5                         # 1 lectura cada 5 minutos
PASOS_DIA = 24 * 60 // PASO_MIN      # 288
PASOS = DIAS * PASOS_DIA             # 61.056 por nodo; x 12 nodos = 732.672
UTC_ARGENTINA_H = -3
MERIDIANO_ARGENTINA = -45.0          # meridiano de UTC-3, para el mediodía solar

MESES_TEMPORADA = [9, 10, 11, 12, 1, 2, 3]

# --- Normales de temperatura (°C) por finca y mes: (máxima, mínima) ---
# San Rafael y San Martín: SMN, normales 1991-2020 (docs/investigacion/vid-malbec.md, sección 6d;
# verificadas en verificacion-fuentes.md). Tupungato: estación El Peral, DACC, 1998-2012.
NORMALES_C = {
    "F-SR": {9: (20.5, 4.9), 10: (23.9, 8.2), 11: (27.6, 11.4), 12: (30.7, 14.2),
             1: (31.8, 15.8), 2: (30.2, 14.7), 3: (27.4, 12.9)},
    "F-SM": {9: (22.2, 7.3), 10: (25.9, 11.1), 11: (29.4, 14.4), 12: (32.2, 17.0),
             1: (32.9, 18.3), 2: (31.2, 16.9), 3: (28.5, 15.0)},
    "F-TU": {9: (18.37, 3.73), 10: (23.03, 7.63), 11: (26.18, 10.03), 12: (28.68, 12.40),
             1: (29.75, 14.26), 2: (28.34, 13.71), 3: (25.55, 11.25)},
}

# --- Punto de rocío medio mensual (°C), medido (SMN, verificacion-fuentes.md, sección 1) ---
PUNTO_ROCIO_C = {
    "F-SR": {9: 1.3, 10: 4.4, 11: 6.9, 12: 9.1, 1: 11.4, 2: 11.6, 3: 10.7},
    "F-SM": {9: 2.8, 10: 6.2, 11: 9.2, 12: 11.8, 1: 14.1, 2: 14.0, 3: 13.0},
}
# Tupungato no tiene punto de rocío medido: se deriva de la humedad de noche supuesta de
# vid-malbec.md (tabla g) a la hora de la mínima. Supuesto adoptado (ADR-012, decisión 5).
HUMEDAD_NOCHE_TUPUNGATO_PCT = {9: 82, 10: 80, 11: 79, 12: 81, 1: 84, 2: 91, 3: 97}

# --- Variación diaria del clima (ADR-012, decisión 12) ---
SIGMA_SINOPTICA_C = 2.0              # anomalía común a la máxima y la mínima, persiste un par de días
PERSISTENCIA = 0.6                   # AR(1): correlación con el día anterior
SIGMA_PROPIA_C = 0.8                 # variación propia de cada día (máxima y mínima por separado)
SIGMA_ROCIO_C = 1.5                  # variación diaria del punto de rocío
PERSISTENCIA_ROCIO = 0.7
PISO_MINIMA_COMUN_C = 1.5            # los días sin helada designada nunca bajan de acá (ver calendario.py)
# --- Curva diaria de Parton y Logan (1981) ---
RETRASO_H = 1.86                     # a: retraso del máximo respecto del mediodía solar
COEF_NOCHE = 2.2                     # b: velocidad del enfriamiento nocturno

# --- Noche de helada (ADR-012, decisión 13) ---
VELOCIDAD_MAX_ENFRIAMIENTO = 0.95    # °C/h después de las primeras 2 h
HORAS_BAJO_CERO_MIN = 3.0
HORAS_BAJO_CERO_MAX = 5.0
HORAS_BAJO_CERO_EXTREMA = 7.0        # excepción de la noche extrema (llegar a -6,3 °C con <1 °C/h)
PRIMERAS_HORAS = 2.0                 # enfriamiento rápido tras la puesta del sol

# --- Nodos (ADR-012, decisión 10) ---
DESVIO_TEMPERATURA_C = 0.3           # un nodo +, el otro - (de a pares)
DESVIO_HUMEDAD_AIRE = 1.5
DESVIO_HUMEDAD_SUELO = 0.4           # detalle de implementación (ADR-013)
RUIDO_TEMPERATURA_C = 0.2
RUIDO_HUMEDAD_AIRE = 0.5
RUIDO_HUMEDAD_SUELO = 0.1            # detalle de implementación (ADR-013)

# --- Riego (ADR-012, decisión 8; ADR-005) ---
SUPERFICIE_HA = 2
LAMINA_SURCO_MM = 76
INTERVALO_SURCO_DIAS = 7
DURACION_SURCO_H = 2
HORA_SURCO = 10
DESFASE_SURCO_DIAS = {"1": 0, "2": 3}        # parcela 1 y 2 de cada finca en días distintos
DESFASE_FINCA_DIAS = {"F-SR": 1, "F-SM": 2}  # y las fincas tampoco riegan todas el mismo día
LAMINA_EXTRA_SURCO_MM = 76
LAMINA_EXTRA_GOTEO_MM = 4
DURACION_GOTEO_H = 4
HORA_GOTEO = 8
DEMORA_EXTRA_H = 3                   # el riego extra empieza 3 h después de abrirse la alerta de riego
DURACION_EXTRA_H = 2
# mm/día de goteo por mes (octubre y verano con fuente; el resto interpolado)
GOTEO_MM_DIA = {9: 1.5, 10: 1.5, 11: 2.5, 12: 3.5, 1: 3.5, 2: 3.5, 3: 2.5}

# --- Humedad de suelo (ADR-012, decisión 9) ---
# Puntos de humedad que pierde un suelo franco por día, según el mes. Se multiplican por el
# factor de cada suelo y por el factor de calor de cada día. Calibradas para que en las olas
# de calor el suelo cruce el umbral entre dos turnos y salte la alerta de riego.
TASA_SECADO_PTS_DIA = {9: 0.30, 10: 0.40, 11: 0.55, 12: 0.80, 1: 0.86, 2: 0.78, 3: 0.50}
FACTOR_SUELO = {"franco": 1.0, "franco_arenoso": 0.95, "pedregoso": 0.40}
CALOR_PENDIENTE = 0.04               # +4 % de secado por cada °C de máxima sobre la normal
CALOR_MIN, CALOR_MAX = 0.6, 1.6
RECARGA_GOTEO = (0.62, 0.82)         # fracción de lo perdido ayer que repone el goteo de hoy
                                     # (el suelo no se seca durante las 4 h del riego: ~0,83 de la pérdida diaria)
HUMEDAD_SUELO_MINIMA = 3.0           # el suelo del modelo nunca baja de acá

# --- Alertas (ADR-012, decisión 7) ---
CIERRE_HELADA_LECTURAS = 12          # 1 h seguida por encima del umbral para cerrar una alerta de helada
                                     # (con menos, el ruido de ±0,2 °C abre varias alertas en una misma noche)
CIERRE_RIEGO_LECTURAS = 12           # 1 h seguida sobre el umbral de riego (mismo motivo: el ruido)

# Mes -> período de los umbrales de riego de `configuracion.umbrales_riego`
PERIODO_RIEGO = {9: "sep_oct", 10: "sep_oct", 11: "nov", 12: "dic_ene", 1: "dic_ene",
                 2: "feb_mar", 3: "feb_mar"}

FUENTE = "simulado"
