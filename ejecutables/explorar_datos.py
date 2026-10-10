"""Punto de entrada para el análisis exploratorio del dataset."""

import sys
from pathlib import Path

CARPETA_PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_PROYECTO))

from clasificador_compras.flujo_datos import AnalizadorExploratorio


if __name__ == "__main__":
    try:
        AnalizadorExploratorio().ejecutar()
    except Exception as error:
        print(f"Error en el análisis exploratorio: {error}", file=sys.stderr)
        raise
