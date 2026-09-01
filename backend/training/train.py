"""Training loop and artifact persistence for CeresPINN."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

from .config import DataConfig, TrainConfig
from .dataset import build_dataset
from .pinn import CeresPINN, physics_loss


def _resolve_device(requested: str) -> str:
    if requested != "auto":
        return requested
    return "cuda" if torch.cuda.is_available() else "cpu"


def _compute_metrics(pred: torch.Tensor, target: torch.Tensor) -> Dict[str, float]:
    mse = float(torch.mean((pred - target) ** 2).item())
    mae = float(torch.mean(torch.abs(pred - target)).item())
    denom = target - target.mean() + 1e-9
    r2 = 1.0 - mse / float(torch.mean((target - target.mean()) ** 2).item() + 1e-9)
    return {"mse": round(mse, 4), "mae": round(mae, 4), "r2": round(r2, 4)}


def train(
    train_config: TrainConfig | None = None,
    data_config: DataConfig | None = None,
) -> Dict[str, Any]:
    """Run the CeresPINN training loop and persist the trained weights.

    Returns a summary dict with metrics, paths and device info.
    """
    train_config = train_config or TrainConfig()
    data_config = data_config or DataConfig()
    device = _resolve_device(train_config.device)

    torch.manual_seed(train_config.seed)
    np.random.seed(train_config.seed)

    X_train, y_train, X_test, y_test, info = build_dataset(train_config, data_config)

    # Normalize features (z-score) and targets (min-max) for training stability.
    mean = X_train.mean(axis=0)
    std = X_train.std(axis=0) + 1e-8
    X_train_n = (X_train - mean) / std
    X_test_n = (X_test - mean) / std

    y_min, y_max = float(y_train.min()), float(y_train.max()) + 1e-8
    y_train_n = (y_train - y_min) / (y_max - y_min)
    y_test_n = (y_test - y_min) / (y_max - y_min)

    model = CeresPINN(train_config, input_dim=X_train_n.shape[1]).to(device)
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=train_config.learning_rate,
        weight_decay=train_config.weight_decay,
    )
    mse_loss = nn.MSELoss()

    loader = DataLoader(
        TensorDataset(
            torch.tensor(X_train_n, dtype=torch.float32),
            torch.tensor(y_train_n, dtype=torch.float32),
        ),
        batch_size=train_config.batch_size,
        shuffle=True,
    )

    history: Dict[str, list] = {"train_loss": [], "test_mse": []}
    best_test_mse = float("inf")

    for epoch in tqdm(range(train_config.epochs), desc="CeresPINN training"):
        model.train()
        epoch_losses = []
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            yield_pred, _ = model(xb)
            data_loss = mse_loss(yield_pred, yb)
            phys = physics_loss(model, xb, train_config)
            regul = sum(p.pow(2).sum() for p in model.parameters())
            loss = (
                train_config.loss_data_weight * data_loss
                + phys
                + train_config.loss_reg_weight * regul
            )
            loss.backward()
            optimizer.step()
            epoch_losses.append(float(loss.detach().item()))

        history["train_loss"].append(float(np.mean(epoch_losses)))

        # Eval
        model.eval()
        with torch.no_grad():
            yp_test, _ = model(torch.tensor(X_test_n, dtype=torch.float32).to(device))
            test_mse = mse_loss(yp_test, torch.tensor(y_test_n, dtype=torch.float32).to(device)).item()
        history["test_mse"].append(test_mse)
        if test_mse < best_test_mse:
            best_test_mse = test_mse

    # Save artifacts
    train_config.output_dir.mkdir(parents=True, exist_ok=True)
    model_path = train_config.output_dir / "cerespinn_pinn.pt"
    torch.save(model.state_dict(), model_path)

    # Final metrics on original scale
    model.eval()
    with torch.no_grad():
        yp_train, _ = model(torch.tensor(X_train_n, dtype=torch.float32).to(device))
        yp_test, _ = model(torch.tensor(X_test_n, dtype=torch.float32).to(device))
        yp_train_orig = yp_train.cpu().numpy() * (y_max - y_min) + y_min
        yp_test_orig = yp_test.cpu().numpy() * (y_max - y_min) + y_min

    train_metrics = _compute_metrics(
        torch.tensor(yp_train_orig), torch.tensor(y_train)
    )
    test_metrics = _compute_metrics(torch.tensor(yp_test_orig), torch.tensor(y_test))

    metadata = {
        "model": "CeresPINN-maize-v2.5",
        "device": device,
        "input_dim": int(X_train_n.shape[1]),
        "feature_names": train_config.feature_names,
        "target_name": train_config.target_name,
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "epochs": train_config.epochs,
        "best_test_mse": round(best_test_mse, 6),
        "train_metrics": train_metrics,
        "test_metrics": test_metrics,
        "data_source": info.get("source"),
        "normalization": {"mean": mean.tolist(), "std": std.tolist(), "y_min": y_min, "y_max": y_max},
        "history": {k: v[-1] for k, v in history.items()},
    }

    metadata_path = train_config.output_dir / "cerespinn_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"\nCheckpoint: {model_path}")
    print(f"Metadata : {metadata_path}")
    print(f"Test     : {test_metrics}")

    return metadata


if __name__ == "__main__":
    train()
