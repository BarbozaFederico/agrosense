# ADR-020: Tercera pantalla del dashboard, "Alertas"

**Estado:** Aceptado (22/10/2026). Requisitos RF-04, RF-11 y RF-12. Continúa [ADR-018](ADR-018-resumen-de-la-manana.md) y [ADR-019](ADR-019-detalle-de-parcela.md) (mismo mundo visual, mismo "ahora" y misma navegación) y reemplaza el apartado 3.3 de [`ux/pantallas.md`](../ux/pantallas.md). Los roles y la autenticación siguen reservados para el ADR-017.

## Contexto

La tercera pantalla de `pantallas.md` es "Alertas": qué alertas hubo, el historial y las heladas por departamento y semana. La usa el encargado o el técnico después de ver el resumen. Al diseñarla apareció un problema de significado: las 35 alertas de la base (10 de helada y 25 de riego) están **todas cerradas**, y las de helada terminan antes de las 09:00, así que a las 12:00 (el "ahora" de la app, ADR-018) casi nunca hay una abierta. Una lista de "activas" en sentido estricto quedaría vacía casi siempre. Se acordó con el equipo el significado de "activas", si entran las de riego y cómo se muestra Q8 (filas 1 a 3).

## Decisiones

| # | Tema | Decisión | Descartadas |
|---|---|---|---|
| 1 | Qué son las "activas" | Las **alertas de la noche elegida**: las que se solapan con la ventana de 18:00 a 12:00 de esa fecha, abiertas o cerradas. Una alerta sin `fin` al cierre se marca "en curso" (barra abierta y un `+` en la duración). Es la misma noche del Resumen y del Detalle, y hay algo para mostrar en las 5 noches con helada | Solo las abiertas a las 12:00 (casi siempre vacía y hay que explicarlo); un selector de hora dentro de la noche (suma un control y estado) |
| 2 | Tipos | **Helada y riego**, con un control "Todas / Helada / Riego" (`st.segmented_control`, `required=True`) que filtra la lista y el historial. La de riego muestra la humedad de suelo mínima contra el umbral del suelo (2 decimales: el valor extremo suele quedar a centésimas del umbral), con un triángulo ámbar y la barra en ámbar. El resumen semanal es siempre de helada | Solo helada (deja fuera de la interfaz 25 alertas que existen en la base) |
| 3 | Pantalla | Frase de estado ("2 alertas de helada esta noche, en Finca Los Álamos (San Rafael)", con la más fuerte y su duración), **tabla de la noche** con la barra de tiempo de ADR-018, **historial** de la temporada y **resumen semanal**. Filtro de finca en la barra lateral ("Todas" por defecto). El nombre de la parcela enlaza al detalle con la fecha | Tarjetas por alerta (no se comparan) |
| 4 | Orden | Primero las de helada y, dentro de cada tipo, la que más pasó su umbral (`valor_extremo − umbral`, la más negativa primero) | Por hora (no dice cuál mirar primero) |
| 5 | Historial | Tabla nativa y ordenable (`st.dataframe` con `column_config`) de las alertas que empezaron antes del cierre de la noche elegida, las más recientes primero, hasta 200. Trae tipo, parcela y finca, etapa, inicio, fin, duración, valor extremo, umbral y estado. El valor extremo y el umbral van como **texto con su unidad**: dos columnas numéricas (una por unidad) dejaban "None" en la mitad de las celdas y ordenar valores de unidades distintas no tiene sentido | Dos columnas numéricas °C y % (celdas vacías); una tabla HTML propia (pierde el orden por columna) |
| 6 | Resumen semanal (Q8) | **Tabla semana × departamento**: filas = semanas con helada, columnas = los departamentos (o solo el de la finca elegida), con la cantidad de alertas y la mínima del brote. La semana de la fecha elegida va resaltada. Q8 se usa **tal cual**, es decir, de toda la temporada: no se le agregó un parámetro de fecha para no cambiar una consulta ya probada | Barras apiladas (ocultan la mínima y con 3 semanas con datos aportan poco) |
| 7 | Etapa por nombre | Las alertas guardan solo `etapa_bbch` (ADR-006). El nombre se busca en las etapas de la variedad (`variedades`, Malbec) con `nombre_de_etapa`; un BBCH sin etapa conocida se muestra como "BBCH n" | Guardar el nombre en la alerta (cambia el modelo por un dato que se calcula) |
| 8 | Consultas | Se reutiliza Q8. Se agrega `db/queries/alertas_pantalla.py` con tres consultas de apoyo que **no son Q11**: `alertas_de_la_noche`, `historial` y `etapas_del_malbec`. Los nombres de parcela y finca salen del catálogo (ADR-003: las alertas solo guardan la parcela). Los textos y el HTML van en `dashboard/piezas_alertas.py`, sin Streamlit ni MongoDB | Un `$lookup` a parcelas y fincas en cada consulta (el catálogo ya se lee para las otras pantallas) |

## Consecuencias

- **Falta 1 pantalla** (estado de nodos). Se agregó a `app.py` y a `lateral.PANTALLAS_HECHAS`.
- La frase "esta noche" y el filtro de tipo se evalúan sobre la noche, y el contador de la derecha ("N alertas en la temporada hasta el dd/mm/aaaa") sobre el historial con los mismos filtros.
- El historial recorta a 200 alertas. La temporada simulada tiene 35, pero con más sensores el recorte importaría; el límite es una constante (`HISTORIAL_MAXIMO`).
- Pruebas: `python -m dashboard.probar_alertas` (44 casos: datos, textos, filtros, historial, semanas y consultas de apoyo) y 13 casos nuevos de punta a punta en `python -m dashboard.probar_pantallas` (36 en total). Verificado en el navegador a 1440 px de ancho. Falta la prueba con el wifi apagado y en pantallas angostas.
