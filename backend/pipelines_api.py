"""FastAPI routes exposing the CeresPINN data extraction pipelines.

REST contract:
  GET  /api/pipelines            -> list every pipeline + its current manifest status
  POST /api/pipelines/{id}/sync  -> trigger a (re)extraction for one pipeline
  POST /api/pipelines/sync-all   -> trigger every pipeline
  GET  /api/pipelines/jobs/{job_id} -> poll the status/progress of a background job

Status model
  Each pipeline reports a status derived from its on-disk manifest:
    - "healthy"     extraction ran and produced records
    - "empty"       extraction ran but produced zero records
    - "error"       extraction failed
    - "never"       no manifest yet (never synced)

Jobs
  Background extractions are tracked in-memory with a bounded ring buffer. A job
  transitions pending -> running -> done|error and exposes coarse progress events
  (step/total/stage) reported by the providers.

A runtime fallback (`fallback: true`) is used by the frontend when the backend is
unreachable; it is deliberately explicit and never silent.
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .data import settings
from .data.chirps import CHIRPSProvider
from .data.nass import NASSProvider
from .data.nex_gddp import NEXGDDPProvider

router = APIRouter(prefix="/api/pipelines", tags=["pipelines"])

_executor = ThreadPoolExecutor(max_workers=2)

# ---------------------------------------------------------------------------
# Provider registry (id is stable and matches the frontend pipe ids)
# ---------------------------------------------------------------------------
def _providers(progress: Optional[Any] = None) -> Dict[str, Any]:
    return {
        "pipe-chirps": CHIRPSProvider(settings, progress),
        "pipe-nasa-nex": NEXGDDPProvider(settings, progress),
        "pipe-usda-nass": NASSProvider(settings, progress),
    }


PIPE_META = {
    "pipe-chirps": {
        "name": "CHIRPS Daily Precipitation Pipeline",
        "frequency": "Diario (06:00 UTC)",
        "source": "UCSB Climate Hazards Center (FTP/GeoTIFF 0.05°)",
        "resolution": "0.05° (~5.3 km) downscaled to 100m",
    },
    "pipe-nasa-nex": {
        "name": "NASA NEX-GDDP CMIP6 Climate Scenarios",
        "frequency": "Semanal (Actualización de proyecciones)",
        "source": "NASA Earth Exchange (S3 Public Bucket / NetCDF4)",
        "resolution": "0.25° con Quantile Delta Mapping",
    },
    "pipe-usda-nass": {
        "name": "USDA NASS QuickStats Crop Harvest Yields",
        "frequency": "Mensual",
        "source": "USDA National Agricultural Statistics Service API",
        "resolution": "Nivel Condado / Parcela de calibración",
    },
}

# id --(manifest file name / output dir)--
PIPE_MANIFEST = {
    "pipe-chirps": "chirps_manifest.json",
    "pipe-nasa-nex": "nex-gddp_manifest.json",
    "pipe-usda-nass": "usda-nass_manifest.json",
}


def _manifest_path(pipe_id: str) -> Optional[Path]:
    """Return the manifest path for a pipeline, or None if missing."""
    cfg = {
        "pipe-chirps": settings.paths.chirps,
        "pipe-nasa-nex": settings.paths.nex,
        "pipe-usda-nass": settings.paths.nass,
    }.get(pipe_id)
    if cfg is None:
        return None
    manifest = cfg / PIPE_MANIFEST[pipe_id]
    return manifest if manifest.exists() else None


def _read_manifest(path: Optional[Path]) -> Optional[Dict[str, Any]]:
    if path is None:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _pipeline_status(pipe_id: str) -> Dict[str, Any]:
    """Derive a stable status object for a pipeline from its on-disk manifest."""
    manifest = _read_manifest(_manifest_path(pipe_id))
    meta = PIPE_META[pipe_id]

    if manifest is None:
        status, last_sync, records = "never", "-", "Sin sincronizar"
    else:
        records = str(manifest.get("records", 0))
        last_sync = manifest.get("generated_at", "-")
        if manifest.get("records", 0) is not None and manifest.get("records", 0) > 0:
            status = "healthy"
        else:
            status = "empty"

    return {
        "id": pipe_id,
        "name": meta["name"],
        "source": meta["source"],
        "frequency": meta["frequency"],
        "resolution": meta["resolution"],
        "status": status,
        "lastSync": last_sync,
        "recordsProcessed": records,
        "detail": manifest or {},
    }


class SyncResponse(BaseModel):
    job_id: str
    pipeline_id: str
    accepted: bool
    message: str


class PipelineListResponse(BaseModel):
    pipelines: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# In-memory job registry (bounded)
# ---------------------------------------------------------------------------
class JobRegistry:
    """Thread-safe, bounded store of background extraction jobs."""

    def __init__(self, max_entries: int = 100) -> None:
        self._lock = threading.Lock()
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._order: List[str] = []
        self._max = max_entries

    def create(self, job_id: str, pipeline_id: str) -> Dict[str, Any]:
        with self._lock:
            job = {
                "job_id": job_id,
                "pipeline_id": pipeline_id,
                "status": "pending",
                "stage": "queued",
                "step": 0,
                "total": 0,
                "percent": 0,
                "message": "Job creado y en cola.",
                "error": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "started_at": None,
                "finished_at": None,
                "result": None,
            }
            self._jobs[job_id] = job
            self._order.append(job_id)
            while len(self._order) > self._max:
                oldest = self._order.pop(0)
                self._jobs.pop(oldest, None)
            return job

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def update(self, job_id: str, **fields: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            job.update(fields)


registry = JobRegistry()


def _make_progress(job_id: str):
    """Return a progress callback that updates the named job's coarse state."""
    def _on_progress(payload: Dict[str, Any]) -> None:
        step = payload.get("step", 0)
        total = payload.get("total", 0) or 1
        stage = payload.get("stage", "")
        percent = min(99, int(round(step / total * 100))) if total else 0
        registry.update(
            job_id,
            status="running",
            stage=stage,
            step=step,
            total=total,
            percent=percent,
            message=f"Procesando: {stage} ({step}/{total})",
        )
    return _on_progress


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("", response_model=PipelineListResponse)
def list_pipelines() -> Dict[str, Any]:
    return {"pipelines": [_pipeline_status(pid) for pid in PIPE_META]}


@router.get("/jobs/{job_id}")
def get_job(job_id: str) -> Dict[str, Any]:
    job = registry.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Unknown job: {job_id}")
    return job


@router.post(
    "/sync-all",
    response_model=SyncResponse,
    responses={202: {"description": "Extraction started in background"}},
)
def sync_all() -> SyncResponse:
    job_id = str(uuid.uuid4())
    registry.create(job_id, "*")
    _executor.submit(_run_all_jobs, job_id)
    return SyncResponse(
        job_id=job_id,
        pipeline_id="*",
        accepted=True,
        message="Extraction started for all pipelines (background job).",
    )


@router.post(
    "/{pipe_id}/sync",
    response_model=SyncResponse,
    responses={202: {"description": "Extraction started in background"}},
)
def sync_pipeline(pipe_id: str) -> SyncResponse:
    providers = _providers()
    provider = providers.get(pipe_id)
    if provider is None:
        raise HTTPException(status_code=404, detail=f"Unknown pipeline: {pipe_id}")

    job_id = str(uuid.uuid4())
    registry.create(job_id, pipe_id)
    _executor.submit(_run_single_job, job_id, pipe_id)
    return SyncResponse(
        job_id=job_id,
        pipeline_id=pipe_id,
        accepted=True,
        message="Extraction started (background job).",
    )


# ---------------------------------------------------------------------------
# Background jobs
# ---------------------------------------------------------------------------
def _run_single_job(job_id: str, pipe_id: str) -> None:
    registry.update(job_id, status="running", started_at=datetime.now(timezone.utc).isoformat())
    try:
        progress = _make_progress(job_id)
        provider = _providers(progress)[pipe_id]
        result = provider.run()
        registry.update(
            job_id,
            status="done",
            percent=100,
            message="Extracción completada.",
            finished_at=datetime.now(timezone.utc).isoformat(),
            result=_safe_result(result),
        )
    except Exception as exc:  # noqa: BLE001
        import traceback

        traceback.print_exc()
        registry.update(
            job_id,
            status="error",
            message=f"Extracción falló: {exc}",
            error=str(exc),
            finished_at=datetime.now(timezone.utc).isoformat(),
        )


def _run_all_jobs(job_id: str) -> None:
    registry.update(job_id, status="running", started_at=datetime.now(timezone.utc).isoformat())
    try:
        progress = _make_progress(job_id)
        providers = _providers(progress)
        total = len(providers)
        completed = 0
        errors: List[str] = []
        for the_id in providers:
            completed += 1
            registry.update(
                job_id,
                stage=f"pipeline::{the_id}",
                step=completed,
                total=total,
                percent=min(99, int(round(completed / total * 100))),
            )
            try:
                providers[the_id].run()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{the_id}: {exc}")
        status = "error" if len(errors) == total else ("done" if not errors else "error")
        registry.update(
            job_id,
            status=status,
            percent=100,
            message=("Extracción completada." if not errors else f"Finalizado con errores: {'; '.join(errors)}"),
            error="; ".join(errors) if errors else None,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:  # noqa: BLE001
        registry.update(
            job_id,
            status="error",
            message=f"Extracción falló: {exc}",
            error=str(exc),
            finished_at=datetime.now(timezone.utc).isoformat(),
        )


def _safe_result(result: Any) -> Any:
    """Ensure results stored on a job are JSON-serializable primitives."""
    if result is None:
        return None
    if isinstance(result, dict):
        return {str(k): _safe_result(v) for k, v in result.items()}
    if isinstance(result, (list, tuple)):
        return [_safe_result(v) for v in result]
    try:
        json.dumps(result)
        return result
    except (TypeError, ValueError):
        return str(result)
