"""Construcción de agentes LangChain a partir de ficha + memoria.

Cada agente lleva su propio set de herramientas (identidad fijada por
closure sobre el buzón compartido). El proveedor además lleva el catálogo
para que los guardrails validen sus ofertas.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from .buzon import Buzon
from .herramientas import crear_herramientas
from .loaders import cargar_config, cargar_memoria
from .prompts import prompt_industrial, prompt_proveedor


def modelo() -> ChatOpenAI:
    return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))


def crear_agente_proveedor(
    buzon: Buzon,
    ruta_config: Path,
    ruta_memoria: Path,
) -> tuple[Any, str, dict[str, Any]]:
    """Devuelve (agente, proveedor_id, metadatos de config)."""
    _, meta = cargar_config(ruta_config)
    memoria_md = cargar_memoria(ruta_memoria)
    proveedor_id = f"P_{meta['id']}"

    herramientas = crear_herramientas(buzon, proveedor_id, "proveedor", catalogo=meta["catalogo"])
    agente = create_agent(
        model=modelo(),
        tools=herramientas,
        system_prompt=prompt_proveedor(meta, memoria_md),
        name=f"proveedor_{meta['id']}",
    )
    return agente, proveedor_id, meta


def crear_agente_industrial(buzon: Buzon, industrial: dict[str, Any], proveedor_id: str) -> Any:
    herramientas = crear_herramientas(buzon, industrial["industrial_id"], "industrial")
    return create_agent(
        model=modelo(),
        tools=herramientas,
        system_prompt=prompt_industrial(industrial, proveedor_id),
        name=industrial["industrial_id"],
    )
