# ADR-010: Organización y criterios del seed base

**Estado:** Aceptado (16/10/2026). Usa el modelo de [`modelo-datos.md`](../modelo-datos.md) y los parámetros de [ADR-005](ADR-005-parametros-simulacion.md) y [ADR-009](ADR-009-temperatura-sospechosa-y-noche-extrema.md).

## Contexto

Antes del simulador hace falta cargar los datos que no cambian durante la temporada: `fincas`, `parcelas`, `nodos`, `variedades`, `configuracion`, `observaciones_fenologicas` y el evento climático de la noche extrema. Las alertas, los riegos y las lecturas los genera el simulador.

## Decisiones

| # | Tema | Elegida | Descartadas |
|---|---|---|---|
| 1 | Código del seed | **Un cargador único** (`python -m db.seeds.cargar`) y **un módulo de datos por colección** en `db/seeds/`. Valida cada colección con `validar_documentos`, llama a `verificar_coherencia` y se puede repetir | Un script por colección (orden de ejecución a mano, coherencia dispersa); un solo archivo (largo y difícil de revisar) |
| 2 | Geometrías | **Rectángulos calculados desde un centro ficticio**: cada parcela mide unas 2 ha (~141 × 141 m), la finca es el rectángulo que envuelve sus 2 parcelas y los nodos caen dentro de su parcela | Polígonos irregulares escritos a mano (más trabajo y riesgo de nodos fuera de su parcela) |
| 3 | Etapas previas a la brotación | **Etapas BBCH continuas de 0 a 99.** Los 70 grados-día desde el 1/9 hasta la brotación se parten a la mitad: yema dormida de 0 a 35 y yema hinchada de 35 a 70. Las etapas sin umbral con fuente llevan `umbral_helada_c: null` | Solo las 7 etapas con umbral (huecos en Q9); pre-brotación como una sola etapa (pierde el −10,6 °C documentado) |

## Supuestos que introduce (a validar)

- El corte de 35 grados-día entre yema dormida e yema hinchada es **supuesto**: ninguna fuente lo da. Los 70 grados-día hasta la brotación ya eran un supuesto (`vid-malbec.md`, calibrado con Chacras de Coria).
- Las coordenadas de las fincas son **ficticias**: no representan fincas reales.

## Consecuencias

- El corte decide cuántas noches de setiembre generan alerta. Con el sensor en −4,5 °C (San Rafael) el brote queda en −6,5 °C: cruza el umbral de yema hinchada (−6,1 °C) pero no el de yema dormida (−10,6 °C). En San Martín (−2,8 °C en el sensor, −4,8 °C en el brote) ninguna etapa previa a la brotación genera alerta. El simulador tiene que planificar las noches de helada según la etapa de cada parcela.
- **Observaciones fenológicas y horas de la noche extrema quedan para el simulador:** las observaciones tienen que ser coherentes con las temperaturas simuladas, y las horas exactas de la noche extrema se comprueban con Q9 sobre las lecturas (ADR-009, decisión 8). Hasta entonces la ventana es provisoria: 5/10/2026, 06:00 a 11:00 UTC.
- El evento de la noche extrema tiene un `_id` fijo (`ObjectId` inventado) para que el seed dé siempre el mismo resultado y para validarlo antes de insertar.
- **`umbrales_riego` se resolvieron en [ADR-011](ADR-011-umbrales-de-riego.md):** la Tabla 19 está en el capítulo 7 del HTML de la FAO-56 (no en el 8, donde se buscó primero).
