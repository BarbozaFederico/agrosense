# Seed base

**Estado:** parcial (16/10/2026). Decisiones en [ADR-010](decisions/ADR-010-seed-base.md). Modelo en [`modelo-datos.md`](modelo-datos.md).

## Qué carga

| Colección | Documentos | Notas |
|---|---|---|
| `configuracion` | 1 | Δ, nodo inactivo, límites de "sospechoso", noche extrema, cortes del índice, umbrales de riego |
| `variedades` | 1 | Malbec, con 13 etapas BBCH continuas de 0 a 99 |
| `fincas` | 3 | `F-SR`, `F-SM`, `F-TU` (ficticias) |
| `parcelas` | 6 | 2 ha cada una, Malbec |
| `nodos` | 12 | 2 por parcela, dentro de su parcela |
| `eventos_climaticos` | 1 | Helada de la noche extrema (San Rafael) |

No incluye todavía las observaciones fenológicas ni las horas definitivas de la noche extrema: dependen de las lecturas del simulador.

## Cómo se usa

Desde la raíz, con el entorno virtual activado:

```bash
python -m db.seeds.cargar
```

Se puede repetir: borra y vuelve a insertar solo lo del seed. No toca `lecturas`, `alertas`, `riegos` ni `observaciones_fenologicas`. Si una validación falla, termina con código 1 sin escribir nada.

**Hoy no puede cargar `configuracion`:** `db/seeds/umbrales_riego.py` está en `None` hasta verificar la Tabla 19 de la FAO-56. El cargador se detiene con un mensaje claro y no escribe nada.

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `db/seeds/cargar.py` | Cargador: arma, valida, carga y comprueba la geografía |
| `db/seeds/ubicaciones.py`, `geometria.py` | Medidas y centros ficticios; de acá salen las geometrías |
| `db/seeds/fincas.py`, `parcelas.py`, `nodos.py`, `variedades.py`, `configuracion.py`, `eventos_climaticos.py` | Datos de cada colección, con la fuente y la marca (supuesto, con fuente) de cada valor |
| `db/seeds/umbrales_riego.py` | Umbrales de riego, pendientes |

## Qué comprueba el cargador

1. Cada colección cumple su `$jsonSchema` (validación sin guardar).
2. `verificar_coherencia` de `configuracion` (límites, ventana y piso de la noche extrema).
3. Las etapas de la variedad cubren BBCH 0 a 99 sin huecos y con grados-día crecientes.
4. Las referencias existen (parcela → finca y variedad, nodo → parcela y finca).
5. Después de cargar, con consultas geoespaciales de MongoDB: cada nodo está dentro de su parcela y cada parcela dentro de su finca.

## Resultado de las pruebas (base `agrosense_tests`)

Con umbrales de riego de prueba (no verificados, solo para ejercitar el flujo):

- Primera corrida: 1 + 1 + 3 + 6 + 12 + 1 documentos válidos e insertados; geografía OK.
- Segunda corrida: mismos conteos (1, 1, 3, 6, 12, 1 borrados y reinsertados); geografía OK.
- Sin umbrales: termina con código 1 y no crea nada.
- Casos negativos detectados: hueco en las etapas, nodo con la finca de otra parcela, noche extrema en una finca sin límite, nodo fuera de su parcela.
- Una parcela mide 141,5 × 141,4 m (2,00 ha). El evento de la noche extrema toca `P-SR-1` y `P-SR-2` y ninguna otra parcela.

## Supuestos y pendientes

- Coordenadas de los centros de las fincas: ficticias, a validar que caigan dentro de cada departamento.
- Altitudes: las de las estaciones de referencia, aproximadas.
- Conducción (espaldero), densidad (4.000 plantas/ha) y superficie (2 ha): supuestos.
- Corte de 35 grados-día entre yema dormida e hinchada y 70 hasta la brotación: supuestos (ADR-010).
- Grados-día de las etapas intermedias: supuestos e interpolación; con fuente solo 260 (floración) y 972 (envero).
- Límite de "sospechoso" de Tupungato: `None`, a validar (ADR-009).
- Piso de −6,3 °C de la noche extrema: supuesto, a validar.
- `umbrales_riego`: pendientes de la Tabla 19 de la FAO-56.
