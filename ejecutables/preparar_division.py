"""Punto de entrada para crear las particiones de entrenamiento y prueba."""

import sys
from pathlib import Path

CARPETA_PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_PROYECTO))

from clasificador_compras.flujo_datos import DivisorDatos


if __name__ == "__main__":
    try:
        DivisorDatos().ejecutar()
    except Exception as error:
        print(f"Error al preparar las particiones: {error}", file=sys.stderr)
        raise
