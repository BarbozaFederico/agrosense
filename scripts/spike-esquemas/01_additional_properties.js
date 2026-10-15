// Spike de esquemas · Prueba 1
// Pregunta: ¿funciona un $jsonSchema cerrado (additionalProperties: false) en una
// serie temporal? ¿Y el _id que agrega MongoDB solo?
// Importa para ADR-006 (validación estricta: validationAction "error" y esquema cerrado).
//
// Cómo correrlo (desde la raíz del repo):
//   mongosh --file scripts/spike-esquemas/01_additional_properties.js
//
// Usa la base de PRUEBA `agrosense_tests`, que se borra al empezar. No toca la base real.
// Los valores son inventados, solo para probar.

const bd = db.getSiblingDB("agrosense_tests");
bd.dropDatabase();

// --- Esquema de una lectura (simplificado del modelo-datos.md, sección 3.4) ---
// incluirId: si es true, declara _id en properties; si es false, no lo declara.
function esquemaLectura(incluirId) {
  const properties = {
    ts: { bsonType: "date" },
    meta: {
      bsonType: "object",
      required: ["nodo_id", "parcela_id", "finca_id", "fuente"],
      additionalProperties: false,          // meta también cerrado
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

// Crea una colección (serie temporal o común) con el esquema indicado.
function crear(nombre, serieTemporal, incluirId) {
  const opciones = {
    validator: { $jsonSchema: esquemaLectura(incluirId) },
    validationLevel: "strict",
    validationAction: "error"
  };
  if (serieTemporal) {
    opciones.timeseries = { timeField: "ts", metaField: "meta", granularity: "minutes" };
  }
  try {
    bd.createCollection(nombre, opciones);
    print("OK    | crear " + nombre);
  } catch (e) {
    print("ERROR | crear " + nombre + " | " + e.message);
  }
}

// Inserta un documento y muestra si entró o fue rechazado.
function probar(coleccion, descripcion, doc) {
  try {
    bd.getCollection(coleccion).insertOne(doc);
    print("ENTRA     | " + coleccion + " | " + descripcion);
  } catch (e) {
    // El mensaje de MongoDB es largo; mostramos solo la primera parte.
    print("RECHAZADO | " + coleccion + " | " + descripcion + " | " + e.message.slice(0, 90));
  }
}

const meta = { nodo_id: "N-SR-1-A", parcela_id: "P-SR-1", finca_id: "F-SR", fuente: "simulado" };
const ts = new Date("2026-09-14T09:00:00Z");

// Documentos de prueba
const valido       = { ts, meta, temperatura_c: -1.8, humedad_suelo_pct: 23.4, humedad_aire_pct: 81 };
const campoExtra   = { ts, meta, temperatura_c: -1.8, humedad_suelo_pct: 23.4, humedad_aire_pct: 81, viento_kmh: 3 };
const errorTipeo   = { ts, meta, temperatua_c: -1.8, humedad_suelo_pct: 23.4, humedad_aire_pct: 81 };
const metaExtra    = { ts, meta: { ...meta, color: "rojo" }, temperatura_c: -1.8, humedad_suelo_pct: 23.4, humedad_aire_pct: 81 };
const tipoErroneo  = { ts, meta, temperatura_c: "-1.8", humedad_suelo_pct: 23.4, humedad_aire_pct: 81 };
const sinCampo     = { ts, meta, temperatura_c: -1.8, humedad_suelo_pct: 23.4 };
const conEscenario = { ts, meta: { ...meta, fuente: "simulacion_en_vivo", escenario_id: "demo-1" }, temperatura_c: -3.0, humedad_suelo_pct: 23.4, humedad_aire_pct: 85 };

print("Versión del servidor:", db.version());
print("---");

// Cuatro variantes: serie temporal / común, con y sin _id declarado
crear("ts_sin_id", true, false);
crear("ts_con_id", true, true);
crear("comun_sin_id", false, false);
crear("comun_con_id", false, true);
print("---");

for (const c of ["ts_sin_id", "ts_con_id", "comun_sin_id", "comun_con_id"]) {
  probar(c, "1. Documento válido", valido);
  probar(c, "2. Campo de más (viento_kmh)", campoExtra);
  probar(c, "3. Error de tipeo (temperatua_c)", errorTipeo);
  probar(c, "4. Campo de más dentro de meta (color)", metaExtra);
  probar(c, "5. Tipo equivocado (temperatura_c como texto)", tipoErroneo);
  probar(c, "6. Falta un campo obligatorio (humedad_aire_pct)", sinCampo);
  probar(c, "7. Simulación en vivo con escenario_id en meta", conEscenario);
  print("---");
}

// ¿El validador quedó guardado en la serie temporal?
const info = bd.getCollectionInfos({ name: "ts_con_id" })[0];
print("Opciones guardadas en ts_con_id:");
printjson({ validationLevel: info.options.validationLevel, validationAction: info.options.validationAction,
            tieneValidador: !!info.options.validator });
print("Documentos guardados por colección:");
for (const c of ["ts_sin_id", "ts_con_id", "comun_sin_id", "comun_con_id"]) {
  print("  " + c + ": " + bd.getCollection(c).countDocuments());
}
