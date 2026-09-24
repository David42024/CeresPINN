"""Yield MLP with local agronomic monotonicity regularization.

Architecture: a multi-layer perceptron with two heads
  - `yield_head` : predicted maize yield (bu/acre)            [supervised]
  - `physics_head`: bounded auxiliary output retained for checkpoint compatibility

Regularization
  The implementation encodes two local sign expectations and one range check:

  1. Penalize positive d(yield)/d(temperature anomaly).
  2. Penalize negative d(yield)/d(seasonal precipitation).

  3. Check that the auxiliary sigmoid output remains in [0,1]. This term is
     structurally zero because the sigmoid already guarantees the range.

These terms are not a governing-equation residual and do not establish mass
conservation. The legacy class/function names are retained to load the published
checkpoint without changing its state-dict keys.
"""
from __future__ import annotations

from typing import List

import torch
import torch.nn as nn

from .config import TrainConfig


def _activation(name: str) -> nn.Module:
    return {
        "tanh": nn.Tanh(),
        "gelu": nn.GELU(),
        "relu": nn.ReLU(),
    }[name]


class CeresPINN(nn.Module):
    """Multilayer PINN with yield + physics heads."""

    def __init__(self, train_config: TrainConfig, input_dim: int) -> None:
        super().__init__()
        self.cfg = train_config
        self.input_dim = input_dim

        layers: List[nn.Module] = []
        in_features = input_dim
        for _ in range(train_config.hidden_layers):
            layers.append(nn.Linear(in_features, train_config.hidden_units))
            layers.append(_activation(train_config.activation))
            if train_config.dropout:
                layers.append(nn.Dropout(train_config.dropout))
            in_features = train_config.hidden_units

        self.features = nn.Sequential(*layers)
        self.yield_head = nn.Sequential(
            nn.Linear(in_features, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )
        self.physics_head = nn.Sequential(
            nn.Linear(in_features, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid(),  # water-availability proxy in [0,1]
        )

    def forward(self, x: torch.Tensor):
        h = self.features(x)
        yield_pred = self.yield_head(h).squeeze(-1)
        physics = self.physics_head(h).squeeze(-1)
        return yield_pred, physics


def physics_loss(
    model: nn.Module,
    x: torch.Tensor,
    train_config: TrainConfig,
) -> torch.Tensor:
    """Compute the physics-informed regularization term.

    term_1 : anti-physical yield growth with the heat feature
             penalty = sum(relu(dyield/dx_temp))  (should be <= 0 => zero cost)
    term_2 : hydro-consistency with the precipitation feature
             penalty = sum(relu(-dyield/dx_precip))  (more water never strictly hurts)
    term_3 : range feasibility of the water-availability proxy.
    """
    names = getattr(train_config, "feature_names", [])
    hot_idx = names.index("temp_anomaly_c") if "temp_anomaly_c" in names else None
    cold_idx = names.index("seasonal_precip_mm") if "seasonal_precip_mm" in names else None

    # Re-run a forward on a copy of the batch that is explicitly part of the graph,
    # so autograd can differentiate yield w.r.t. the inputs.
    xg = x.detach().requires_grad_(True)
    yield_pred, physics = model(xg)

    lam = train_config.loss_physics_weight
    loss = torch.zeros((), device=xg.device)

    if hot_idx is not None:
        dy_dtemp = torch.autograd.grad(
            yield_pred.sum(), xg, create_graph=True, retain_graph=True, allow_unused=True
        )[0][:, hot_idx]
        if dy_dtemp is not None:
            loss = loss + lam * torch.relu(dy_dtemp).mean()

    if cold_idx is not None:
        dy_dprecip = torch.autograd.grad(
            yield_pred.sum(), xg, create_graph=True, retain_graph=True, allow_unused=True
        )[0][:, cold_idx]
        if dy_dprecip is not None:
            loss = loss + lam * torch.relu(-dy_dprecip).mean()

    # Range feasibility: availability must stay within [0,1] (already sigmoid, soft).
    loss = loss + lam * (torch.relu(physics - 1.0).mean() + torch.relu(-physics).mean())

    return loss
