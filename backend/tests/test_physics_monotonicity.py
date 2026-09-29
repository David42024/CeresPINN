"""Analytic sign and weight checks for both supported feature schemas."""
import pytest
import torch
from backend.training.config import TrainConfig
from backend.training.pinn import physics_loss


class LinearYield(torch.nn.Module):
    def __init__(self, temperature, precipitation):
        super().__init__()
        self.weights = torch.nn.Parameter(torch.tensor([temperature, precipitation], dtype=torch.float32))

    def forward(self, x):
        return x @ self.weights, torch.sigmoid(x[:, 0] * 0)


@pytest.mark.parametrize('names', [
    ['temp_anomaly_c', 'seasonal_precip_mm'],
    ['season_tmax_mean_c', 'season_precip_mm'],
    ['season_temp_mean_c', 'season_precip_mm'],
])
def test_wrong_signs_penalized_with_weight_applied_once(names):
    model = LinearYield(2, -3)
    cfg = TrainConfig(feature_names=names, loss_physics_weight=0.4)
    loss = physics_loss(model, torch.zeros(4, 2), cfg)
    assert loss.item() == pytest.approx(2.0)
    loss.backward()
    assert model.weights.grad.tolist() == pytest.approx([0.4, -0.4])


def test_correct_signs_have_zero_penalty():
    model = LinearYield(-2, 3)
    cfg = TrainConfig(feature_names=['season_tmax_mean_c', 'season_precip_mm'])
    loss = physics_loss(model, torch.ones(4, 2), cfg)
    assert loss.item() == 0


def test_zero_weight_disables_regularization():
    model = LinearYield(2, -3)
    cfg = TrainConfig(feature_names=['season_tmax_mean_c', 'season_precip_mm'], loss_physics_weight=0)
    assert physics_loss(model, torch.ones(4, 2), cfg).item() == 0
