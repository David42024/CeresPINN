"""CeresPINN training module.

Responsibilities:
  - assimilate the extracted public datasets (USDA NASS yields, CHIRPS + NASA
    NEX-GDDP climate) into a clean feature/target matrix,
  - define the Physics-Informed Neural Network (PDE-consistent residual losses),
  - run the training loop and persist the learned weights.

Public surface:
  from backend.training.dataset import build_dataset, load_artifacts
  from backend.training.pinn import CeresPINN, physics_loss
  from backend.training.train import train
"""
from .config import DataConfig, TrainConfig
from .dataset import build_dataset, load_artifacts
from .pinn import CeresPINN, physics_loss
from .train import train

__all__ = [
    "DataConfig",
    "TrainConfig",
    "build_dataset",
    "load_artifacts",
    "CeresPINN",
    "physics_loss",
    "train",
]
