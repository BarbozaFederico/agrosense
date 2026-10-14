// Spike ADR-001 · Prueba 1
// Pregunta: ¿se puede crear `lecturas` como serie temporal e insertar datos?
//
// Cómo correrlo (desde la raíz del repo):
//   mongosh --file scripts/spike-adr001/01_crear_serie_temporal.js
//
// Usa una base de PRUEBA llamada `spike_agrosense`. No toca ninguna base real.
// Los valores de las lecturas son inventados solo para probar: no representan nada.

// 1) Elegimos la base de prueba. getSiblingDB cambia de base sin salir del script.
const bd = db.getSiblingDB("spike_agrosense");

// 2) Borramos la base de prueba para empezar limpio. Así el script se puede repetir.
bd.dropDatabase();

// 3) Crear la colección de serie temporal.
//    timeField:   campo que guarda CUÁNDO se hizo la lectura.
//    metaField:   campo que guarda DE DÓNDE vino (nodo, parcela, finca).
//    granularity: avisa que las lecturas llegan cada pocos minutos
//                 (el proyecto simula una lectura cada 5 minutos).
bd.createCollection("lecturas", {
  timeseries: { timeField: "ts", metaField: "meta", granularity: "minutes" }
});

// 4) Insertar lecturas de prueba: 2 nodos de la misma parcela, 3 instantes cada uno.
//    Las fechas van en UTC (la "Z" del final). Mendoza está en UTC-3,
//    así que 03:00Z equivale a las 00:00 hora local.
//    Los nombres de los campos de medición (temperatura, humedad_suelo, humedad_aire)
//    son provisorios: el modelo todavía no los fijó.
const meta_n01 = { nodo_id: "N-01", parcela_id: "P-1", finca_id: "F-1" };
const meta_n02 = { nodo_id: "N-02", parcela_id: "P-1", finca_id: "F-1" };

const resultado = bd.lecturas.insertMany([
  { ts: new Date("2026-10-13T03:00:00Z"), meta: meta_n01, temperatura: -0.4, humedad_suelo: 31.0, humedad_aire: 62.0 },
  { ts: new Date("2026-10-13T03:05:00Z"), meta: meta_n01, temperatura: -0.8, humedad_suelo: 31.0, humedad_aire: 63.0 },
  { ts: new Date("2026-10-13T03:10:00Z"), meta: meta_n01, temperatura: -1.1, humedad_suelo: 30.9, humedad_aire: 64.0 },
  { ts: new Date("2026-10-13T03:00:00Z"), meta: meta_n02, temperatura: -0.2, humedad_suelo: 33.0, humedad_aire: 60.0 },
  { ts: new Date("2026-10-13T03:05:00Z"), meta: meta_n02, temperatura: -0.5, humedad_suelo: 33.1, humedad_aire: 61.0 },
  { ts: new Date("2026-10-13T03:10:00Z"), meta: meta_n02, temperatura: -0.9, humedad_suelo: 33.0, humedad_aire: 62.0 },
]);

// 5) Verificar. Estas líneas son las que hay que mirar y anotar.
print("Versión del servidor:", db.version());
// insertMany devuelve los _id que insertó (insertedIds); contarlos da la cantidad.
print("Documentos insertados:", Object.keys(resultado.insertedIds).length);
print("Documentos en la colección:", bd.lecturas.countDocuments());

// El tipo de la colección tiene que decir "timeseries". Si dice "collection", es común.
const info = bd.getCollectionInfos({ name: "lecturas" })[0];
print("Tipo de colección:", info.type);
printjson(info.options);

// Dos lecturas ordenadas por fecha, para ver cómo quedaron los documentos.
printjson(bd.lecturas.find().sort({ ts: 1 }).limit(2).toArray());
