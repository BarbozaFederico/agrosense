"""Genera la temporada simulada y la carga en MongoDB (ADR-004, ADR-012).

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m db.seeds.cargar         # requisito: fincas, parcelas, nodos, configuración
    python -m simulator.generar

Por defecto usa la base `agrosense`. Para otra base, en Git Bash:
    AGROSENSE_BD=agrosense_tests python -m simulator.generar

Qué hace, en este orden:
    1. Lee de la base la configuración, la variedad, las fincas, las parcelas y los nodos.
    2. Arma la temporada completa en memoria (simular): clima, riegos, alertas, observaciones.
    3. Valida alertas, riegos y observaciones con sus esquemas, sin guardar.
    4. Borra lo simulado anteriormente y vuelve a cargar (se puede repetir; el resultado es el mismo).
    5. Inserta las lecturas nodo por nodo, en lotes de 5.000, validando cada lote con el esquema de
       `lecturas` antes de insertarlo (ADR-007).
    6. Corre la auditoría de `lecturas`: tiene que dar 0 mal formadas y 0 sospechosas inesperadas.

Solo borra lo suyo: lecturas con `meta.fuente = "simulado"`, alertas y riegos con `fuente =
"simulado"` y observaciones con `fuente = "seed"`. No toca nada con `escenario_id`.
"""

import sys
import time
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
from bson import ObjectId
from pymongo.database import Database

from db.conexion import obtener_base, preparar_consola
from db.queries.auditoria_lecturas import auditar
from db.schemas import alertas as esquema_alertas
from db.schemas import lecturas as esquema_lecturas
from db.schemas import observaciones_fenologicas as esquema_observaciones
from db.schemas import riegos as esquema_riegos
from db.schemas.validar import validar_documentos
from simulator import alertas, calendario, clima, escenario as E, riego, parametros as P

TAMANO_LOTE = 5000


@dataclass
class Contexto:
    """Lo que el simulador lee de la base (o del seed, en las pruebas)."""
    config: dict
    variedad: dict
    fincas: list[dict]
    parcelas: list[dict]
    nodos: list[dict]


@dataclass
class Temporada:
    """La temporada simulada, lista para escribir."""
    escenario: E.Escenario
    humedad_suelo: dict[str, np.ndarray]               # por parcela
    alertas: list[dict] = field(default_factory=list)
    riegos: list[dict] = field(default_factory=list)
    observaciones: list[dict] = field(default_factory=list)
    resumen: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- lectura de la base

def cargar_contexto(bd: Database) -> Contexto:
    """Lee de la base lo que hace falta; si falta el seed, lo dice."""
    config = bd.configuracion.find_one({"_id": "general"})
    variedades = list(bd.variedades.find())
    fincas, parcelas, nodos = list(bd.fincas.find()), list(bd.parcelas.find()), list(bd.nodos.find())
    if not (config and variedades and fincas and parcelas and nodos):
        raise SystemExit("Faltan datos en la base: corré primero  python -m db.seeds.cargar")
    if {p["variedad_id"] for p in parcelas} != {"malbec"} or not any(v["_id"] == "malbec" for v in variedades):
        raise SystemExit("El simulador solo conoce la variedad 'malbec' (ADR-004).")
    variedad = next(v for v in variedades if v["_id"] == "malbec")
    return Contexto(config, variedad, fincas, parcelas, nodos)


def contexto_desde_seed(umbrales=None) -> Contexto:
    """Lo mismo que cargar_contexto, pero armado con los módulos del seed, sin base de datos."""
    from db.seeds import configuracion, fincas, nodos, parcelas, variedades
    return Contexto(configuracion.documentos(umbrales)[0], variedades.documentos()[0], fincas.documentos(),
                    parcelas.documentos(), nodos.documentos())


# --------------------------------------------------------------------------- identificadores

def id_determinista(tipo: str, parcela_id: str, n: int, momento: datetime) -> ObjectId:
    """ObjectId que sale siempre igual: 4 bytes de fecha, 4 de (tipo, parcela) y 4 de número."""
    segundos = int(momento.timestamp())
    huella = zlib.crc32(f"{tipo}:{parcela_id}".encode())
    return ObjectId(segundos.to_bytes(4, "big") + huella.to_bytes(4, "big") + n.to_bytes(4, "big"))


# --------------------------------------------------------------------------- la temporada

def simular(contexto: Contexto) -> Temporada:
    """Arma la temporada completa en memoria. Determinista."""
    esc = E.construir(contexto.config, contexto.variedad, contexto.fincas, contexto.parcelas, contexto.nodos)
    etapas = contexto.variedad["etapas"]
    superficie = {p["_id"]: p["superficie_ha"] for p in contexto.parcelas}
    ts = clima.marcas_de_tiempo_utc()
    temporada = Temporada(esc, {})

    for pid in sorted(esc.parcelas):
        parcela = esc.parcelas[pid]
        agua = riego.simular_parcela(parcela, esc.nodos, contexto.config)
        temporada.humedad_suelo[pid] = agua.humedad_suelo

        # --- alertas de riego y riegos (los extra apuntan a su alerta) ---
        ids_alerta_riego = []
        for n, a in enumerate(agua.alertas):
            dia = a.inicio // P.PASOS_DIA
            _id = id_determinista("alerta_riego", pid, n, ts[a.inicio])
            ids_alerta_riego.append(_id)
            temporada.alertas.append({
                "_id": _id, "tipo": "riego", "parcela_id": pid,
                "estado": "cerrada" if a.fin is not None else "abierta",
                "inicio": ts[a.inicio], "fin": ts[a.fin] if a.fin is not None else None,
                "etapa_bbch": etapas[parcela.etapa[dia]]["bbch_desde"],
                "umbral": round(a.umbral, 2), "valor_extremo": round(float(a.minimo), 2),
                "riesgo": None, "fuente": P.FUENTE})
        for n, r in enumerate(agua.riegos):
            doc = {"_id": id_determinista("riego", pid, n, ts[r.inicio]), "parcela_id": pid,
                   "inicio": ts[r.inicio], "fin": ts[min(r.fin, P.PASOS - 1)], "sistema": parcela.sistema_riego,
                   "origen": r.origen, "lamina_mm": r.lamina_mm,
                   "litros": round(r.lamina_mm * superficie[pid] * 10_000, 1), "fuente": P.FUENTE}
            if r.origen == "alerta":
                doc["alerta_id"] = ids_alerta_riego[r.alerta]
            temporada.riegos.append(doc)

        # --- alertas de helada ---
        for n, a in enumerate(alertas.detectar_heladas(parcela, esc.nodos, agua.humedad_suelo,
                                                       contexto.config, contexto.variedad)):
            temporada.alertas.append({
                "_id": id_determinista("alerta_helada", pid, n, ts[a.inicio]), "tipo": "helada",
                "parcela_id": pid, "estado": "cerrada" if a.fin is not None else "abierta",
                "inicio": ts[a.inicio], "fin": ts[a.fin] if a.fin is not None else None,
                "etapa_bbch": etapas[a.posicion_etapa]["bbch_desde"],
                "umbral": a.umbral_c, "valor_extremo": round(a.valor_extremo_c, 2),
                "riesgo": a.riesgo, "fuente": P.FUENTE})

        # --- observaciones fenológicas: una por mes, el día 15 ---
        for k, mes in enumerate(P.MESES_TEMPORADA):
            anio = P.INICIO.year if mes >= P.INICIO.month else P.FIN.year
            fecha = datetime(anio, mes, calendario.DIA_OBSERVACION, 15, 0, tzinfo=timezone.utc)   # 12:00 en Argentina
            dia = clima.indice_dia(fecha.date())
            posicion = int(parcela.etapa[dia]) + calendario.OBSERVACIONES_QUE_CORRIGEN.get((pid, fecha.date()), 0)
            posicion = min(max(posicion, 0), len(etapas) - 1)
            temporada.observaciones.append({
                "_id": id_determinista("observacion", pid, k, fecha), "parcela_id": pid, "fecha": fecha,
                "etapa_bbch": etapas[posicion]["bbch_desde"],
                "observador": "tecnico" if (k + int(pid[-1])) % 2 == 0 else "encargado", "fuente": "seed"})

    temporada.resumen = {
        "lecturas": int(sum((~n.sin_reporte).sum() for n in esc.nodos.values())),
        "alertas_helada": sum(1 for a in temporada.alertas if a["tipo"] == "helada"),
        "alertas_riego": sum(1 for a in temporada.alertas if a["tipo"] == "riego"),
        "riegos_turno": sum(1 for r in temporada.riegos if r["origen"] == "turno"),
        "riegos_alerta": sum(1 for r in temporada.riegos if r["origen"] == "alerta"),
        "observaciones": len(temporada.observaciones),
    }
    return temporada


def lecturas_de_nodo(temporada: Temporada, nodo_id: str, ts: list[datetime]):
    """Genera las lecturas de un nodo en lotes de TAMANO_LOTE documentos."""
    esc = temporada.escenario
    nodo = esc.nodos[nodo_id]
    suelo = np.clip(temporada.humedad_suelo[nodo.parcela_id] + nodo.desvio_suelo + nodo.ruido_suelo, 0.0, 100.0)
    temperatura, aire = np.round(nodo.temperatura, 2), np.round(nodo.humedad_aire, 2)
    suelo = np.round(suelo, 2)
    meta = {"nodo_id": nodo.id, "parcela_id": nodo.parcela_id, "finca_id": nodo.finca_id, "fuente": P.FUENTE}
    posiciones = np.nonzero(~nodo.sin_reporte)[0]
    for inicio in range(0, len(posiciones), TAMANO_LOTE):
        parte = posiciones[inicio:inicio + TAMANO_LOTE]
        yield [{"ts": ts[i], "meta": meta, "temperatura_c": t, "humedad_suelo_pct": s, "humedad_aire_pct": a}
               for i, t, s, a in zip(parte.tolist(), temperatura[parte].tolist(),
                                     suelo[parte].tolist(), aire[parte].tolist())]


# --------------------------------------------------------------------------- escritura

def escribir(bd: Database, temporada: Temporada) -> dict:
    """Valida, borra lo simulado anterior y carga la temporada. Devuelve el resultado de la auditoría."""
    print("3) Validación (sin guardar)")
    for nombre, modulo, docs in (("alertas", esquema_alertas, temporada.alertas),
                                 ("riegos", esquema_riegos, temporada.riegos),
                                 ("observaciones_fenologicas", esquema_observaciones, temporada.observaciones)):
        validos, invalidos = validar_documentos(bd, modulo.ESQUEMA, docs)
        print(f"  {nombre}: {len(validos)} válidos, {len(invalidos)} inválidos")
        if invalidos:
            raise SystemExit(f"Hay {nombre} inválidos, por ejemplo: {invalidos[0]}")

    print("4) Carga")
    borradas = {
        "lecturas": bd.lecturas.delete_many({"meta.fuente": P.FUENTE}).deleted_count,
        "alertas": bd.alertas.delete_many({"fuente": P.FUENTE}).deleted_count,
        "riegos": bd.riegos.delete_many({"fuente": P.FUENTE}).deleted_count,
        "observaciones": bd.observaciones_fenologicas.delete_many({"fuente": "seed"}).deleted_count,
    }
    print("  borrado de lo simulado antes: " + ", ".join(f"{k} {v}" for k, v in borradas.items()))
    bd.alertas.insert_many(temporada.alertas)
    bd.riegos.insert_many(temporada.riegos)
    bd.observaciones_fenologicas.insert_many(temporada.observaciones)
    bd.nodos.update_one({"_id": calendario.NODO_EN_MANTENIMIENTO}, {"$set": {"estado": "mantenimiento"}})
    print(f"  alertas {len(temporada.alertas)}, riegos {len(temporada.riegos)}, "
          f"observaciones {len(temporada.observaciones)}; nodo {calendario.NODO_EN_MANTENIMIENTO} en mantenimiento")

    print("5) Lecturas (validadas por lote antes de insertar)")
    ts = clima.marcas_de_tiempo_utc()
    total = 0
    for nodo_id in sorted(temporada.escenario.nodos):
        insertadas = 0
        for lote in lecturas_de_nodo(temporada, nodo_id, ts):
            validos, invalidos = validar_documentos(bd, esquema_lecturas.ESQUEMA, lote)
            if invalidos:
                raise SystemExit(f"{nodo_id}: {len(invalidos)} lecturas inválidas, por ejemplo: {invalidos[0]}")
            bd.lecturas.insert_many(validos, ordered=False)
            insertadas += len(validos)
        total += insertadas
        print(f"  {nodo_id}: {insertadas} lecturas")
    print(f"  total: {total}")

    print("6) Auditoría de lecturas")
    return auditar(bd)


# --------------------------------------------------------------------------- script

def main() -> None:
    preparar_consola()
    bd = obtener_base()
    print(f"Versión del servidor: {bd.client.server_info()['version']} | base: {bd.name}")
    inicio = time.time()

    print("1) Lectura de la base")
    contexto = cargar_contexto(bd)
    print("2) Simulación de la temporada")
    temporada = simular(contexto)
    print("  " + ", ".join(f"{k} {v}" for k, v in temporada.resumen.items()))

    auditoria = escribir(bd, temporada)
    print(f"  lecturas totales: {auditoria['total']} | mal formadas: {auditoria['mal_formadas']} (esperado 0) | "
          f"sospechosas esperadas: {auditoria['esperadas']} | inesperadas: {auditoria['inesperadas']} (esperado 0)")
    print(f"\nTiempo total: {time.time() - inicio:.0f} s")
    if not auditoria["aprobada"]:
        print("RESULTADO: FALLA la auditoría")
        sys.exit(1)
    print("RESULTADO: temporada simulada cargada y auditada")


if __name__ == "__main__":
    main()
