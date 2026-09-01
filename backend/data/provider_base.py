"""Abstract base class shared by every data provider.

Each provider implements a fetch pipeline (download -> snapshot -> metadata log) and
exposes a `run()` entrypoint. This enforces a uniform contract so the CLI orchestrator
in `extractors.py` can drive all three datasets identically.
"""
from __future__ import annotations

import abc
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class ExtractionError(RuntimeError):
    """Raised when a provider cannot complete its extraction."""


class BaseProvider(abc.ABC):
    """Base class with common helpers (logging, manifests, dry-run)."""

    name: str = "base"

    def __init__(self, config: Any, progress: Optional[Any] = None) -> None:
        self.config = config
        self.progress = progress or (lambda *a, **k: None)
        self.log: List[Dict[str, Any]] = []

    # -- Helpers -------------------------------------------------------------
    def log_step(self, message: str, **kwargs: Any) -> None:
        entry = {"time": datetime.now(timezone.utc).isoformat(), "message": message}
        entry.update(kwargs)
        self.log.append(entry)
        print(f"[{self.name}] {message}")

    def set_progress(self, step: int, total: int, stage: str) -> None:
        """Report coarse progress (event-driven) to a registered callback."""
        try:
            self.progress({"step": step, "total": total, "stage": stage})
        except Exception:  # noqa: BLE001 - progress reporting must never break extraction
            pass

    def write_snapshot(self, path: Path, data: Any) -> None:
        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".json":
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        elif path.suffix == ".csv":
            data.to_csv(path, index=False)
        else:
            data.to_csv(path, index=False)

    def write_manifest(self, directory: Path, records: int, extra: Optional[Dict[str, Any]] = None) -> None:
        manifest = {
            "provider": self.name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "records": records,
            "dry_run": self.config.extraction.dry_run,
        }
        if extra:
            manifest.update(extra)
        manifest_path = directory / f"{self.name}_manifest.json"
        self.write_snapshot(manifest_path, manifest)
        return manifest_path

    def throttled(self) -> None:
        # Be polite to public APIs.
        time.sleep(1.0)

    # -- Public interface ----------------------------------------------------
    def run(self) -> Dict[str, Any]:
        """Execute the extraction and return a summary dict."""
        start = time.time()
        self.log_step(f"Starting {self.name} extraction (dry_run={self.config.extraction.dry_run})")
        try:
            result = self.extract()
        except ExtractionError as exc:  # pragma: no cover - defensive
            self.log_step(f"Extraction failed: {exc}")
            raise
        elapsed = round(time.time() - start, 2)
        summary = {"provider": self.name, "elapsed_seconds": elapsed, **result}
        self.log_step(f"Finished {self.name} in {elapsed}s")
        return summary

    @abc.abstractmethod
    def extract(self) -> Dict[str, Any]:
        """Perform the dataset-specific extraction."""
