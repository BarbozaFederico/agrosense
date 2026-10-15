// Spike de esquemas · Prueba 2
// Pregunta: la prueba 1 mostró que MongoDB 9.0.2 no acepta crear una serie temporal
// con `validator` en el mismo createCollection. ¿Se puede agregar el validador
// después, con collMod? ¿Funciona el esquema cerrado?
//
// Cómo correrlo (desde la raíz del repo):
//   mongosh --file scripts/spike-esquemas/02_validador_serie_temporal.js
//
// Usa la base de PRUEBA `agrosense_tests`, que se borra al empezar.

const bd = db.getSiblingDB("agrosense_tests");
bd.dropDatabase();

// Mismo esquema de la prueba 1, con o sin _id declarado.
function esquemaLectura(incluirId) {
  const properties = {
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
  };
  if (incluirId) properties._id = { bsonType: "objectId" };
  return {
    bsonType: "object",
    required: ["ts", "meta", "temperatura_c", "humedad_suelo_pct", "humedad_aire_pct"],
    additionalProperties: false,
    properties
  };
}

// Paso 1: crear la serie temporal SIN validador. Paso 2: agregarlo con collMod.
function crearConCollMod(nombre, incluirId) {
  try {
    bd.createCollection(nombre, {
      timeseries: { timeField: "ts", metaField: "meta", granularity: "minutes" }
    });
    print("OK    | crear serie temporal " + nombre);
  } catch (e) {
    print("ERROR | crear " + nombre + " | " + e.message);
    return;
  }
  try {
    bd.runCommand({
      collMod: nombre,
      validator: { $jsonSchema: esquemaLectura(incluirId) },
      validationLevel: "strict",
      validationAction: "error"
    });
    // runCommand no lanza error por sí solo: hay que mirar el resultado.
    const info = bd.getCollectionInfos({ name: nombre })[0];
    print((info.options.validator ? "OK    " : "ERROR ") + "| collMod " + nombre +
          " | tipo: " + info.type + " | validador guardado: " + !!info.options.validator);
  } catch (e) {
    print("ERROR | collMod " + nombre + " | " + e.message);
  }
}

function probar(coleccion, descripcion, doc) {
  try {
    bd.getCollection(coleccion).insertOne(doc);
    print("ENTRA     | " + coleccion + " | " + descripcion);
  } catch (e) {
    print("RECHAZADO | " + coleccion + " | " + descripcion + " | " + e.message.slice(0, 90));
  }
}

const meta = { nodo_id: "N-SR-1-A", parcela_id: "P-SR-1", finca_id: "F-SR", fuente: "simulado" };
const ts = new Date("2026-09-14T09:00:00Z");
const valido       = { ts, meta, temperatura_c: -1.8, humedad_suelo_pct: 23.4, humedad_aire_pct: 81 };
const campoExtra   = { ts, meta, temperatura_c: -1.8, humedad_suelo_pct: 23.4, humedad_aire_pct: 81, viento_kmh: 3 };
const errorTipeo   = { ts, meta, temperatua_c: -1.8, humedad_suelo_pct: 23.4, humedad_aire_pct: 81 };
const metaExtra    = { ts, meta: { ...meta, color: "rojo" }, temperatura_c: -1.8, humedad_suelo_pct: 23.4, humedad_aire_pct: 81 };
const tipoErroneo  = { ts, meta, temperatura_c: "-1.8", humedad_suelo_pct: 23.4, humedad_aire_pct: 81 };
const sinCampo     = { ts, meta, temperatura_c: -1.8, humedad_suelo_pct: 23.4 };
const conEscenario = { ts, meta: { ...meta, fuente: "simulacion_en_vivo", escenario_id: "demo-1" }, temperatura_c: -3.0, humedad_suelo_pct: 23.4, humedad_aire_pct: 85 };

print("Versión del servidor:", db.version());
print("---");
crearConCollMod("ts_sin_id", false);
crearConCollMod("ts_con_id", true);
print("---");

for (const c of ["ts_sin_id", "ts_con_id"]) {
  probar(c, "1. Documento válido", valido);
  probar(c, "2. Campo de más (viento_kmh)", campoExtra);
  probar(c, "3. Error de tipeo (temperatua_c)", errorTipeo);
  probar(c, "4. Campo de más dentro de meta (color)", metaExtra);
  probar(c, "5. Tipo equivocado (temperatura_c como texto)", tipoErroneo);
  probar(c, "6. Falta un campo obligatorio (humedad_aire_pct)", sinCampo);
  probar(c, "7. Simulación en vivo con escenario_id en meta", conEscenario);
  print("---");
}

// insertMany: así va a cargar el simulador. ¿Un documento malo frena todo el lote?
probar_lote();
function probar_lote() {
  const antes = bd.ts_con_id.countDocuments();
  try {
    bd.ts_con_id.insertMany([valido, campoExtra, valido], { ordered: false });
    print("LOTE | entraron todos");
  } catch (e) {
    print("LOTE | error en el lote: " + e.message.slice(0, 60));
  }
  print("LOTE | insertMany de 3 (1 inválido, ordered: false): entraron " +
        (bd.ts_con_id.countDocuments() - antes));
}

print("---");
for (const c of ["ts_sin_id", "ts_con_id"]) {
  print("Documentos guardados en " + c + ": " + bd.getCollection(c).countDocuments());
}
