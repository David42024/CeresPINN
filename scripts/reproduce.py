"""One-command, offline reproduction of the CeresPINN Q1 evidence package."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reproducibility" / "manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def data_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.reader(handle)) - 1


def verify_inputs() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        path = ROOT / entry["path"]
        if not path.is_file():
            raise FileNotFoundError(f"Required reproducibility input is missing: {entry['path']}")
        if path.stat().st_size != entry["bytes"]:
            raise RuntimeError(f"Byte-size mismatch for {entry['path']}")
        actual_hash = sha256(path)
        if actual_hash != entry["sha256"]:
            raise RuntimeError(
                f"SHA-256 mismatch for {entry['path']}: {actual_hash} != {entry['sha256']}"
            )
        if "data_rows" in entry and data_rows(path) != entry["data_rows"]:
            raise RuntimeError(f"Row-count mismatch for {entry['path']}")
    print(f"Verified {len(manifest['files'])} immutable inputs against {MANIFEST.relative_to(ROOT)}")
    return manifest


def run(relative_script: str) -> None:
    command = [sys.executable, str(ROOT / relative_script)]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def verify_outputs(manifest: dict) -> None:
    missing = [path for path in manifest["generated_outputs"] if not (ROOT / path).is_file()]
    if missing:
        raise FileNotFoundError(f"Reproduction did not create expected outputs: {missing}")

    temporal_path = (
        ROOT
        / "docs/q1_artifacts/temporal/temporal_validation_1990_2017_to_2018_2025.json"
    )
    temporal = json.loads(temporal_path.read_text(encoding="utf-8"))
    protocol = temporal["protocol"]
    if protocol["train_years"] != list(range(1990, 2018)):
        raise RuntimeError("Unexpected prospective training period")
    if protocol["test_years"] != list(range(2018, 2026)):
        raise RuntimeError("Unexpected prospective test period")
    if protocol["leakage_check"] != "passed":
        raise RuntimeError("Prospective validation leakage check did not pass")
    print(f"Verified {len(manifest['generated_outputs'])} generated outputs")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify committed inputs and existing outputs without retraining.",
    )
    args = parser.parse_args()

    manifest = verify_inputs()
    if not args.verify_only:
        run("scripts/generate_q1_revision_artifacts.py")
        run("scripts/generate_q1_extended_audit.py")
        run("scripts/run_temporal_validation.py")
    verify_outputs(manifest)
    print("CeresPINN reproducibility pipeline completed successfully.")


if __name__ == "__main__":
    main()
