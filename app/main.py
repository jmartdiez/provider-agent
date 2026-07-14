"""API del ecosistema de negociación (FastAPI).

Los endpoints concretos están por especificar; este stub deja preparado:
- el ciclo de vida de la app con un Buzon y el agente proveedor cargados,
- la inyección de dependencias para que los routers los reciban limpios,
- un health check para validar el despliegue.

Cuando se definan las APIs, cada bloque funcional va en su router dentro
de app/routers/ y se registra aquí con include_router.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request

from agente import Buzon, crear_agente_proveedor

RAIZ = Path(__file__).resolve().parent.parent
RUTA_CONFIG = RAIZ / "plantillas" / "p01_config.md"
RUTA_MEMORIA = RAIZ / "plantillas" / "p01_memoria.md"


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    load_dotenv(RAIZ / ".env")
    buzon = Buzon()
    agente, proveedor_id, meta = crear_agente_proveedor(buzon, RUTA_CONFIG, RUTA_MEMORIA)
    app.state.buzon = buzon
    app.state.proveedor = agente
    app.state.proveedor_id = proveedor_id
    app.state.config_proveedor = meta
    yield


app = FastAPI(title="Ecosistema de negociación multi-agente", lifespan=ciclo_de_vida)


def obtener_buzon(request: Request) -> Buzon:
    return request.app.state.buzon


@app.get("/health")
def health(request: Request) -> dict:
    return {
        "status": "ok",
        "proveedor": request.app.state.proveedor_id,
        "mensajes_en_buzon": len(request.app.state.buzon.mensajes),
    }


# TODO: registrar routers cuando se especifiquen las APIs, por ejemplo:
# from .routers import negociacion
# app.include_router(negociacion.router, prefix="/negociacion", tags=["negociacion"])
