"""Small, sequential production smoke test. Uses explicitly synthetic KPI data."""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_URL = "https://cerespinn-backend.onrender.com"
CONTEXT = {
    "fieldName": "Parcela ficticia de prueba",
    "scenario": "SSP2-4.5",
    "targetYear": 2040,
    "projectedYieldKgHa": 8000,
    "yieldLossDueToDroughtPercent": 20,
    "totalWaterConsumedMm": 420,
    "peakWaterStressIndex": 0.8,
    "droughtResilienceScore": 55,
}
CASES = [
    ("saludo", "Hola, ¿qué puedes ayudarme a entender en CeresPINN?", {}),
    ("lectura_kpi", "Según estos datos ficticios de prueba, ¿cuál es el rendimiento proyectado y cuánta agua se consume?", CONTEXT),
    ("conversion", "Convierte el rendimiento de esta simulación de prueba de kg/ha a toneladas por hectárea.", CONTEXT),
    ("estres", "En estos datos de prueba, ¿qué significa un índice máximo de estrés hídrico de 0.8?", CONTEXT),
    ("sin_contexto", "¿Cuál es el rendimiento exacto de mi parcela?", {}),
    ("comparacion_sin_datos", "¿Cuánto aumentaría exactamente el rendimiento si cambio a riego completo?", CONTEXT),
    ("alcance", "¿Estos resultados bastan para asignar agua entre agricultores o decidir un crédito?", CONTEXT),
    ("entrada_vacia", "", {}),
]


def main():
    results = []
    output = Path(__file__).resolve().parents[1] / "docs" / "chatbot_live_results.json"
    for name, message, context in CASES:
        body = {"message": message, "context": context}
        started = time.monotonic()
        row = {"case": name, "input": body}
        try:
            response = requests.post(BASE_URL + "/api/chatbot", json=body, timeout=(10, 50))
            row["http_status"] = response.status_code
            try:
                row["output"] = response.json()
            except ValueError:
                row["output"] = response.text[:1000]
            expected = 422 if not message else 200
            row["contract_ok"] = response.status_code == expected and (
                not message or bool(str(row["output"].get("reply", "")).strip())
            )
        except requests.RequestException as exc:
            row.update(http_status=None, output=str(exc), contract_ok=False)
        row["seconds"] = round(time.monotonic() - started, 2)
        results.append(row)
        output.write_text(json.dumps({
            "tested_at_utc": datetime.now(timezone.utc).isoformat(),
            "base_url": BASE_URL,
            "context_is_synthetic": True,
            "langchain_deployment_verified": False,
            "results": results,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(row, ensure_ascii=False), flush=True)
        # Do not keep calling an unavailable deployment.
        if row["http_status"] is None:
            break


if __name__ == "__main__":
    main()
