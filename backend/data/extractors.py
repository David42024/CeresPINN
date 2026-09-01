"""CLI orchestrator for CeresPINN data extraction pipelines.

Usage:
    python -m backend.data.extractors all          # run every provider
    python -m backend.data.extractors chirps       # CHIRPS only
    python -m backend.data.extractors nass         # USDA NASS only
    python -m backend.data.extractors nex          # NASA NEX-GDDP only

Environment switches:
    CERESPINN_DRY_RUN=1|0   (default 1 = offline planning / no network writes)
    NASS_API_KEY=...        (required for real USDA NASS extraction)
    CERESPINN_DATA_DIR=...  (override output root, default: backend/data)
"""
from __future__ import annotations

import sys
from typing import Dict, List, Optional

from .config import settings
from .chirps import run_chirps
from .nass import run_nass
from .nex_gddp import run_nex


PROVIDERS: Dict[str, object] = {
    "chirps": run_chirps,
    "nass": run_nass,
    "nex": run_nex,
}


def run_all() -> None:
    dry_run = settings.extraction.dry_run
    print("=" * 64)
    print("CeresPINN Data Extraction")
    print(f"Mode: {'DRY-RUN (offline, no real downloads)' if dry_run else 'LIVE (network)'}")
    print(f"Target dir: {settings.paths.base_dir}")
    print("=" * 64)

    results: List[str] = []
    for name, fn in PROVIDERS.items():
        print(f"\n>>> Pipeline: {name}")
        try:
            summary = fn(settings)
            for key, value in summary.items():
                print(f"    {key}: {value}")
            results.append(f"{name}: OK")
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"    ERROR: {exc}")
            results.append(f"{name}: ERROR ({exc})")

    print("\n" + "=" * 64)
    print("\n".join(results))
    print("=" * 64)


def run_single(name: str) -> None:
    fn = PROVIDERS.get(name)
    if fn is None:
        print(f"Unknown provider: {name}. Available: {', '.join(PROVIDERS)}")
        sys.exit(2)
    summary = fn(settings)
    for key, value in summary.items():
        print(f"{name}.{key}: {value}")


def main(argv: Optional[List[str]] = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("Usage: python -m backend.data.extractors [all|chirps|nass|nex]")
        sys.exit(1)
    target = argv[0]
    if target == "all":
        run_all()
    else:
        run_single(target)


if __name__ == "__main__":
    main()
