"""Neural network models for ML Lab.

This module provides implementations of neural network models including
MLP (Multi-Layer Perceptron) for tabular data.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import torch
import torch.nn as nn
from sklearn.base import BaseEstimator, ClassifierMixin, RegressorMixin

from ..core.model_catalog import BaseModel


class MLPConfig:
    """Configuration for MLP model."""
    
    def __init__(
        self,
        hidden_layers: int = 2,
        hidden_units: int = 64,
        activation: str = "relu",
        dropout: float = 0.0,
        batch_norm: bool = False,
        output_activation: Optional[str] = None,
    ):
        self.hidden_layers = hidden_layers
        self.hidden_units = hidden_units
        self.activation = activation
        self.dropout = dropout
        self.batch_norm = batch_norm
        self.output_activation = output_activation


class MLP(nn.Module):
    """Multi-Layer Perceptron neural network."""
    
    def __init__(
        self,
        input_dim: int,
        output_dim: int = 1,
        config: Optional[MLPConfig] = None,
    ) -> None:
        super().__init__()
        self.config = config or MLPConfig()
        self.input_dim = input_dim
        self.output_dim = output_dim
        
        # Build layers
        layers: List[nn.Module] = []
        in_features = input_dim
        
        for i in range(self.config.hidden_layers):
            layers.append(nn.Linear(in_features, self.config.hidden_units))
            
            if self.config.batch_norm:
                layers.append(nn.BatchNorm1d(self.config.hidden_units))
            
            layers.append(self._get_activation(self.config.activation))
            
            if self.config.dropout > 0:
                layers.append(nn.Dropout(self.config.dropout))
            
            in_features = self.config.hidden_units
        
        # Output layer
        layers.append(nn.Linear(in_features, output_dim))
        
        if self.config.output_activation:
            layers.append(self._get_activation(self.config.output_activation))
        
        self.network = nn.Sequential(*layers)
    
    def _get_activation(self, name: str) -> nn.Module:
        """Get activation function by name."""
        activations = {
            "relu": nn.ReLU(),
            "leaky_relu": nn.LeakyReLU(),
            "tanh": nn.Tanh(),
            "sigmoid": nn.Sigmoid(),
            "gelu": nn.GELU(),
            "selu": nn.SELU(),
        }
        return activations.get(name, nn.ReLU())
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        return self.network(x)


class MLPClassifier(BaseModel, BaseEstimator, ClassifierMixin):
    """MLP classifier wrapper for scikit-learn compatibility."""
    
    def __init__(
        self,
        hyperparameters: Optional[Dict[str, Any]] = None,
        input_dim: Optional[int] = None,
        n_classes: int = 2,
    ):
        super().__init__(hyperparameters)
        self.input_dim = input_dim
        self.n_classes = n_classes
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    def _build_model(self, input_dim: int) -> None:
        """Build the MLP model."""
        config = MLPConfig(
            hidden_layers=self.hyperparameters.get("hidden_layers", 2),
            hidden_units=self.hyperparameters.get("hidden_units", 64),
            activation=self.hyperparameters.get("activation", "relu"),
            dropout=self.hyperparameters.get("dropout", 0.0),
            batch_norm=self.hyperparameters.get("batch_norm", False),
        )
        self.model = MLP(input_dim, self.n_classes, config).to(self.device)
        self.input_dim = input_dim
    
    def fit(self, X, y, epochs: int = 100, batch_size: int = 32, learning_rate: float = 0.001):
        """Fit the model to training data."""
        import torch.optim as optim
        
        X = self._to_tensor(X)
        y = self._to_tensor(y)
        
        if self.model is None:
            self._build_model(X.shape[1])
        
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.CrossEntropyLoss()
        
        self.model.train()
        for epoch in range(epochs):
            # Simple batch training (for full dataset training, use DataLoader)
            optimizer.zero_grad()
            outputs = self.model(X)
            loss = criterion(outputs, y.long())
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
            outputs = self.model(X)
            predictions = torch.argmax(outputs, dim=1)
        return predictions.cpu().numpy()
    
    def predict_proba(self, X):
        """Predict class probabilities."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        X = self._to_tensor(X)
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(X)
            probabilities = torch.softmax(outputs, dim=1)
        return probabilities.cpu().numpy()
    
    def get_feature_importance(self):
        """Get feature importance (not available for MLP)."""
        return None
    
    def _to_tensor(self, data):
        """Convert data to tensor."""
        if isinstance(data, np.ndarray):
            return torch.FloatTensor(data).to(self.device)
        return torch.FloatTensor(data).to(self.device)


class MLPRegressor(BaseModel, BaseEstimator, RegressorMixin):
    """MLP regressor wrapper for scikit-learn compatibility."""
    
    def __init__(
        self,
        hyperparameters: Optional[Dict[str, Any]] = None,
        input_dim: Optional[int] = None,
    ):
        super().__init__(hyperparameters)
        self.input_dim = input_dim
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    def _build_model(self, input_dim: int) -> None:
        """Build the MLP model."""
        config = MLPConfig(
            hidden_layers=self.hyperparameters.get("hidden_layers", 2),
            hidden_units=self.hyperparameters.get("hidden_units", 64),
            activation=self.hyperparameters.get("activation", "relu"),
            dropout=self.hyperparameters.get("dropout", 0.0),
            batch_norm=self.hyperparameters.get("batch_norm", False),
            output_activation=None,  # No activation for regression
        )
        self.model = MLP(input_dim, 1, config).to(self.device)
        self.input_dim = input_dim
    
    def fit(self, X, y, epochs: int = 100, batch_size: int = 32, learning_rate: float = 0.001):
        """Fit the model to training data."""
        import torch.optim as optim
        
        X = self._to_tensor(X)
        y = self._to_tensor(y)
        
        if self.model is None:
            self._build_model(X.shape[1])
        
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()
        
        self.model.train()
        for epoch in range(epochs):
            # Simple batch training
            optimizer.zero_grad()
            outputs = self.model(X).squeeze()
            loss = criterion(outputs, y)
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
            outputs = self.model(X).squeeze()
        return outputs.cpu().numpy()
    
    def predict_proba(self, X):
        """Predict class probabilities (not applicable for regression)."""
        return None
    
    def get_feature_importance(self):
        """Get feature importance (not available for MLP)."""
        return None
    
    def _to_tensor(self, data):
        """Convert data to tensor."""
        if isinstance(data, np.ndarray):
            return torch.FloatTensor(data).to(self.device)
        return torch.FloatTensor(data).to(self.device)
