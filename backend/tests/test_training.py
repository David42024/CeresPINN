"""Tests for the training pipeline (dataset assembly + physics loss)."""
from __future__ import annotations

import numpy as np
import pytest
import torch

from backend.training.config import DataConfig, TrainConfig
from backend.training.dataset import build_dataset, load_artifacts
from backend.training.pinn import CeresPINN, physics_loss


def test_build_dataset_returns_compatible_shapes(tmp_path):
    cfg = TrainConfig(epochs=1)
    data = DataConfig(base_dir=tmp_path)
    X_tr, y_tr, X_te, y_te, info = build_dataset(cfg, data)

    # No artifacts on disk -> synthetic fallback, still well-formed.
    assert info["source"] == "synthetic-fallback"
    assert X_tr.ndim == 2 and X_tr.shape[1] == len(cfg.feature_names)
    assert len(X_tr) == len(y_tr)
    assert len(X_te) == len(y_te)
    assert len(X_tr) + len(X_te) == info["n_rows"]


def test_dataset_is_deterministic(tmp_path):
    cfg = TrainConfig(epochs=1, seed=7)
    data = DataConfig(base_dir=tmp_path)
    a = build_dataset(cfg, data)
    b = build_dataset(cfg, data)
    np.testing.assert_array_equal(a[0], b[0])
    np.testing.assert_array_equal(a[1], b[1])


def test_missing_artifacts_handled(tmp_path):
    data = DataConfig(base_dir=tmp_path)
    art = load_artifacts(data)
    assert art["nass"] is None
    assert art["nex_summary"] is None


def test_pinn_forward_passes_to_two_heads():
    cfg = TrainConfig()
    model = CeresPINN(cfg, input_dim=len(cfg.feature_names))
    x = torch.randn(8, len(cfg.feature_names))
    y_pred, phys = model(x)
    assert y_pred.shape == (8,)
    assert phys.shape == (8,)
    # Physics head is sigmoid -> in [0,1].
    assert float(phys.detach().min()) >= 0.0 and float(phys.detach().max()) <= 1.0


def test_physics_loss_is_finite_and_differentiable():
    cfg = TrainConfig()
    model = CeresPINN(cfg, input_dim=len(cfg.feature_names))
    x = torch.randn(16, len(cfg.feature_names), requires_grad=True)
    loss = physics_loss(model, x, cfg)
    assert torch.isfinite(loss)
    # It must be backprop-able to the model parameters without error.
    loss.backward()
    grads = [p.grad for p in model.parameters() if p.requires_grad and p.grad is not None]
    # At least some parameters must receive a gradient through the physics terms.
    assert len(grads) > 0
    assert all(torch.isfinite(g).all() for g in grads)
