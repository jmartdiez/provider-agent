"""Buzón compartido del ecosistema.

Sustituye a las variables globales del notebook (MESSAGES, ACCEPTANCES,
CURRENT_ROUND, ACTIVE_AGENT_ID). Al ser una clase, podemos tener un buzón
por simulación, inyectarlo en FastAPI como dependencia, y paralelizar
agentes sin que se pisen entre ellos.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any
from uuid import uuid4


class Buzon:
    """Registro central de mensajes entre agentes, organizado por rondas."""

    def __init__(self) -> None:
        self.mensajes: list[dict[str, Any]] = []
        self.aceptaciones: list[dict[str, Any]] = []
        self.ronda_actual: int = 0

    def emitir(self, tipo: str, emisor: str, receptor: str, payload: dict[str, Any]) -> dict[str, Any]:
        registro = {
            "id": f"{tipo}-{len(self.mensajes) + 1:03d}-{uuid4().hex[:6]}",
            "ronda": self.ronda_actual,
            "tipo": tipo,
            "from": emisor,
            "to": receptor,
            "payload": payload,
        }
        self.mensajes.append(registro)
        if tipo == "aceptar_oferta":
            self.aceptaciones.append(registro)
        return registro

    def mensajes_de_ronda(self, ronda: int) -> list[dict[str, Any]]:
        return [m for m in self.mensajes if m["ronda"] == ronda]

    def agrupar_por_receptor(self, mensajes: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        agrupados: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for mensaje in mensajes:
            agrupados[mensaje["to"]].append(mensaje)
        return dict(agrupados)

    def bandeja(self, agente_id: str, ronda: int) -> list[dict[str, Any]]:
        return self.agrupar_por_receptor(self.mensajes_de_ronda(ronda)).get(agente_id, [])

    def reiniciar(self) -> None:
        self.mensajes.clear()
        self.aceptaciones.clear()
        self.ronda_actual = 0
