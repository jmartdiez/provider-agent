"""Prompts de los agentes.

El prompt del proveedor se construye desde el YAML parseado de su config:
catálogo, reglas y estilo salen de la ficha, no de texto hardcodeado. Así
si mañana cambia un precio mínimo, se cambia en el markdown y punto.
"""

from __future__ import annotations

from typing import Any


def _seccion_catalogo(catalogo: dict[str, Any]) -> str:
    lineas = []
    for material, ficha in catalogo.items():
        lineas.append(
            f"- {material}: precio objetivo {ficha['precio_objetivo_eur']}, "
            f"mínimo {ficha['precio_minimo_eur']}, "
            f"entrega mínima {ficha['entrega_minima_semanas']} semana(s), "
            f"stock {ficha.get('stock_disponible', 'sin límite')}"
        )
    return "\n".join(lineas)


def _seccion_reglas(reglas: dict[str, Any]) -> str:
    bloques = []
    for clave, titulo in (("aceptar_si", "Acepta si"), ("contraofertar_si", "Contraoferta si"), ("rechazar_si", "Rechaza si")):
        items = reglas.get(clave, [])
        if items:
            bloques.append(f"{titulo}:\n" + "\n".join(f"  - {item}" for item in items))
    estilo = reglas.get("estilo_negociacion")
    if estilo:
        bloques.append(f"Estilo de negociación: {estilo}")
    return "\n".join(bloques)


def prompt_proveedor(meta: dict[str, Any], memoria_md: str) -> str:
    proveedor_id = f"P_{meta['id']}"
    return f"""
Eres el agente proveedor {proveedor_id} ({meta['nombre']}).
Vendes materias primas a empresas industriales negociando exclusivamente
a través de las herramientas disponibles.

Catálogo (fuente de verdad, definida en tu ficha de configuración):
{_seccion_catalogo(meta['catalogo'])}

Reglas de negociación:
{_seccion_reglas(meta.get('reglas_negociacion', {}))}

Normas operativas:
- El campo `tiempo_entrega` siempre está en semanas enteras; nunca uses días.
- Si recibes `solicitud_presupuesto`, responde con una `oferta` por cada solicitud.
- Si recibes `contraoferta`, acéptala si cada coste está en o por encima del mínimo
  y cada plazo respeta la entrega mínima; si está cerca, responde con `contraoferta`
  ajustando solo precio, cantidad o plazo; rechaza solo si no hay forma razonable de cerrar.
- Haz como máximo una llamada de herramienta por mensaje recibido.
- No cierres acuerdos fuera de las herramientas: todo debe quedar en el buzón.

Memoria de interacciones anteriores:
{memoria_md}
""".strip()


def prompt_industrial(industrial: dict[str, Any], proveedor_id: str) -> str:
    return f"""
Representas a {industrial['nombre']} ({industrial['industrial_id']}).
Negocias con el proveedor {proveedor_id} usando exclusivamente herramientas.

Necesidades:
- Materias primas: {industrial['materia_prima']}
- Cantidades: {industrial['cantidad']}
- Costes objetivo: {industrial['coste_objetivo']}
- Costes máximos: {industrial['coste_maximo']}
- Tiempos máximos en semanas: {industrial['tiempo_maximo']}
- Prioridad: {industrial['prioridad']}

Reglas:
- Si no tienes mensajes previos, inicia con `solicitud_presupuesto`.
- El campo `tiempo_entrega` siempre está en semanas enteras; nunca uses días.
- Si recibes una oferta en o por debajo del coste objetivo y dentro de plazo, usa `aceptar_oferta`.
- Si está por debajo del coste máximo pero por encima del objetivo, usa `contraoferta`.
- Si supera coste máximo o plazo máximo, usa `rechazar_oferta`.
- Haz como máximo una llamada de herramienta por mensaje recibido.
- No cierres nada fuera de las herramientas.
""".strip()
