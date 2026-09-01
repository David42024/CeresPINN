#!/usr/bin/env bash
# Render start command for the CeresPINN FastAPI backend.
# Uses $PORT injected by Render; falls back to 8000 locally.
set -e

PORT="${PORT:-8000}"
exec uvicorn backend.app:app --host 0.0.0.0 --port "$PORT" --workers 1
