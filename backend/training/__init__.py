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
# NOTE: `pinn` and `train` import torch eagerly. To keep the FastAPI runtime
# importable without PyTorch (it only needs the config for feature metadata), we
# import only the torch-free submodules here. torch-dependent symbols (CeresPINN,
# physics_loss, train) are imported lazily inside the modules that use them.
from .config import DataConfig, TrainConfig
from .dataset import build_dataset, load_artifacts

__all__ = [
    "DataConfig",
    "TrainConfig",
    "build_dataset",
    "load_artifacts",
    "CeresPINN",
    "physics_loss",
    "train",
]
