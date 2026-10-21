# ADR-016: Backup y restauración con mongodump y mongorestore

**Estado:** Aceptado (21/10/2026). Requisitos RNF-02 y RNF-03. Procedimiento y prueba en [`backup-restore.md`](../backup-restore.md). Los usuarios y roles (RNF-04) van en un cambio aparte, que será el ADR-017.

## Contexto

La materia pide una política de resguardo con un script reproducible y una restauración probada. La base `agrosense` pesa unos 3 MB en disco (727.980 lecturas en una serie temporal), corre en una instancia sola de MongoDB 9.0.2, sin réplicas ni oplog, y el repositorio es público: ningún respaldo puede terminar en él (RNF-07). Antes de decidir se comprobó con un experimento que `mongodump` y `mongorestore` manejan bien la serie temporal `lecturas`.

## Decisiones

| # | Tema | Decisión | Descartadas |
|---|---|---|---|
| 1 | Herramientas | `mongodump` y `mongorestore` de MongoDB Database Tools 100.19.1 (instaladas con `winget install MongoDB.DatabaseTools`). El instalador no las agrega al PATH: los scripts las buscan en `AGROSENSE_HERRAMIENTAS`, en el PATH y en `C:\Program Files\MongoDB\Tools\*\bin` | Copiar la carpeta de datos del servicio (no es portable y exige apagar `mongod`); respaldar con `pymongo` (se reinventa lo que ya hace la herramienta oficial) |
| 2 | Lenguaje | Python en `scripts/` (`python -m scripts.backup`, `scripts.restaurar`, `scripts.probar_respaldo`): llaman a las herramientas y verifican con `pymongo` | PowerShell o Bash (no corren en todos los sistemas y comparar datos entre dos bases queda torpe) |
| 3 | Qué se respalda | Solo la base `agrosense`, en **un archivo comprimido** (`--archive --gzip`). Los usuarios no se incluyen (se recrean con su propio script), para que los hashes de contraseñas nunca queden en un respaldo | Una carpeta con un `.bson` por colección (rotar y mover una carpeta es más torpe; ocupa 1,6 veces más: 4,1 MB contra 2,5 MB, medido el 21/10/2026); todo el servidor (mezcla bases ajenas y guarda hashes) |
| 4 | Dónde | Fuera del repositorio: `AGROSENSE_BACKUP_DIR` o `~/agrosense-backups`. El código **se niega** a guardar dentro del repo | Una carpeta `backups/` en el repo (ya está en `.gitignore`, pero un `git add -f` la subiría) |
| 5 | Política (**supuesto adoptado**) | Un backup por día a las 02:00. Se conserva la última copia de cada uno de los 7 días más recientes y la de los 4 últimos domingos; el resto se borra | Solo diario con 7 copias (un error que se descubre a los 8 días no tiene copia); semanal con 4 copias (perder hasta 7 días de lecturas de sensores que reportan cada 5 minutos es difícil de justificar) |
| 6 | Programación | El script hace el backup y la rotación. El comando de `schtasks` queda documentado, pero no se registra ninguna tarea en el Windows del equipo | Registrar la tarea (modifica el sistema, la notebook puede estar apagada a las 02:00 y la tarea necesitaría la clave guardada) |
| 7 | Manifiesto | Junto a cada backup, un `.manifiesto.json` con la huella `sha256`, el tamaño, la versión del servidor y, por colección, el tipo, los documentos, los nombres de índices y una huella del validador. Sin datos ni credenciales | Confiar solo en el archivo (no se sabría si cambió ni si la restauración quedó igual cuando la base original ya no exista) |
| 8 | Restauración | A una base **aparte** (`<base>_restaurada`). No pisa una base que ya existe salvo `--reemplazar`; antes de restaurar comprueba la huella; después compara contra el manifiesto, y con `--comparar-con` corre Q1, Q5, Q9 y Q10 en las dos bases | Restaurar siempre encima de la base viva (un error borra datos buenos); verificar solo los conteos (no prueba que índices, validadores y consultas sobrevivieron) |
| 9 | Serie temporal | Se respalda con la misma herramienta: `mongodump` vuelca los 2.529 *buckets* en los que MongoDB agrupa las lecturas y `mongorestore` reconstruye la colección como serie temporal con las 727.980 lecturas (verificado el 21/10/2026) | Exportar `lecturas` aparte a JSON o CSV (más lento y se pierde el tipo de la colección) |

## Consecuencias

- **Pérdida máxima = el tiempo desde el último backup (24 h con esta política).** Con una instancia sola no hay réplicas ni oplog, así que no existe recuperación a un instante. Es un límite conocido, no un descuido.
- `mongodump` sin oplog no saca una foto instantánea: si alguien escribe mientras corre, el respaldo puede mezclar momentos. En este proyecto las escrituras ocurren al cargar datos, nunca durante el backup.
- La política (7 diarios y 4 semanales) no tiene fuente: es una decisión del equipo, marcada como **supuesto adoptado** (ADR-012). La regla exacta está en `seleccionar_a_borrar`, una función que no borra nada y se prueba con fechas inventadas.
- `scripts/probar_respaldo.py` (19 casos) hace un backup real de `agrosense_tests`, lo restaura en `agrosense_tests_restaurada` y comprueba conteos, tipo de la serie temporal, los 7 índices del proyecto, validadores y Q1, Q5, Q9 y Q10. También prueba las protecciones (ubicación dentro del repo, base existente, archivo con un byte cambiado) y un simulacro de desastre.
- **Pendiente para el ADR-017:** los scripts usan hoy `AGROSENSE_URI` sin credenciales. Cuando se active la autenticación, el usuario `respaldo` (roles `backup` y `restore`) tendrá que conectarse sin que su clave aparezca en la línea de comandos del proceso.
