"""Physics-Informed Neural Network for specialized modeling.

This module provides a generalized PINN implementation adapted from CeresPINN
for use in ML Lab. The PINN can be configured with custom physics loss functions
for domain-specific applications.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

import torch
import torch.nn as nn


def _activation(name: str) -> nn.Module:
    """Get activation function by name."""
    return {
        "tanh": nn.Tanh(),
        "gelu": nn.GELU(),
        "relu": nn.ReLU(),
        "leaky_relu": nn.LeakyReLU(),
        "selu": nn.SELU(),
    }.get(name, nn.ReLU())


class PINNConfig:
    """Configuration for PINN model."""
    
    def __init__(
        self,
        hidden_layers: int = 3,
        hidden_units: int = 64,
        activation: str = "tanh",
        dropout: float = 0.0,
        loss_physics_weight: float = 0.1,
        feature_names: Optional[List[str]] = None,
    ):
        self.hidden_layers = hidden_layers
        self.hidden_units = hidden_units
        self.activation = activation
        self.dropout = dropout
        self.loss_physics_weight = loss_physics_weight
        self.feature_names = feature_names or []


class CeresPINN(nn.Module):
    """Physics-Informed Neural Network with yield + physics heads.
    
    This is the original CeresPINN architecture adapted for ML Lab.
    It has two heads:
    - yield_head: predicted target value (supervised)
    - physics_head: predicted physics state (regularized)
    """
    
    def __init__(self, config: PINNConfig, input_dim: int) -> None:
        super().__init__()
        self.cfg = config
        self.input_dim = input_dim
        
        # Build feature extractor
        layers: List[nn.Module] = []
        in_features = input_dim
        for _ in range(config.hidden_layers):
            layers.append(nn.Linear(in_features, config.hidden_units))
            layers.append(_activation(config.activation))
            if config.dropout > 0:
                layers.append(nn.Dropout(config.dropout))
            in_features = config.hidden_units
        
        self.features = nn.Sequential(*layers)
        
        # Build heads
        self.yield_head = nn.Sequential(
            nn.Linear(in_features, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )
        
        self.physics_head = nn.Sequential(
            nn.Linear(in_features, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid(),  # normalized proxy in [0,1]
        )
    
    def forward(self, x: torch.Tensor):
        """Forward pass through the network.
        
        Args:
            x: Input tensor
        
        Returns:
            Tuple of (yield_pred, physics)
        """
        h = self.features(x)
        yield_pred = self.yield_head(h).squeeze(-1)
        physics = self.physics_head(h).squeeze(-1)
        return yield_pred, physics


class GenericPINN(nn.Module):
    """Generic Physics-Informed Neural Network.
    
    This is a more flexible PINN that can be configured with custom
    architecture and custom physics loss functions.
    """
    
    def __init__(
        self,
        input_dim: int,
        output_dim: int = 1,
        hidden_layers: int = 3,
        hidden_units: int = 64,
        activation: str = "tanh",
        dropout: float = 0.0,
        physics_output_dim: int = 1,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.physics_output_dim = physics_output_dim
        
        # Build feature extractor
        layers: List[nn.Module] = []
        in_features = input_dim
        for _ in range(hidden_layers):
            layers.append(nn.Linear(in_features, hidden_units))
            layers.append(_activation(activation))
            if dropout > 0:
                layers.append(nn.Dropout(dropout))
            in_features = hidden_units
        
        self.features = nn.Sequential(*layers)
        
        # Build main output head
        self.output_head = nn.Sequential(
            nn.Linear(in_features, hidden_units // 2),
            _activation(activation),
            nn.Linear(hidden_units // 2, output_dim),
        )
        
        # Build physics head
        self.physics_head = nn.Sequential(
            nn.Linear(in_features, hidden_units // 2),
            _activation(activation),
            nn.Linear(hidden_units // 2, physics_output_dim),
            nn.Sigmoid(),  # normalized proxy in [0,1]
        )
    
    def forward(self, x: torch.Tensor):
        """Forward pass through the network.
        
        Args:
            x: Input tensor
        
        Returns:
            Tuple of (output, physics)
        """
        h = self.features(x)
        output = self.output_head(h)
        if self.output_dim == 1:
            output = output.squeeze(-1)
        physics = self.physics_head(h)
        if self.physics_output_dim == 1:
            physics = physics.squeeze(-1)
        return output, physics


def cerespinn_physics_loss(
    model: nn.Module,
    x: torch.Tensor,
    config: PINNConfig,
    temp_feature: str = "temp_anomaly_c",
    precip_feature: str = "seasonal_precip_mm",
) -> torch.Tensor:
    """Compute the CeresPINN-specific physics-informed regularization term.
    
    This loss enforces:
    1. Monotonicity: yield should not increase with temperature anomaly
    2. Hydro-consistency: yield should not decrease with precipitation
    3. Range feasibility: physics head should stay in [0,1]
    
    Args:
        model: PINN model
        x: Input tensor
        config: PINN configuration
        temp_feature: Name of temperature feature
        precip_feature: Name of precipitation feature
    
    Returns:
        Physics loss value
    """
    names = config.feature_names
    temp_idx = names.index(temp_feature) if temp_feature in names else None
    precip_idx = names.index(precip_feature) if precip_feature in names else None
    
    # Re-run forward with gradient tracking
    xg = x.detach().requires_grad_(True)
    yield_pred, physics = model(xg)
    
    lam = config.loss_physics_weight
    loss = torch.zeros((), device=xg.device)
    
    # Monotonicity: yield should not increase with temperature
    if temp_idx is not None:
        dy_dtemp = torch.autograd.grad(
            yield_pred.sum(), xg, create_graph=True, retain_graph=True, allow_unused=True
        )[0][:, temp_idx]
        if dy_dtemp is not None:
            loss = loss + lam * torch.relu(dy_dtemp).mean()
    
    # Hydro-consistency: yield should not decrease with precipitation
    if precip_idx is not None:
        dy_dprecip = torch.autograd.grad(
            yield_pred.sum(), xg, create_graph=True, retain_graph=True, allow_unused=True
        )[0][:, precip_idx]
        if dy_dprecip is not None:
            loss = loss + lam * torch.relu(-dy_dprecip).mean()
    
    # Range feasibility: physics head should stay in [0,1]
    loss = loss + lam * (torch.relu(physics - 1.0).mean() + torch.relu(-physics).mean())
    
    return loss


def generic_physics_loss(
    model: nn.Module,
    x: torch.Tensor,
    physics_loss_fn: Optional[Callable] = None,
    physics_weight: float = 0.1,
) -> torch.Tensor:
    """Compute a generic physics-informed regularization term.
    
    Args:
        model: PINN model
        x: Input tensor
        physics_loss_fn: Custom physics loss function
        physics_weight: Weight for physics loss
    
    Returns:
        Physics loss value
    """
    if physics_loss_fn is None:
        # Default: range feasibility for physics head
        xg = x.detach().requires_grad_(True)
        _, physics = model(xg)
        loss = physics_weight * (torch.relu(physics - 1.0).mean() + torch.relu(-physics).mean())
        return loss
    else:
        return physics_weight * physics_loss_fn(model, x)
