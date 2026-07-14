"""Carga de los dos markdowns que definen al agente: config y memoria.

La config es la única fuente de verdad del comportamiento del proveedor
(catálogo, mínimos, reglas). El prompt se construye a partir del YAML
parseado, no de texto suelto, así evitamos el mismatch config/rol que
tuvimos con c01_config.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def leer_texto(ruta: Path) -> str:
    if not ruta.exists():
        raise FileNotFoundError(ruta)
    return ruta.read_text(encoding="utf-8").strip()


def frontmatter(markdown: str) -> dict[str, Any]:
    """Extrae el bloque YAML entre los dos primeros '---' del markdown."""
    if not markdown.startswith("---"):
        return {}
    _, yaml_crudo, _ = markdown.split("---", 2)
    return yaml.safe_load(yaml_crudo) or {}


def cargar_config(ruta: Path) -> tuple[str, dict[str, Any]]:
    """Devuelve (markdown completo, metadatos del frontmatter) y valida lo esencial."""
    texto = leer_texto(ruta)
    meta = frontmatter(texto)

    # Validación temprana: mejor petar aquí con un mensaje claro que
    # descubrir el problema a mitad de negociación.
    if meta.get("tipo") != "proveedor":
        raise ValueError(
            f"La config {ruta.name} define tipo={meta.get('tipo')!r}, se esperaba 'proveedor'. "
            "Revisa que estás cargando la ficha correcta."
        )
    if not meta.get("catalogo"):
        raise ValueError(f"La config {ruta.name} no tiene 'catalogo' en el frontmatter.")

    return texto, meta


def cargar_memoria(ruta: Path) -> str:
    if not ruta.exists():
        return "_Sin memoria previa._"
    texto = ruta.read_text(encoding="utf-8").strip()
    return texto or "_Sin memoria previa._"
