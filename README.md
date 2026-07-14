# Agente proveedor — negociación multi-agente (LangChain puro)

Implementación del agente proveedor a partir del ejemplo de referencia
(`comunicacion.ipynb`): mismo contrato de comunicación (5 herramientas),
mismo patrón config + memoria en dos markdowns, pero estructurado como
paquete Python y preparado para exponerse vía FastAPI.

## Estructura

```
agente/           # Paquete del agente
  buzon.py        # Buzón compartido (clase, sin globales)
  loaders.py      # Carga y validación de config/memoria markdown
  herramientas.py # Las 5 tools de comunicación + guardrails de catálogo
  prompts.py      # Prompts construidos desde el YAML de la ficha
  fabrica.py      # create_agent de LangChain para proveedor e industriales
  simulacion.py   # Bucle de rondas y generación/persistencia de memoria
app/              # FastAPI (endpoints por especificar)
  main.py         # Lifespan con buzón + agente cargados, /health
  routers/        # Aquí irán los routers cuando se definan las APIs
plantillas/       # Fichas del agente
  p01_config.md   # Config del proveedor (fuente única de verdad)
  p01_memoria.md  # Memoria persistida entre ejecuciones
scripts/
  demo_negociacion.py  # Reproduce el escenario del notebook (2 industriales)
```

## Uso

```bash
cp .env.example .env   # y rellenar OPENAI_API_KEY
make demo              # negociación de 4 rondas contra 2 industriales
make api               # levantar FastAPI en :8000 (de momento solo /health)
```

## Decisiones de diseño respecto al ejemplo

- **Config como fuente única de verdad.** El catálogo (precios objetivo/mínimo,
  entregas mínimas, stock) vive en el frontmatter YAML de `p01_config.md` y el
  prompt se genera desde ahí. Se elimina el mismatch cliente/proveedor de
  `c01_config.md`: el loader valida `tipo: proveedor` y peta con mensaje claro
  si se carga una ficha equivocada.
- **Identidad por closure, no por global.** Cada agente recibe su set de
  herramientas con su id ya fijado, en lugar del `ACTIVE_AGENT_ID` global.
  Esto hace el sistema seguro ante ejecución paralela/async (necesario para
  FastAPI) y elimina la posibilidad de suplantación de emisor.
- **Guardrails deterministas.** Las ofertas y contraofertas del proveedor se
  validan en código contra el catálogo: coste bajo mínimo se corrige al mínimo,
  plazo bajo entrega mínima se corrige, exceso sobre stock se avisa. Las
  correcciones quedan anotadas en `avisos_guardrail` dentro del payload para
  que sean auditables. No dependemos de que el LLM respete los suelos.
- **El proveedor responde a rechazos.** El filtro de bandeja incluye
  `rechazar_oferta`, permitiendo re-ofertar tras un rechazo (en el ejemplo
  original el rechazo cortaba la negociación en silencio).
- **Memoria con síntesis de acuerdos.** Además del log de mensajes, la memoria
  incluye una sección de acuerdos cerrados (quién, qué, precio, plazo), que es
  lo útil para la siguiente ejecución.
