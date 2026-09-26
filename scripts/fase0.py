import hashlib
import json
import os
import subprocess
from datetime import datetime

# Set up paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "backend", "models")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
REPRO_DIR = os.path.join(BASE_DIR, "reproducibility")
TEST_FIXTURES_DIR = os.path.join(BASE_DIR, "tests", "fixtures", "model_v2")

os.makedirs(REPRO_DIR, exist_ok=True)
os.makedirs(TEST_FIXTURES_DIR, exist_ok=True)

# Helper for SHA256
def get_sha256(file_path):
    if not os.path.exists(file_path):
        return None
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def run_cmd(cmd, cwd):
    try:
        result = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"

# 1. Hashes
files_to_hash = [
    os.path.join(DATA_DIR, "cerespinn_training_iowa.csv"),
    os.path.join(DATA_DIR, "cerespinn_training_preprocessed.csv"),
    os.path.join(MODELS_DIR, "cerespinn_pinn.pt"),
    os.path.join(MODELS_DIR, "cerespinn_metadata.json"),
    os.path.join(DOCS_DIR, "q1_artifacts", "temporal", "temporal_validation_1990_2017_to_2018_2025.json"),
    os.path.join(DOCS_DIR, "q1_artifacts", "same_split_baseline_comparison.csv")
]

hashes = {}
for file_path in files_to_hash:
    rel_path = os.path.relpath(file_path, BASE_DIR)
    hashes[rel_path] = get_sha256(file_path)

# 2. Get API responses
print("Getting API responses...")
import sys
sys.path.insert(0, BASE_DIR)
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

status_resp = client.get("/api/model/status")
status_data = status_resp.json()

# Fixed cases for /api/simulate
cases = [
    {
        "year": 2024,
        "state": "Iowa",
        "county": "Story",
        "scenario": "SSP2-4.5",
        "irrigation": "rainfed",
        "nitrogen_rate": 150,
        "management_practice": "conventional",
        "crop_variety": "default"
    },
    {
        "year": 2025,
        "state": "Iowa",
        "county": "Polk",
        "scenario": "SSP5-8.5",
        "irrigation": "full",
        "nitrogen_rate": 200,
        "management_practice": "conservation",
        "crop_variety": "drought_tolerant"
    }
]

simulate_responses = []
for idx, case in enumerate(cases):
    # Depending on schema, let's see what simulate endpoint expects...
    # Usually it's state, scenario, year or something.
    try:
        resp = client.post("/api/simulate", json=case)
        resp_data = resp.json()
        simulate_responses.append({
            "case_index": idx,
            "request": case,
            "response": resp_data,
            "status_code": resp.status_code
        })
    except Exception as e:
         simulate_responses.append({
            "case_index": idx,
            "request": case,
            "error": str(e)
        })

# Save fixtures
fixtures_path = os.path.join(TEST_FIXTURES_DIR, "api_responses.json")
with open(fixtures_path, "w") as f:
    json.dump({
        "status": status_data,
        "simulate_cases": simulate_responses
    }, f, indent=2)

# 3. Get dependencies
print("Getting dependencies...")
python_deps = run_cmd("pip freeze", cwd=BASE_DIR)

print("Getting git commit...")
git_commit = run_cmd("git rev-parse HEAD", cwd=BASE_DIR)

# 4. Manifest
manifest = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "git_commit": git_commit,
    "python_dependencies": python_deps.split("\n"),
    "files_sha256": hashes,
    "api_fixtures": "tests/fixtures/model_v2/api_responses.json"
}

manifest_path = os.path.join(REPRO_DIR, "baseline_v2_manifest.json")
with open(manifest_path, "w") as f:
    json.dump(manifest, f, indent=2)

print("Manifest created successfully.")
