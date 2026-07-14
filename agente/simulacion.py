"""Bucle de rondas de negociación y persistencia de memoria.

Mismo flujo que el ejemplo de referencia: los industriales hablan primero
(ronda 1 o si tienen bandeja), el proveedor responde a solicitudes,
contraofertas y también a rechazos (para poder re-ofertar, cosa que el
ejemplo original no permitía).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .buzon import Buzon

TIPOS_QUE_DESPIERTAN_AL_PROVEEDOR = {"solicitud_presupuesto", "contraoferta", "rechazar_oferta"}


def invocar_agente(buzon: Buzon, agente: Any, agente_id: str, payload: dict[str, Any]) -> None:
    antes = len(buzon.mensajes)
    agente.invoke(
        {"messages": [{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]},
        config={"recursion_limit": 12},
    )
    if len(buzon.mensajes) == antes:
        print(f"{agente_id}: sin llamada de herramienta")


def ejecutar_ronda(
    buzon: Buzon,
    ronda: int,
    proveedor: Any,
    proveedor_id: str,
    industriales: list[dict[str, Any]],
    agentes_industriales: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    buzon.ronda_actual = ronda
    ronda_anterior = ronda - 1

    for industrial in industriales:
        industrial_id = industrial["industrial_id"]
        bandeja = buzon.bandeja(industrial_id, ronda_anterior)
        if ronda == 1 or bandeja:
            invocar_agente(
                buzon,
                agentes_industriales[industrial_id],
                industrial_id,
                {
                    "ronda": ronda,
                    "agente": industrial,
                    "mensajes_recibidos": bandeja,
                    "proveedor_id": proveedor_id,
                },
            )

    bandeja_proveedor = [
        m for m in buzon.bandeja(proveedor_id, ronda_anterior) if m["tipo"] in TIPOS_QUE_DESPIERTAN_AL_PROVEEDOR
    ]
    if bandeja_proveedor:
        invocar_agente(
            buzon,
            proveedor,
            proveedor_id,
            {"ronda": ronda, "proveedor_id": proveedor_id, "mensajes_recibidos": bandeja_proveedor},
        )

    agrupados = buzon.agrupar_por_receptor(buzon.mensajes_de_ronda(ronda))
    print(f"\nRonda {ronda}: mensajes agrupados por destinatario")
    print(json.dumps(agrupados, ensure_ascii=False, indent=2))
    return agrupados


def ejecutar_negociacion(
    buzon: Buzon,
    proveedor: Any,
    proveedor_id: str,
    industriales: list[dict[str, Any]],
    agentes_industriales: dict[str, Any],
    max_rondas: int = 4,
) -> dict[str, Any]:
    buzon.reiniciar()
    por_ronda = {
        ronda: ejecutar_ronda(buzon, ronda, proveedor, proveedor_id, industriales, agentes_industriales)
        for ronda in range(1, max_rondas + 1)
    }
    return {"mensajes_por_ronda": por_ronda, "mensajes": buzon.mensajes, "aceptaciones": buzon.aceptaciones}


def generar_memoria_markdown(buzon: Buzon) -> str:
    """Histórico de mensajes + resumen de acuerdos cerrados.

    El resumen de acuerdos es lo que de verdad le sirve al proveedor en la
    siguiente ejecución (qué cerró, con quién y a qué precio), sin tener que
    reinterpretar el log entero.
    """
    lineas = ["# Memoria del agente proveedor", "", "## Historial de interacciones", ""]
    for mensaje in buzon.mensajes:
        payload = mensaje.get("payload", {})
        texto = payload.get("message") or payload.get("motivo") or ""
        lineas.append(f"- Ronda {mensaje['ronda']} | {mensaje['tipo']} | {mensaje['from']} -> {mensaje['to']} | {texto}")

    lineas += ["", "## Acuerdos cerrados", ""]
    if not buzon.aceptaciones:
        lineas.append("_Ninguno todavía._")
    ofertas_por_id = {m["id"]: m for m in buzon.mensajes if m["tipo"] in {"oferta", "contraoferta"}}
    for aceptacion in buzon.aceptaciones:
        oferta_id = aceptacion["payload"].get("oferta_id", "")
        oferta = ofertas_por_id.get(oferta_id)
        if oferta:
            p = oferta["payload"]
            detalle = ", ".join(
                f"{mat} x{cant} a {coste} ({t} sem)"
                for mat, cant, coste, t in zip(
                    p.get("materia_prima", []), p.get("cantidad", []), p.get("coste", []), p.get("tiempo_entrega", [])
                )
            )
        else:
            detalle = f"oferta {oferta_id} no localizada en el buzón"
        lineas.append(f"- Ronda {aceptacion['ronda']} | {aceptacion['from']} acepta a {aceptacion['to']} | {detalle}")

    return "\n".join(lineas).strip() + "\n"


def persistir_memoria(buzon: Buzon, ruta: Path) -> None:
    ruta.write_text(generar_memoria_markdown(buzon), encoding="utf-8")
