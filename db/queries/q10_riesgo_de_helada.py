"""Q10 - ¿Qué índice de riesgo de helada tuvo cada parcela en cada noche?

Requisito: RF-19.   Técnica: $group + $setWindowFields + $lookup (ADR-005).

El índice NO es un porcentaje de daño: es un nivel (bajo, medio, alto) que combina:
    Margen = mínima de la temperatura del brote en la noche - umbral de la etapa.
        Nivel base: alto si margen <= 0, medio si margen <= 2, bajo si es mayor.
    Agravantes (cada uno sube un nivel, con tope "alto"):
        duración    2 h o más con el brote a menos de 1 °C por encima del umbral;
        aire seco   humedad del aire media de la noche (22:00 a 08:00) menor al 60 %;
        suelo seco  (solo sube de bajo a medio) humedad de suelo media bajo el umbral de riego.
Los cortes salen de `configuracion.riesgo`. El brote es la temperatura del nodo más frío menos Δ.
Usa la etapa ESTIMADA (Q9), igual que las alertas guardadas (ADR-014).

Cómo se calcula:
    1. Etapa y umbral de cada parcela (Q9).
    2. $group por parcela e instante: temperatura del nodo más frío, humedad de aire y de suelo medias.
    3. $setWindowFields con $integral: horas con el brote cerca del umbral.
    4. $group por parcela: mínima, horas, humedades medias.
    5. $set: margen, agravantes y nivel.

Cómo correrla (desde la raíz del repo):
    python -m db.queries.q10_riesgo_de_helada --fecha 2026-09-21
"""

from datetime import date

from db.conexion import obtener_base, preparar_consola
from db.queries import comun, q9_etapa_por_grados_dia as q9

COLECCION = "lecturas"
NIVELES = ["bajo", "medio", "alto"]
HORA_NOCHE_DESDE, HORA_NOCHE_HASTA = 22, 8      # "noche" para la humedad del aire: 22:00 a 08:00 hora local


def umbral_de_riego_por_parcela(bd, fecha: date) -> dict[str, float]:
    """{parcela_id: umbral de humedad de suelo (%)} del suelo de su finca en el período de `fecha`."""
    config = comun.configuracion(bd)
    periodo = comun.PERIODO_RIEGO[fecha.month]
    suelo_de_finca = {f["_id"]: f["tipo_suelo"] for f in bd.fincas.find({}, {"tipo_suelo": 1})}
    return {p["_id"]: config["umbrales_riego"][suelo_de_finca[p["finca_id"]]][periodo]
            for p in bd.parcelas.find({}, {"finca_id": 1})}


def _en_lista(agravante: str):
    return {"$cond": [{"$in": [agravante, "$agravantes"]}, 1, 0]}


def pipeline(fecha: date, etapas: dict[str, dict], umbral_riego: dict[str, float], config: dict) -> list:
    """`etapas`: resultado de q9.etapas_estimadas. `config`: documento de `configuracion`."""
    inicio, fin = comun.ventana_noche(fecha)
    delta, cortes = config["delta_brote_c"], config["riesgo"]
    umbrales = {p: e["umbral_helada_c"] for p, e in etapas.items()}
    nombres = {p: e["etapa"] for p, e in etapas.items()}

    def por_parcela(mapa, campo="$_id.parcela"):        # busca el valor de la parcela en un diccionario
        return {"$getField": {"field": campo, "input": {"$literal": mapa}}}

    return [
        {"$match": {"ts": {"$gte": inicio, "$lt": fin}}},
        # en cada instante: nodo más frío y humedades medias. El aire cuenta solo de noche
        # (22:00 a 08:00 hora de Argentina): la ventana llega hasta el mediodía y a esa hora el aire está seco
        {"$group": {"_id": {"parcela": "$meta.parcela_id", "ts": "$ts"},
                    "tmin": {"$min": "$temperatura_c"},
                    "aire": {"$avg": {"$cond": [{"$or": [
                        {"$gte": [{"$hour": {"date": "$ts", "timezone": comun.ZONA}}, HORA_NOCHE_DESDE]},
                        {"$lt": [{"$hour": {"date": "$ts", "timezone": comun.ZONA}}, HORA_NOCHE_HASTA]}]},
                        "$humedad_aire_pct", None]}},
                    "suelo": {"$avg": "$humedad_suelo_pct"}}},
        {"$set": {"umbral": por_parcela(umbrales)}},
        # horas con el brote a menos de `margen_duracion_c` por encima del umbral
        {"$setWindowFields": {
            "partitionBy": "$_id.parcela", "sortBy": {"_id.ts": 1},
            "output": {"horas_cerca": {
                "$integral": {"input": {"$cond": [
                    {"$lt": [{"$subtract": ["$tmin", delta]}, {"$add": ["$umbral", cortes["margen_duracion_c"]]}]}, 1, 0]},
                    "unit": "hour"},
                "window": {"range": ["unbounded", "current"], "unit": "hour"}}}}},
        {"$group": {"_id": "$_id.parcela", "minima_c": {"$min": "$tmin"}, "horas_cerca": {"$max": "$horas_cerca"},
                    "aire_medio": {"$avg": "$aire"}, "suelo_medio": {"$avg": "$suelo"},
                    "umbral_helada_c": {"$first": "$umbral"}}},
        {"$match": {"umbral_helada_c": {"$ne": None}}},               # una etapa sin umbral no se evalúa
        {"$set": {"minima_brote_c": {"$subtract": ["$minima_c", delta]},
                  "umbral_riego": por_parcela(umbral_riego, "$_id"), "etapa": por_parcela(nombres, "$_id")}},
        {"$set": {"margen_c": {"$subtract": ["$minima_brote_c", "$umbral_helada_c"]}}},
        {"$set": {"agravantes": {"$concatArrays": [
            {"$cond": [{"$gte": ["$horas_cerca", cortes["horas_duracion"]]}, ["duracion"], []]},
            {"$cond": [{"$lt": ["$aire_medio", cortes["aire_seco_pct"]]}, ["aire_seco"], []]},
            {"$cond": [{"$lt": ["$suelo_medio", "$umbral_riego"]}, ["suelo_seco"], []]}]}}},
        # nivel base (0 bajo, 1 medio, 2 alto) + duración + aire seco, con tope 2
        {"$set": {"nivel_base": {"$switch": {"branches": [
            {"case": {"$lte": ["$margen_c", cortes["margen_alto_c"]]}, "then": 2},
            {"case": {"$lte": ["$margen_c", cortes["margen_bajo_c"]]}, "then": 1}], "default": 0}}}},
        {"$set": {"nivel_n": {"$min": [2, {"$add": ["$nivel_base", _en_lista("duracion"), _en_lista("aire_seco")]}]}}},
        # suelo seco: solo sube de bajo a medio
        {"$set": {"nivel_n": {"$cond": [{"$and": [{"$eq": ["$nivel_n", 0]}, {"$in": ["suelo_seco", "$agravantes"]}]},
                                        1, "$nivel_n"]}}},
        {"$project": {
            "_id": 0, "parcela_id": "$_id", "etapa": 1, "umbral_helada_c": 1, "minima_c": 1,
            "minima_brote_c": {"$round": ["$minima_brote_c", 2]}, "margen_c": {"$round": ["$margen_c", 2]},
            "horas_cerca": {"$round": ["$horas_cerca", 2]}, "aire_medio": {"$round": ["$aire_medio", 1]},
            "suelo_medio": {"$round": ["$suelo_medio", 1]}, "agravantes": 1,
            "nivel": {"$arrayElemAt": [NIVELES, "$nivel_n"]}}},
        {"$sort": {"parcela_id": 1}},
    ]


def consultar(bd, fecha: date | str = comun.FECHA_NOCHE) -> list[dict]:
    """Índice de riesgo de cada parcela en la noche de la mañana `fecha`."""
    fecha = comun.a_fecha(fecha)
    return list(bd[COLECCION].aggregate(pipeline(
        fecha, q9.etapas_estimadas(bd, fecha), umbral_de_riego_por_parcela(bd, fecha), comun.configuracion(bd))))


def main() -> None:
    preparar_consola()
    p = comun.parser(__doc__.splitlines()[0])
    p.add_argument("--fecha", default=comun.FECHA_NOCHE.isoformat(), help="mañana de la noche (AAAA-MM-DD)")
    a = p.parse_args()
    bd = obtener_base()
    if a.mongosh:
        fecha = comun.a_fecha(a.fecha)
        print(comun.texto_mongosh(COLECCION, pipeline(fecha, q9.etapas_estimadas(bd, fecha),
                                                      umbral_de_riego_por_parcela(bd, fecha), comun.configuracion(bd))))
        return
    comun.imprimir_tabla(consultar(bd, a.fecha), ["parcela_id", "etapa", "umbral_helada_c", "minima_brote_c",
                                                  "margen_c", "horas_cerca", "aire_medio", "agravantes", "nivel"])


if __name__ == "__main__":
    main()
