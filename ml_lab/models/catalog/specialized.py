"""Specialized models for ML Lab.

This module provides wrappers for specialized domain-specific models,
including the CeresPINN physics-informed neural network.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import torch
import torch.nn as nn
from sklearn.base import BaseEstimator, RegressorMixin

from core.model_catalog import BaseModel
from models.pinn import CeresPINN, PINNConfig, cerespinn_physics_loss


class CeresPINNModel(BaseModel, BaseEstimator, RegressorMixin):
    """CeresPINN model wrapper for ML Lab.
    
    This wrapper integrates the CeresPINN physics-informed neural network
    as a specialized model in the ML Lab catalog. It provides scikit-learn
    compatible interface for training and inference.
    """
    
    def __init__(
        self,
        hyperparameters: Optional[Dict[str, Any]] = None,
        input_dim: Optional[int] = None,
        feature_names: Optional[List[str]] = None,
        physics_weight: float = 0.1,
    ):
        super().__init__(hyperparameters)
        self.input_dim = input_dim
        self.feature_names = feature_names or []
        self.physics_weight = physics_weight
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._y_min = 0.0
        self._y_span = 1.0

        # PINN configuration (accepts catalog default keys hidden_dim/num_layers
        # as aliases of hidden_units/hidden_layers)
        hp = hyperparameters or {}
        hidden_layers = hp.get("hidden_layers", hp.get("num_layers", 3))
        hidden_units = hp.get("hidden_units", hp.get("hidden_dim", 64))
        self.pinn_config = PINNConfig(
            hidden_layers=hidden_layers,
            hidden_units=hidden_units,
            activation=hp.get("activation", "tanh"),
            dropout=hp.get("dropout", 0.0),
            loss_physics_weight=physics_weight,
            feature_names=self.feature_names,
        )
    
    def _build_model(self, input_dim: int) -> None:
        """Build the CeresPINN model."""
        self.model = CeresPINN(self.pinn_config, input_dim).to(self.device)
        self.input_dim = input_dim
    
    def fit(
        self,
        X,
        y,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.001,
        physics_weight: Optional[float] = None,
    ):
        """Fit the CeresPINN model to training data.
        
        Args:
            X: Training features
            y: Training targets
            epochs: Number of training epochs
            batch_size: Batch size for training
            learning_rate: Learning rate for optimizer
            physics_weight: Weight for physics loss (overrides init value)
        """
        import torch.optim as optim
        from torch.utils.data import DataLoader, TensorDataset

        # Training schedule may come from ML Lab UI via hyperparameters
        hp = self.hyperparameters or {}
        epochs = int(hp.get("epochs", epochs))
        batch_size = int(hp.get("batch_size", batch_size))
        learning_rate = float(hp.get("learning_rate", learning_rate))

        # Min-max target normalization (mirrors backend/train.py): keeps the
        # MSE + physics loss on a stable scale; predict() denormalizes.
        import numpy as np

        y_arr = np.asarray(y, dtype=float)
        self._y_min = float(y_arr.min())
        self._y_span = float(y_arr.max() - y_arr.min()) or 1.0
        y_n = (y_arr - self._y_min) / self._y_span

        X = self._to_tensor(X)
        y = self._to_tensor(y_n)
        
        if self.model is None:
            self._build_model(X.shape[1])
        
        # Update physics weight if provided
        if physics_weight is not None:
            self.pinn_config.loss_physics_weight = physics_weight
        
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()
        
        # Create data loader
        dataset = TensorDataset(X, y)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        self.model.train()
        for epoch in range(epochs):
            total_loss = 0.0
            for batch_X, batch_y in loader:
                optimizer.zero_grad()
                
                # Forward pass
                yield_pred, physics = self.model(batch_X)
                
                # Data loss
                data_loss = criterion(yield_pred, batch_y)
                
                # Physics loss
                phys_loss = cerespinn_physics_loss(self.model, batch_X, self.pinn_config)
                
                # Combined loss
                loss = data_loss + phys_loss
                
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
        
        self.is_fitted = True
        return self
    
    def predict(self, X):
        """Make predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        X = self._to_tensor(X)
        self.model.eval()
        with torch.no_grad():
            yield_pred, _ = self.model(X)
        return yield_pred.cpu().numpy() * self._y_span + self._y_min
    
    def predict_proba(self, X):
        """Predict class probabilities (not applicable for regression)."""
        return None
    
    def get_feature_importance(self):
        """Get feature importance (not available for PINN)."""
        return None
    
    def get_physics_output(self, X):
        """Get physics head output (water-stress proxy).
        
        Args:
            X: Input features
        
        Returns:
            Physics head output
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        X = self._to_tensor(X)
        self.model.eval()
        with torch.no_grad():
            _, physics = self.model(X)
        return physics.cpu().numpy()
    
    def _to_tensor(self, data):
        """Convert data to tensor."""
        if isinstance(data, np.ndarray):
            return torch.FloatTensor(data).to(self.device)
        return torch.FloatTensor(data).to(self.device)


class GenericPINNModel(BaseModel, BaseEstimator, RegressorMixin):
    """Generic PINN model wrapper for ML Lab.
    
    This wrapper provides a generic physics-informed neural network
    that can be configured with custom physics loss functions.
    """
    
    def __init__(
        self,
        hyperparameters: Optional[Dict[str, Any]] = None,
        input_dim: Optional[int] = None,
        output_dim: int = 1,
        physics_loss_fn: Optional[callable] = None,
        physics_weight: float = 0.1,
    ):
        super().__init__(hyperparameters)
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.physics_loss_fn = physics_loss_fn
        self.physics_weight = physics_weight
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._y_min = 0.0
        self._y_span = 1.0
    
    def _build_model(self, input_dim: int) -> None:
        """Build the generic PINN model."""
        from models.pinn import GenericPINN
        
        self.model = GenericPINN(
            input_dim=input_dim,
            output_dim=self.output_dim,
            hidden_layers=self.hyperparameters.get("hidden_layers", 3) if self.hyperparameters else 3,
            hidden_units=self.hyperparameters.get("hidden_units", 64) if self.hyperparameters else 64,
            activation=self.hyperparameters.get("activation", "tanh") if self.hyperparameters else "tanh",
            dropout=self.hyperparameters.get("dropout", 0.0) if self.hyperparameters else 0.0,
        ).to(self.device)
        self.input_dim = input_dim
    
    def fit(
        self,
        X,
        y,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.001,
        physics_weight: Optional[float] = None,
    ):
        """Fit the generic PINN model to training data."""
        import torch.optim as optim
        from torch.utils.data import DataLoader, TensorDataset
        from models.pinn import generic_physics_loss

        # Training schedule may come from ML Lab UI via hyperparameters
        hp = self.hyperparameters or {}
        epochs = int(hp.get("epochs", epochs))
        batch_size = int(hp.get("batch_size", batch_size))
        learning_rate = float(hp.get("learning_rate", learning_rate))

        # Min-max target normalization (mirrors backend/train.py)
        import numpy as np

        y_arr = np.asarray(y, dtype=float)
        self._y_min = float(y_arr.min())
        self._y_span = float(y_arr.max() - y_arr.min()) or 1.0
        y_n = (y_arr - self._y_min) / self._y_span

        X = self._to_tensor(X)
        y = self._to_tensor(y_n)
        
        if self.model is None:
            self._build_model(X.shape[1])
        
        # Update physics weight if provided
        if physics_weight is not None:
            self.physics_weight = physics_weight
        
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()
        
        # Create data loader
        dataset = TensorDataset(X, y)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        self.model.train()
        for epoch in range(epochs):
            for batch_X, batch_y in loader:
                optimizer.zero_grad()
                
                # Forward pass
                output, physics = self.model(batch_X)
                
                # Data loss
                data_loss = criterion(output.squeeze(), batch_y)
                
                # Physics loss
                phys_loss = generic_physics_loss(
                    self.model, batch_X, self.physics_loss_fn, self.physics_weight
                )
                
                # Combined loss
                loss = data_loss + phys_loss
                
                loss.backward()
                optimizer.step()
        
        self.is_fitted = True
        return self
    
    def predict(self, X):
        """Make predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        X = self._to_tensor(X)
        self.model.eval()
        with torch.no_grad():
            output, _ = self.model(X)
        return output.cpu().numpy() * self._y_span + self._y_min
    
    def predict_proba(self, X):
        """Predict class probabilities (not applicable for regression)."""
        return None
    
    def get_feature_importance(self):
        """Get feature importance (not available for PINN)."""
        return None
    
    def get_physics_output(self, X):
        """Get physics head output.
        
        Args:
            X: Input features
        
        Returns:
            Physics head output
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        X = self._to_tensor(X)
        self.model.eval()
        with torch.no_grad():
            _, physics = self.model(X)
        return physics.cpu().numpy()
    
    def _to_tensor(self, data):
        """Convert data to tensor."""
        if isinstance(data, np.ndarray):
            return torch.FloatTensor(data).to(self.device)
        return torch.FloatTensor(data).to(self.device)
