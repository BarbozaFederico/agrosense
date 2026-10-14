// Spike ADR-001 · Prueba 3
// Pregunta: ¿se puede poner un índice geoespacial (2dsphere) en una serie temporal?
// Importa para Q3 (nodos más cercanos, $geoNear) y Q4 (parcelas dentro de un polígono, $geoIntersects).
// Si no se puede combinar, `eventos_climaticos` va como colección común (CLAUDE.md, sección 5).
//
// Cómo correrlo (desde la raíz del repo):
//   mongosh --file scripts/spike-adr001/03_indice_2dsphere.js
//
// Usa la base de PRUEBA `spike_agrosense`. No toca ninguna base real.
// Las coordenadas están inventadas, solo para probar. En GeoJSON el orden es [longitud, latitud].

const bd = db.getSiblingDB("spike_agrosense");
bd.dropDatabase();

// Un polígono de prueba (cerrado: el primer punto se repite al final) y tres puntos.
const poligono = {
  type: "Polygon",
  coordinates: [[[-68.40, -34.70], [-68.20, -34.70], [-68.20, -34.55], [-68.40, -34.55], [-68.40, -34.70]]]
};
const punto_dentro = { type: "Point", coordinates: [-68.30, -34.62] };   // cae dentro del polígono
const punto_fuera  = { type: "Point", coordinates: [-69.15, -33.37] };   // cae fuera

// Cinco colecciones, para comparar dónde funciona el índice:
//   ts_area:     serie temporal, con el POLÍGONO como campo común (fuera de meta)
//   ts_punto:    serie temporal, con un PUNTO como campo común (fuera de meta)
//   ts_meta:     serie temporal, con un PUNTO DENTRO de meta
//   comun_area:  colección común, con el polígono (punto de comparación)
//   comun_nodos: colección común, con puntos (punto de comparación para $geoNear)
const opciones_ts = { timeseries: { timeField: "ts", metaField: "meta" } };
bd.createCollection("ts_area", opciones_ts);
bd.createCollection("ts_punto", opciones_ts);
bd.createCollection("ts_meta", opciones_ts);
bd.createCollection("comun_area");
bd.createCollection("comun_nodos");

bd.ts_area.insertOne({ ts: new Date("2026-10-13T03:00:00Z"), meta: { evento_id: "E-1" }, area: poligono });
bd.comun_area.insertOne({ evento_id: "E-1", area: poligono });
bd.ts_punto.insertMany([
  { ts: new Date("2026-10-13T03:00:00Z"), meta: { nodo_id: "N-01" }, ubicacion: punto_dentro, temperatura: -0.4 },
  { ts: new Date("2026-10-13T03:00:00Z"), meta: { nodo_id: "N-02" }, ubicacion: punto_fuera,  temperatura: -0.2 },
]);
bd.ts_meta.insertMany([
  { ts: new Date("2026-10-13T03:00:00Z"), meta: { nodo_id: "N-01", ubicacion: punto_dentro }, temperatura: -0.4 },
  { ts: new Date("2026-10-13T03:00:00Z"), meta: { nodo_id: "N-02", ubicacion: punto_fuera },  temperatura: -0.2 },
]);
bd.comun_nodos.insertMany([
  { nodo_id: "N-01", ubicacion: punto_dentro },
  { nodo_id: "N-02", ubicacion: punto_fuera },
]);

// Ejecuta un caso y muestra OK o ERROR (igual que en la prueba 2).
function probar(descripcion, accion) {
  try {
    const resultado = accion();
    print("OK    | " + descripcion + " | " + JSON.stringify(resultado));
  } catch (e) {
    print("ERROR | " + descripcion + " | " + e.message);
  }
}

print("Versión del servidor:", db.version());
print("---");

// --- Crear índices ---

// 1) Índice 2dsphere en una serie temporal, sobre un campo común (el polígono)
probar("1. Índice 2dsphere en serie temporal, campo común (area)", () =>
  bd.ts_area.createIndex({ area: "2dsphere" })
);

// 1b) Lo mismo, pero con un PUNTO. El error del caso 1 dice que las series temporales
//     solo aceptan puntos, así que este caso separa "polígono" de "campo común".
probar("1b. Índice 2dsphere en serie temporal, campo común con un PUNTO (ubicacion)", () =>
  bd.ts_punto.createIndex({ ubicacion: "2dsphere" })
);

// 2) Índice 2dsphere en una serie temporal, sobre un campo dentro de meta
probar("2. Índice 2dsphere en serie temporal, dentro de meta (meta.ubicacion)", () =>
  bd.ts_meta.createIndex({ "meta.ubicacion": "2dsphere" })
);

// 3) Índice 2dsphere en una colección común (punto de comparación)
probar("3. Índice 2dsphere en colección común (area)", () =>
  bd.comun_area.createIndex({ area: "2dsphere" })
);

// --- Consultar ---

// 4) $geoIntersects (técnica de Q4) en colección común: ¿qué eventos contienen este punto?
probar("4. $geoIntersects en colección común", () =>
  bd.comun_area.find({ area: { $geoIntersects: { $geometry: punto_dentro } } }).toArray().length
);

// 5) $geoIntersects en la serie temporal. OJO: si el caso 1 falló, esta colección no tiene
//    índice geoespacial y la consulta recorre todo (no usa índice).
probar("5. $geoIntersects en serie temporal (sin índice si el caso 1 falló)", () =>
  bd.ts_area.find({ area: { $geoIntersects: { $geometry: punto_dentro } } }).toArray().length
);

// 6) $geoNear (técnica de Q3) en la serie temporal con el índice dentro de meta:
//    ¿cuáles son los nodos más cercanos a un punto? Devuelve nodo y distancia en metros.
probar("6. $geoNear en serie temporal (índice en meta.ubicacion)", () =>
  bd.ts_meta.aggregate([
    { $geoNear: { near: punto_dentro, distanceField: "distancia_m", key: "meta.ubicacion" } },
    { $limit: 2 },
  ]).toArray().map(d => ({ nodo: d.meta.nodo_id, distancia_m: Math.round(d.distancia_m) }))
);

// 7) $geoNear en una colección común: punto de comparación. ¿Devuelve la distancia?
//    (En el caso 6 el campo distancia_m no apareció en la serie temporal.)
bd.comun_nodos.createIndex({ ubicacion: "2dsphere" });
probar("7. $geoNear en colección común (para comparar con el caso 6)", () =>
  bd.comun_nodos.aggregate([
    { $geoNear: { near: punto_dentro, distanceField: "distancia_m" } },
    { $limit: 2 },
  ]).toArray().map(d => ({ nodo: d.nodo_id, distancia_m: Math.round(d.distancia_m) }))
);

// Índices que quedaron creados en cada colección
print("---");
for (const nombre of ["ts_area", "ts_punto", "ts_meta", "comun_area", "comun_nodos"]) {
  print("Índices de " + nombre + ": " + bd.getCollection(nombre).getIndexes().map(i => i.name).join(", "));
}
