"""Umbrales de humedad de suelo (%) para la alerta de riego, por tipo de suelo y período.

Fórmula (FAO-56, Allen et al. 1998, capítulo 8, ecuaciones 82 y 83): el agua que la planta
puede gastar sin sufrir estrés es p × (θFC − θWP), así que el riego se dispara cuando la
humedad baja a

    umbral = θFC − p × (θFC − θWP)

    θFC  capacidad de campo: humedad del suelo después de drenar (m³/m³).
    θWP  punto de marchitez: humedad a la que la planta ya no puede extraer agua (m³/m³).
    p    fracción del agua disponible que se puede gastar sin estrés.

Datos y fuentes (ADR-011):
    p = 0,45   FAO-56, Tabla 22, "Grapes – Wine" (válido para ETc ≈ 5 mm/día). Verificado en
               el original. Se usa el mismo valor en los 4 períodos: el ajuste por ETc y los
               p del ADR-005 para noviembre, diciembre-enero y febrero-marzo se descartaron.
    θFC, θWP   FAO-56, Tabla 19 (capítulo 7), rango por textura USDA. Verificado en el
               original. Se usa el PUNTO MEDIO del rango: es un cálculo propio, no una cifra
               de la FAO. El Ejemplo 35 usa 0,23 / 0,10 para sandy loam, algo distinto del
               punto medio (0,23 / 0,11).

    Suelo del proyecto     Clase de la Tabla 19     Rango θFC     Rango θWP     Usado θFC / θWP
    franco                 Loam                     0,20 – 0,30   0,07 – 0,17  0,25 / 0,12
    franco_arenoso         Sandy loam               0,18 – 0,28   0,06 – 0,16  0,23 / 0,11
    pedregoso (SUPUESTO)   Loamy sand               0,11 – 0,19   0,03 – 0,10  0,15 / 0,065 × (1 − 0,30)

Pedregoso: la FAO no tiene una clase "pedregoso" (las piedras no son una textura). DOS
SUPUESTOS ADOPTADOS (ADR-011 y ADR-012):
    1. La tierra fina se trata como loamy sand. La elección se apoya en descripciones de
       bodegas (Zuccardi 2024), que solo sirven de contexto.
    2. Las gravas ocupan el 30 % del volumen (RV_PEDREGOSO = 0,30), valor INVENTADO e
       ilustrativo: hay que medirlo. Las piedras no retienen agua, así que θFC y θWP del suelo
       completo se multiplican por (1 − Rv) (criterio del USDA-NRCS, Soil Quality Indicators:
       Available Water Capacity).
Ojo: si el sensor midiera solo la tierra fina, el umbral a comparar sería el de loamy sand sin
corregir (11,2 %). Se eligió corregir (ADR-011); el efecto de elegir mal es de unos 3 puntos.

Qué pesa más: la textura. Dentro del rango de la Tabla 19, un suelo franco da umbrales entre
14,2 % y 24,2 % con p = 0,45; entre períodos la diferencia sería de unos 2 puntos. Por eso
sería mejor medir θFC y θWP de cada parcela. Pendiente: el sensor del MVP es simulado.
"""

from decimal import ROUND_HALF_UP, Decimal

P_VID_DE_VINO = Decimal("0.45")      # FAO-56, Tabla 22

# Fracción del volumen del suelo pedregoso ocupada por gravas. SUPUESTO inventado, a medir.
RV_PEDREGOSO = Decimal("0.30")

# Suelo del proyecto → (θFC, θWP) en m³/m³, punto medio del rango de la Tabla 19.
SUELOS = {
    "franco": (Decimal("0.25"), Decimal("0.12")),             # Loam
    "franco_arenoso": (Decimal("0.23"), Decimal("0.11")),     # Sandy loam
    # Loamy sand (punto medio 0,15 / 0,065) menos las gravas: supuesto adoptado.
    "pedregoso": (Decimal("0.15") * (1 - RV_PEDREGOSO), Decimal("0.065") * (1 - RV_PEDREGOSO)),
}

PERIODOS = ["sep_oct", "nov", "dic_ene", "feb_mar"]


def umbral_pct(theta_fc: Decimal, theta_wp: Decimal, p: Decimal = P_VID_DE_VINO) -> float:
    """Humedad de suelo (% volumétrico) a la que se dispara el riego, con un decimal.

    Se usa Decimal para que 19,15 redondee a 19,2 (con números binarios podría dar 19,1)."""
    pct = (theta_fc - p * (theta_fc - theta_wp)) * 100
    return float(pct.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


# Mismo valor en los 4 períodos (p fijo). Se mantiene la estructura por período del esquema
# para poder ajustar p más adelante sin cambiar `configuracion` ni las consultas.
UMBRALES_RIEGO = {
    suelo: {periodo: umbral_pct(fc, wp) for periodo in PERIODOS}
    for suelo, (fc, wp) in SUELOS.items()
}
