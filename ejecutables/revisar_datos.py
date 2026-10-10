"""Punto de entrada para auditar el dataset original de UCI."""

import sys
from pathlib import Path

CARPETA_PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_PROYECTO))

from clasificador_compras.flujo_datos import AuditorDatos


if __name__ == "__main__":
    try:
        AuditorDatos().ejecutar()
    except Exception as error:
        print(f"Error al revisar el dataset: {error}", file=sys.stderr)
        raise
