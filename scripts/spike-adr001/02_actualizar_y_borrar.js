// Spike ADR-001 · Prueba 2
// Pregunta: ¿qué se puede actualizar y qué se puede borrar en una serie temporal?
// Importa para RF-15 ("Reiniciar demo"): hay que poder borrar lo que generó una simulación en vivo.
//
// Cómo correrlo (desde la raíz del repo):
//   mongosh --file scripts/spike-adr001/02_actualizar_y_borrar.js
//
// Usa la base de PRUEBA `spike_agrosense`. No toca ninguna base real.
// Cada caso arranca desde cero (preparar()) para que no se mezclen entre sí.

const bd = db.getSiblingDB("spike_agrosense");

// Deja la colección en un estado conocido: 3 lecturas normales y 2 de una "simulación en vivo".
// La simulación en vivo se marca con escenario_id DENTRO de meta (decisión a validar con esta prueba).
function preparar() {
  bd.dropDatabase();
  bd.createCollection("lecturas", {
    timeseries: { timeField: "ts", metaField: "meta", granularity: "minutes" }
  });
  bd.lecturas.insertMany([
    { ts: new Date("2026-10-13T03:00:00Z"), meta: { nodo_id: "N-01", parcela_id: "P-1", finca_id: "F-1" }, temperatura: -0.4 },
    { ts: new Date("2026-10-13T03:05:00Z"), meta: { nodo_id: "N-01", parcela_id: "P-1", finca_id: "F-1" }, temperatura: -0.8 },
    { ts: new Date("2026-10-13T03:00:00Z"), meta: { nodo_id: "N-02", parcela_id: "P-1", finca_id: "F-1" }, temperatura: -0.2 },
    // Lecturas de una simulación en vivo (se marcan con escenario_id)
    { ts: new Date("2026-10-13T04:00:00Z"), meta: { nodo_id: "N-01", parcela_id: "P-1", finca_id: "F-1", escenario_id: "demo-1" }, temperatura: -3.0 },
    { ts: new Date("2026-10-13T04:05:00Z"), meta: { nodo_id: "N-01", parcela_id: "P-1", finca_id: "F-1", escenario_id: "demo-1" }, temperatura: -3.2 },
  ]);
}

// Ejecuta un caso: prepara la colección, corre la acción y muestra OK o ERROR.
// Si MongoDB rechaza la operación, el catch captura el error y el script sigue con el próximo caso.
function probar(descripcion, accion) {
  preparar();
  try {
    const resultado = accion();
    print("OK    | " + descripcion + " | resultado: " + JSON.stringify(resultado) +
          " | quedan " + bd.lecturas.countDocuments() + " documentos");
  } catch (e) {
    print("ERROR | " + descripcion + " | " + e.message);
  }
}

print("Versión del servidor:", db.version());
print("---");

// 1) Actualizar un valor medido de una lectura puntual (filtro: nodo + hora exacta)
probar("1. Actualizar temperatura de una lectura puntual", () =>
  bd.lecturas.updateOne(
    { "meta.nodo_id": "N-01", ts: new Date("2026-10-13T03:00:00Z") },
    { $set: { temperatura: -9.9 } }
  )
);

// 1b) Lo mismo, pero con updateMany. El error del caso 1 habla de una actualización "non-multi"
//     (updateOne), así que este caso separa dos preguntas: ¿falla por usar updateOne,
//     o falla por querer modificar un valor medido?
probar("1b. Actualizar temperatura con updateMany (nodo + hora exacta)", () =>
  bd.lecturas.updateMany(
    { "meta.nodo_id": "N-01", ts: new Date("2026-10-13T03:00:00Z") },
    { $set: { temperatura: -9.9 } }
  )
);

// 1c) El error del caso 1b habla de filtrar por un campo que no es el metaField (usamos `ts`).
//     Acá el filtro usa SOLO meta, pero lo que se modifica sigue siendo un valor medido.
probar("1c. Actualizar temperatura con filtro solo por meta (todo el nodo N-01)", () =>
  bd.lecturas.updateMany(
    { "meta.nodo_id": "N-01" },
    { $set: { temperatura: -9.9 } }
  )
);

// 2) Actualizar un campo dentro de meta, para todo un nodo
probar("2. Cambiar meta.parcela_id de todo el nodo N-02", () =>
  bd.lecturas.updateMany(
    { "meta.nodo_id": "N-02" },
    { $set: { "meta.parcela_id": "P-2" } }
  )
);

// 3) Borrar por un campo de meta: es lo que usaría "Reiniciar demo"
probar("3. Borrar por meta.escenario_id", () =>
  bd.lecturas.deleteMany({ "meta.escenario_id": "demo-1" })
);

// 4) Borrar por rango de fechas
probar("4. Borrar lecturas anteriores a las 03:05", () =>
  bd.lecturas.deleteMany({ ts: { $lt: new Date("2026-10-13T03:05:00Z") } })
);

// 5) Borrar por un valor medido (un campo común, no meta ni ts)
probar("5. Borrar lecturas con temperatura menor a -1", () =>
  bd.lecturas.deleteMany({ temperatura: { $lt: -1 } })
);

// 6) Borrar una sola lectura (nodo + hora exacta)
probar("6. Borrar una sola lectura (deleteOne)", () =>
  bd.lecturas.deleteOne({ "meta.nodo_id": "N-02", ts: new Date("2026-10-13T03:00:00Z") })
);

// 7) Borrar todo con filtro vacío
probar("7. Borrar todo (deleteMany con filtro vacío)", () =>
  bd.lecturas.deleteMany({})
);
