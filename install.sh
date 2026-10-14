#!/usr/bin/env bash
# install.sh — prepara el entorno de Python de agrosense.
#
# Qué hace:
#   1. Busca Python 3.
#   2. Crea el entorno virtual .venv (si no existe).
#   3. Instala las dependencias de requirements.txt dentro de .venv.
#   4. Avisa si faltan las herramientas de MongoDB (no las instala).
#
# Uso (desde la raíz del repositorio, en Git Bash, Linux o macOS):
#   ./install.sh

set -euo pipefail

cd "$(dirname "$0")"

VENV_DIR=".venv"

# 1. Buscar Python 3
if command -v python3 >/dev/null 2>&1 && python3 -c "import sys" >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "Error: no se encontró Python 3. Instalalo y volvé a ejecutar este script." >&2
    exit 1
fi

if ! "$PYTHON" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "Error: se necesita Python 3.10 o superior (encontrado: $("$PYTHON" --version))." >&2
    exit 1
fi
echo "Usando $("$PYTHON" --version)"

# 2. Crear el entorno virtual
if [ ! -d "$VENV_DIR" ]; then
    echo "Creando el entorno virtual en $VENV_DIR ..."
    "$PYTHON" -m venv "$VENV_DIR"
else
    echo "El entorno virtual $VENV_DIR ya existe; se reutiliza."
fi

# En Windows los ejecutables están en Scripts/; en Linux y macOS, en bin/
if [ -d "$VENV_DIR/Scripts" ]; then
    VENV_BIN="$VENV_DIR/Scripts"
else
    VENV_BIN="$VENV_DIR/bin"
fi
VENV_PYTHON="$VENV_BIN/python"

# 3. Instalar dependencias
echo "Actualizando pip ..."
"$VENV_PYTHON" -m pip install --upgrade pip --quiet

echo "Instalando dependencias de requirements.txt ..."
"$VENV_PYTHON" -m pip install -r requirements.txt

# 4. Verificar herramientas de MongoDB (solo aviso)
echo
echo "Verificando herramientas de MongoDB ..."
faltan=0
for herramienta in mongosh mongodump mongorestore; do
    if command -v "$herramienta" >/dev/null 2>&1; then
        echo "  OK      $herramienta"
    else
        echo "  FALTA   $herramienta"
        faltan=1
    fi
done
if [ "$faltan" -eq 1 ]; then
    echo "  Instalá mongosh y MongoDB Database Tools desde https://www.mongodb.com/try/download"
    echo "  y agregalos al PATH."
fi

echo
echo "Listo. Para activar el entorno virtual:"
if [ "$VENV_BIN" = "$VENV_DIR/Scripts" ]; then
    echo "  source $VENV_DIR/Scripts/activate"
else
    echo "  source $VENV_DIR/bin/activate"
fi
