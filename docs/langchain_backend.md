# LangChain en el backend CeresPINN

El chatbot y el resumen de reportes ejecutan la cadena LCEL
`ChatPromptTemplate | ChatGoogleGenerativeAI | StrOutputParser` definida en
`backend/llm.py`. El contenido se pasa como variable del prompt para conservar
literalmente las llaves de JSON y del mensaje del usuario.

## Entorno comprobado

Python 3.12.14; Pydantic 2.9.2; pydantic-core 2.23.4; FastAPI 0.141.1;
Starlette 1.6.0; Torch 2.6.0+cpu; langchain-core 1.6.4;
langchain-google-genai 4.3.7; google-genai 2.8.0.

Las dos dependencias nuevas quedan sin fijar en `backend/requirements.txt`.
Pip debe resolver **todo ese archivo junto**, respetando Pydantic 2.9.2.
Instalar las integraciones por separado sin restricciones puede actualizar
Pydantic. El entorno local `.venv-langchain` está separado de `.venv`.

Para reproducir las versiones principales comprobadas:

```powershell
python -m venv .venv-langchain
.\.venv-langchain\Scripts\python.exe -m pip install -r backend/requirements-test.txt langchain-core==1.6.4 langchain-google-genai==4.3.7 google-genai==2.8.0 fastapi==0.141.1 starlette==1.6.0
.\.venv-langchain\Scripts\python.exe -m pip check
.\.venv-langchain\Scripts\python.exe -c "from backend.app import app"
.\.venv-langchain\Scripts\python.exe -m pytest backend/tests/test_api.py backend/tests/test_llm.py -q
.\.venv-langchain\Scripts\python.exe -m uvicorn backend.app:app --reload
```

## Configuración

Se reutiliza `GEMINI_API_KEY` del backend. `GEMINI_MODEL` conserva su valor
predeterminado `gemini-flash-latest`. No se necesita cuenta ni clave de
LangChain o LangSmith. No se activa el envío de trazas a LangSmith.
La credencial de Render no se copia automáticamente al entorno local.

La configuración del modelo conserva temperatura 0.3, 300 tokens de salida y
presupuesto de razonamiento 0. Los reintentos están a cargo del endpoint:
hasta tres intentos para 429, 500, 503, UNAVAILABLE o RESOURCE_EXHAUSTED, con
esperas de 1.5 y 3 segundos. Se configura un timeout de 10 segundos por llamada.

## Contratos

`POST /api/chatbot` conserva `message` y `context`, su prompt original,
el resultado `{reply, error: null, model}`, la respuesta alternativa cuando
el modelo no produce texto, y los errores HTTP 503/502 con `detail` sanitizado.

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
Langflow en este cambio.

## Verificación local realizada

- `pip check`: sin dependencias rotas.
- Importación de `backend.app`: correcta.
- Uvicorn con `--reload`, puerto 8017: arranque correcto.
- 34 pruebas de `test_api.py` y `test_llm.py`: aprobadas. Se usó SQLite en
  memoria para la suite. Hubo avisos de deprecación de AnyIO y de permisos de
  la caché de pytest; no hubo fallos de pruebas.
- POST reales por HTTP sin credencial: ambos endpoints devolvieron HTTP 503
  con errores controlados.
- POST reales por HTTP en un segundo proceso de prueba, puerto 8018:
  ambos devolvieron HTTP 200 con el contrato esperado. Este proceso mantuvo
  la cadena LCEL y `ChatGoogleGenerativeAI`, sustituyendo únicamente
  `google.genai.models.Models.generate_content` por una respuesta determinística.
  Esa sustitución fue temporal en memoria, no forma parte del backend.
- Se detuvieron ambos servidores de prueba al terminar.

No se validó una respuesta real de Google porque la sesión local no dispone
de `GEMINI_API_KEY`. No se realizó despliegue ni se modificó producción.
