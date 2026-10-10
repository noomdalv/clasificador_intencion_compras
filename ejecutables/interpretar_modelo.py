"""Punto de entrada para generar la interpretación del modelo."""

import sys
from pathlib import Path

CARPETA_PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_PROYECTO))

from clasificador_compras.interpretacion import InterpreteModelo


if __name__ == "__main__":
    try:
        InterpreteModelo().ejecutar()
    except Exception as error:
        print(f"Error al interpretar el modelo: {error}", file=sys.stderr)
        raise
