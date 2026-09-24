# LangChain en el backend CeresPINN

El chatbot y el resumen de reportes ejecutan la cadena LCEL
`ChatPromptTemplate | ChatOpenAI | StrOutputParser` definida en
`backend/llm.py`. El contenido se pasa como variable del prompt para conservar
literalmente las llaves de JSON y del mensaje del usuario.

## Entorno comprobado

Python 3.12.14; Pydantic 2.9.2; FastAPI 0.141.1; Starlette 1.6.0;
Torch 2.6.0+cpu; langchain-core 1.6.4; langchain-openai 1.6.6;
openai 3.19.2.

Las dependencias de LangChain quedan sin fijar agresivamente en
`backend/requirements.txt`. El `pip --dry-run` con el archivo completo
no pidió cambiar Pydantic, FastAPI, Starlette, Torch ni otro paquete ya
instalado. Añadiría solo `langchain-openai 1.6.6`, `openai 3.19.2`,
`tiktoken 0.14.0`, `jiter 0.17.0` y `regex 2026.9.10`.

Para reproducir las versiones principales comprobadas:

```powershell
.\.venv-langchain\Scripts\python.exe -m pip install -r backend/requirements-test.txt
.\.venv-langchain\Scripts\python.exe -m pip check
.\.venv-langchain\Scripts\python.exe -c "from backend.app import app"
.\.venv-langchain\Scripts\python.exe -m pytest backend/tests/test_api.py backend/tests/test_llm.py -q
.\.venv-langchain\Scripts\python.exe -m uvicorn backend.app:app --reload
```

## Configuración

En el backend de Render se debe configurar `OPENAI_API_KEY` con una clave
**nueva**. La clave compartida en la conversación debe revocarse. La variable
opcional `OPENAI_MODEL` toma `gpt-5-nano` por defecto. `GEMINI_API_KEY` y
`GEMINI_MODEL` ya no se leen por el backend; `render.yaml` todavía las declara
y se dejó intacto por la restricción previa. La clave OpenAI nunca va en el
frontend, GitHub, `render.yaml` ni en archivos compartidos.

No se necesita una clave de LangChain o LangSmith y no se activan trazas.
`ChatOpenAI` usa la API de Responses con razonamiento `minimal`, límite de
512 tokens, timeout de 30 segundos, `store=False` y sin `temperature` (GPT-5
nano no acepta el valor 0.3 anterior). Los reintentos están a cargo de los
endpoints: hasta tres intentos para errores transitorios. Los logs registran
solo tipo de error, código y request ID, nunca prompt ni credencial.

## Contratos

`POST /api/chatbot` conserva `message` y `context`, su prompt original,
el resultado `{reply, error: null, model}` con `model: "gpt-5-nano"`, la
respuesta alternativa cuando el modelo no produce texto, y los errores HTTP
503/502 con `detail` sanitizado.

`POST /api/reports/ai-summary` recibe:

```json
{
  "scenario": "SSP2-4.5",
  "simulation_summary": {
    "projectedYieldKgHa": 8000,
    "peakWaterStressIndex": 0.4,
    "totalWaterConsumedMm": 420
  }
}
```

Responde HTTP 200 con `{ "summary": "..." }`. Si falta la clave devuelve
HTTP 503; si falla el proveedor o no produce texto, HTTP 502. En ambos casos
de error la respuesta contiene `summary: null` y `error` sanitizado, nunca
la excepción cruda. Los datos inválidos reciben HTTP 422.

El resumen admite de 1 a 100 entradas y hasta 12 000 caracteres serializados,
con números finitos. El escenario admite hasta 120 caracteres y no puede
consistir únicamente en espacios.

La redacción de 4-5 oraciones y la fidelidad científica son instrucciones al
modelo, no garantías matemáticas. Los KPI proceden del solicitante: este
endpoint no verifica su procedencia, no calcula predicciones ni sustituye la
revisión del informe. No hay botón nuevo en el frontend ni integración con
Langflow en este cambio. `GET /api/chatbot/status` solo comprueba que exista
`OPENAI_API_KEY`; no prueba conectividad ni saldo de la cuenta.

## Verificación local realizada

- `pip check`: sin dependencias rotas.
- Importación de `backend.app`: correcta.
- 34 pruebas de `test_api.py` y `test_llm.py`: aprobadas. Se usó SQLite en
  memoria para la suite. Hubo un aviso de deprecación de AnyIO; no hubo
  fallos de pruebas. Las respuestas del modelo en estas pruebas son simuladas.
- Pendiente: configurar una clave OpenAI nueva en Render, desplegar y obtener
  HTTP 200 reales en ambos endpoints. La clave compartida en la conversación
  no se usó en pruebas locales ni se guardó en el repositorio.
