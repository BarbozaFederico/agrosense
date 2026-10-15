// Spike de esquemas · Prueba 3
// Pregunta: si una serie temporal no admite validador (prueba 2), ¿se puede usar el
// mismo $jsonSchema como FILTRO de búsqueda para encontrar lecturas mal formadas?
// Es la "consulta de auditoría" (opción B del spike de esquemas).
//
// Cómo correrlo (desde la raíz del repo):
//   mongosh --file scripts/spike-esquemas/03_auditoria_serie_temporal.js
//
// Usa la base de PRUEBA `agrosense_tests`, que se borra al empezar.

const bd = db.getSiblingDB("agrosense_tests");
bd.dropDatabase();

// Mismo esquema de las pruebas 1 y 2 (con _id declarado).
const esquema = {
  bsonType: "object",
  required: ["ts", "meta", "temperatura_c", "humedad_suelo_pct", "humedad_aire_pct"],
  additionalProperties: false,
  properties: {
    _id: { bsonType: "objectId" },
    ts: { bsonType: "date" },
    meta: {
      bsonType: "object",
      required: ["nodo_id", "parcela_id", "finca_id", "fuente"],
      additionalProperties: false,
      properties: {
        nodo_id: { bsonType: "string" },
        parcela_id: { bsonType: "string" },
        finca_id: { bsonType: "string" },
        fuente: { enum: ["simulado", "simulacion_en_vivo"] },
        escenario_id: { bsonType: "string" }
      }
    },
    temperatura_c: { bsonType: ["double", "int"] },
    humedad_suelo_pct: { bsonType: ["double", "int"] },
    humedad_aire_pct: { bsonType: ["double", "int"] }
  }
};

// Serie temporal SIN validador (es lo único que permite MongoDB 9.0.2).
bd.createCollection("lecturas", {
  timeseries: { timeField: "ts", metaField: "meta", granularity: "minutes" }
});
const info = bd.getCollectionInfos({ name: "lecturas" })[0];
print("Versión del servidor:", db.version(), "| tipo de colección:", info.type);
print("---");

// Cargamos los mismos 7 documentos de las pruebas anteriores. Cada uno lleva una
// etiqueta en `caso` para saber cuál es cuál... pero `caso` sería un campo de más.
// Por eso la etiqueta va en la hora: cada documento tiene un minuto distinto.
const meta = { nodo_id: "N-SR-1-A", parcela_id: "P-SR-1", finca_id: "F-SR", fuente: "simulado" };
const hora = m => new Date(Date.UTC(2026, 8, 14, 9, m));   // 14/9/2026 09:0m UTC
const casos = {
  1: "Válido",
  2: "Campo de más (viento_kmh)",
  3: "Error de tipeo (temperatua_c)",
  4: "Campo de más dentro de meta (color)",
  5: "Tipo equivocado (temperatura_c como texto)",
  6: "Falta un campo obligatorio (humedad_aire_pct)",
  7: "Simulación en vivo con escenario_id en meta"
};
bd.lecturas.insertMany([
  { ts: hora(1), meta, temperatura_c: -1.8, humedad_suelo_pct: 23.4, humedad_aire_pct: 81 },
  { ts: hora(2), meta, temperatura_c: -1.8, humedad_suelo_pct: 23.4, humedad_aire_pct: 81, viento_kmh: 3 },
  { ts: hora(3), meta, temperatua_c: -1.8, humedad_suelo_pct: 23.4, humedad_aire_pct: 81 },
  { ts: hora(4), meta: { ...meta, color: "rojo" }, temperatura_c: -1.8, humedad_suelo_pct: 23.4, humedad_aire_pct: 81 },
  { ts: hora(5), meta, temperatura_c: "-1.8", humedad_suelo_pct: 23.4, humedad_aire_pct: 81 },
  { ts: hora(6), meta, temperatura_c: -1.8, humedad_suelo_pct: 23.4 },
  { ts: hora(7), meta: { ...meta, fuente: "simulacion_en_vivo", escenario_id: "demo-1" }, temperatura_c: -3.0, humedad_suelo_pct: 23.4, humedad_aire_pct: 85 },
]);
print("Lecturas cargadas (sin validación):", bd.lecturas.countDocuments());
print("---");

function probar(descripcion, accion) {
  try {
    print("OK    | " + descripcion + " | " + JSON.stringify(accion()));
  } catch (e) {
    print("ERROR | " + descripcion + " | " + e.message.slice(0, 120));
  }
}
const casosDe = docs => docs.map(d => d.ts.getUTCMinutes() + ". " + casos[d.ts.getUTCMinutes()]);

// 1) ¿Qué lecturas CUMPLEN el esquema? (esperado: casos 1 y 7)
probar("1. find({ $jsonSchema }) → lecturas que cumplen", () =>
  casosDe(bd.lecturas.find({ $jsonSchema: esquema }).sort({ ts: 1 }).toArray())
);

// 2) ¿Qué lecturas NO cumplen? Es la consulta de auditoría (esperado: casos 2 a 6)
probar("2. find({ $nor: [{ $jsonSchema }] }) → lecturas mal formadas", () =>
  casosDe(bd.lecturas.find({ $nor: [{ $jsonSchema: esquema }] }).sort({ ts: 1 }).toArray())
);

// 3) Lo mismo dentro de una agregación ($match), contando cuántas fallan
probar("3. aggregate $match + $count → cantidad de lecturas mal formadas", () =>
  bd.lecturas.aggregate([
    { $match: { $nor: [{ $jsonSchema: esquema }] } },
    { $count: "mal_formadas" }
  ]).toArray()
);

// 4) Auditoría combinada con un filtro común (por nodo y rango de fechas), como se usaría en la práctica
probar("4. Auditoría filtrando por nodo y rango de fechas", () =>
  bd.lecturas.countDocuments({
    "meta.nodo_id": "N-SR-1-A",
    ts: { $gte: hora(0), $lt: hora(10) },
    $nor: [{ $jsonSchema: esquema }]
  })
);

// 5) Borrar las lecturas mal formadas con el mismo filtro (posible "limpieza")
probar("5. deleteMany con $nor + $jsonSchema", () =>
  bd.lecturas.deleteMany({ $nor: [{ $jsonSchema: esquema }] })
);
print("Lecturas que quedan después de limpiar:", bd.lecturas.countDocuments(),
      "→", JSON.stringify(casosDe(bd.lecturas.find().sort({ ts: 1 }).toArray())));
