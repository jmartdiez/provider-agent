"""Las 5 herramientas de comunicación entre empresas.

Mismo contrato que el ejemplo de referencia (solicitud_presupuesto, oferta,
contraoferta, aceptar_oferta, rechazar_oferta), con dos cambios de fondo:

1. Identidad por closure: cada agente recibe SU set de herramientas con su
   id ya fijado. El LLM no puede suplantar a nadie ni equivocarse de emisor,
   y desaparece el global ACTIVE_AGENT_ID (que impedía paralelizar).

2. Guardrails deterministas: las ofertas/contraofertas del proveedor se
   validan en código contra el catálogo (precio mínimo, entrega mínima,
   stock). No confiamos en que el LLM respete los suelos por prompt: si los
   rompe, la herramienta corrige y lo deja anotado en el payload.
"""

from __future__ import annotations

from typing import Any, Literal

from langchain_core.tools import tool

from .buzon import Buzon


def _validar_lineas_proveedor(
    catalogo: dict[str, Any],
    materia_prima: list[str],
    coste: list[float],
    cantidad: list[int],
    tiempo_entrega: list[int],
) -> tuple[list[float], list[int], list[str]]:
    """Corrige en código cualquier línea que rompa los límites del catálogo.

    Devuelve (costes corregidos, tiempos corregidos, avisos). Los avisos se
    adjuntan al payload para que quede auditable qué corrigió el guardrail.
    """
    costes_ok: list[float] = []
    tiempos_ok: list[int] = []
    avisos: list[str] = []

    for i, material in enumerate(materia_prima):
        ficha = catalogo.get(material)
        if ficha is None:
            avisos.append(f"{material}: fuera de catálogo, línea emitida sin validar")
            costes_ok.append(coste[i])
            tiempos_ok.append(tiempo_entrega[i])
            continue

        minimo = float(ficha["precio_minimo_eur"])
        entrega_min = int(ficha["entrega_minima_semanas"])
        stock = int(ficha.get("stock_disponible", 10**9))

        c = float(coste[i])
        if c < minimo:
            avisos.append(f"{material}: coste {c} por debajo del mínimo {minimo}, corregido a {minimo}")
            c = minimo
        costes_ok.append(c)

        t = int(tiempo_entrega[i])
        if t < entrega_min:
            avisos.append(f"{material}: plazo {t} inferior a la entrega mínima {entrega_min}, corregido")
            t = entrega_min
        tiempos_ok.append(t)

        if int(cantidad[i]) > stock:
            avisos.append(f"{material}: cantidad {cantidad[i]} supera stock {stock} (revisar antes de comprometer)")

    return costes_ok, tiempos_ok, avisos


def crear_herramientas(
    buzon: Buzon,
    agente_id: str,
    rol: Literal["proveedor", "industrial"],
    catalogo: dict[str, Any] | None = None,
) -> list[Any]:
    """Construye el set de herramientas de un agente concreto.

    El emisor de cada mensaje es siempre `agente_id`: da igual lo que el LLM
    ponga en sus argumentos, la identidad la fija el código.
    """

    @tool
    def solicitud_presupuesto(
        proveedor_id: str,
        materia_prima: list[str],
        cantidad: list[int],
        coste: list[float] | None = None,
        message: str = "",
    ) -> dict[str, Any]:
        """Envía una solicitud de presupuesto de esta empresa industrial a un proveedor."""
        return buzon.emitir(
            "solicitud_presupuesto",
            agente_id,
            proveedor_id,
            {
                "industrial_id": agente_id,
                "proveedor_id": proveedor_id,
                "materia_prima": materia_prima,
                "cantidad": cantidad,
                "coste": coste or [],
                "message": message,
            },
        )

    @tool
    def oferta(
        industrial_id: str,
        materia_prima: list[str],
        coste: list[float],
        cantidad: list[int],
        tiempo_entrega: list[int],
        message: str = "",
    ) -> dict[str, Any]:
        """Envía una oferta de este proveedor a una empresa industrial. tiempo_entrega en semanas."""
        avisos: list[str] = []
        if rol == "proveedor" and catalogo:
            coste, tiempo_entrega, avisos = _validar_lineas_proveedor(
                catalogo, materia_prima, coste, cantidad, tiempo_entrega
            )
        return buzon.emitir(
            "oferta",
            agente_id,
            industrial_id,
            {
                "proveedor_id": agente_id,
                "industrial_id": industrial_id,
                "materia_prima": materia_prima,
                "coste": coste,
                "cantidad": cantidad,
                "tiempo_entrega": tiempo_entrega,
                "message": message,
                "avisos_guardrail": avisos,
            },
        )

    @tool
    def contraoferta(
        receptor_id: str,
        materia_prima: list[str],
        coste: list[float],
        cantidad: list[int],
        tiempo_entrega: list[int],
        message: str = "",
    ) -> dict[str, Any]:
        """Envía una contraoferta a la otra parte de la negociación. tiempo_entrega en semanas."""
        avisos: list[str] = []
        if rol == "proveedor" and catalogo:
            coste, tiempo_entrega, avisos = _validar_lineas_proveedor(
                catalogo, materia_prima, coste, cantidad, tiempo_entrega
            )
        return buzon.emitir(
            "contraoferta",
            agente_id,
            receptor_id,
            {
                "emisor_id": agente_id,
                "receptor_id": receptor_id,
                "rol_emisor": rol,
                "materia_prima": materia_prima,
                "coste": coste,
                "cantidad": cantidad,
                "tiempo_entrega": tiempo_entrega,
                "message": message,
                "avisos_guardrail": avisos,
            },
        )

    @tool
    def aceptar_oferta(receptor_id: str, oferta_id: str, message: str = "") -> dict[str, Any]:
        """Acepta una oferta o contraoferta anterior identificada por su oferta_id."""
        return buzon.emitir(
            "aceptar_oferta",
            agente_id,
            receptor_id,
            {"emisor_id": agente_id, "receptor_id": receptor_id, "oferta_id": oferta_id, "message": message},
        )

    @tool
    def rechazar_oferta(
        receptor_id: str,
        oferta_id: str,
        motivo: str = "",
        message: str = "",
    ) -> dict[str, Any]:
        """Rechaza una oferta o contraoferta anterior identificada por su oferta_id."""
        return buzon.emitir(
            "rechazar_oferta",
            agente_id,
            receptor_id,
            {
                "emisor_id": agente_id,
                "receptor_id": receptor_id,
                "oferta_id": oferta_id,
                "motivo": motivo,
                "message": message,
            },
        )

    if rol == "industrial":
        return [solicitud_presupuesto, contraoferta, aceptar_oferta, rechazar_oferta]
    return [oferta, contraoferta, aceptar_oferta, rechazar_oferta]
