"""Demo: reproduce el escenario del ejemplo de referencia (2 industriales)
contra el agente proveedor del paquete. Requiere OPENAI_API_KEY en .env.

Uso: python -m scripts.demo_negociacion
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from agente import Buzon, crear_agente_industrial, crear_agente_proveedor, ejecutar_negociacion, persistir_memoria

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("Falta OPENAI_API_KEY en .env. Este script ejecuta agentes reales, no simulados.")

INDUSTRIALES = [
    {
        "industrial_id": "I_METALNORTE",
        "nombre": "MetalNorte Automocion",
        "materia_prima": ["M01", "M02"],
        "cantidad": [90, 90],
        "coste_objetivo": [21.0, 16.0],
        "coste_maximo": [23.0, 18.0],
        "tiempo_maximo": [2, 2],
        "prioridad": "precio equilibrado y cumplimiento de plazo",
    },
    {
        "industrial_id": "I_FRIOPACK",
        "nombre": "FrioPack Agroindustrial",
        "materia_prima": ["M01"],
        "cantidad": [140],
        "coste_objetivo": [21.5],
        "coste_maximo": [23.5],
        "tiempo_maximo": [2],
        "prioridad": "continuidad de suministro para cadena de frio",
    },
]


def main() -> None:
    buzon = Buzon()
    proveedor, proveedor_id, _ = crear_agente_proveedor(
        buzon,
        RAIZ / "plantillas" / "p01_config.md",
        RAIZ / "plantillas" / "p01_memoria.md",
    )
    agentes_industriales = {
        item["industrial_id"]: crear_agente_industrial(buzon, item, proveedor_id) for item in INDUSTRIALES
    }

    resultado = ejecutar_negociacion(buzon, proveedor, proveedor_id, INDUSTRIALES, agentes_industriales, max_rondas=4)

    print("\nAceptaciones registradas:")
    print(json.dumps(resultado["aceptaciones"], ensure_ascii=False, indent=2))

    persistir_memoria(buzon, RAIZ / "plantillas" / "p01_memoria.md")
    print("\nMemoria actualizada en plantillas/p01_memoria.md")


if __name__ == "__main__":
    main()
