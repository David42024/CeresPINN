import sys
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from backend.training.pinn import CeresPINN
from backend.training.config import TrainConfig

DATA_PATH = PROJECT_ROOT / "backend" / "data" / "processed" / "canonical_panel.parquet"
df = pd.read_parquet(DATA_PATH)

feature_names = ['year', 'season_temp_mean_c', 'season_tmax_mean_c', 'season_precip_mm', 'gdd', 'cdd', 'vpd_mean_kpa']
feature_names = [f for f in feature_names if f in df.columns]

X_df = df[feature_names].fillna(0)
y_df = df['yield_kg_ha'].fillna(0)

scaler_X = StandardScaler()
scaler_y = StandardScaler()

X_scaled = scaler_X.fit_transform(X_df)
y_scaled = scaler_y.fit_transform(y_df.values.reshape(-1, 1))

X_tensor = torch.tensor(X_scaled, dtype=torch.float32, requires_grad=True)
y_tensor = torch.tensor(y_scaled, dtype=torch.float32).squeeze(-1)

best_r2 = -999
best_params = {}

epochs_list = [300, 500, 800]
lr_list = [0.001, 0.005, 0.01]
physics_list = [0.1, 0.5, 0.9]

print("Starting grid search for PyTorch PINN...")

for ep in epochs_list:
    for lr in lr_list:
        for pw in physics_list:
            cfg = TrainConfig()
            model = CeresPINN(train_config=cfg, input_dim=len(feature_names))
            optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
            criterion = nn.MSELoss()
            
            for epoch in range(1, ep + 1):
                model.train()
                optimizer.zero_grad()
                yield_pred, physics_penalty = model(X_tensor)
                mse_loss = criterion(yield_pred, y_tensor)
                loss = mse_loss + (pw * physics_penalty.mean())
                loss.backward()
                optimizer.step()
                
            model.eval()
            with torch.no_grad():
                final_pred_scaled, _ = model(X_tensor)
                final_pred = scaler_y.inverse_transform(final_pred_scaled.numpy().reshape(-1, 1))
            
            r2 = r2_score(y_df, final_pred)
            print(f"Ep: {ep}, LR: {lr}, PW: {pw} => R2: {r2:.4f}")
            
            if r2 > best_r2:
                best_r2 = r2
                best_params = {'epochs': ep, 'lr': lr, 'physics_weight': pw}

print(f"\\nBEST PARAMS: {best_params} with R2: {best_r2:.4f}")
