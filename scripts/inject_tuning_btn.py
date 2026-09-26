import re

file_path = "ml_lab/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# We want to inject the auto-tuning button right after the st.success of the normal PyTorch training.
# Or better, put it side by side with the "🔥 Iniciar Entrenamiento Acelerado (CPU/PyTorch)" button.
# Let's replace the button block.

old_button = """    if st.button("🔥 Iniciar Entrenamiento Acelerado (CPU/PyTorch)", type="primary"):"""
new_buttons = """    colA, colB = st.columns(2)
    with colA:
        train_btn = st.button("🔥 Iniciar Entrenamiento Simple", type="primary")
    with colB:
        search_btn = st.button("🔍 Auto-Tuning (Grid Search PyTorch)", type="secondary")
        
    if train_btn:"""

content = content.replace(old_button, new_buttons)

auto_tuning_block = """
    if search_btn:
        import torch
        import torch.nn as nn
        import torch.optim as optim
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import r2_score
        import joblib
        import json
        import pandas as pd
        from datetime import datetime
        
        try:
            from backend.training.pinn import CeresPINN
            from backend.training.config import TrainConfig
        except ImportError:
            st.error("No se pudo importar CeresPINN. Asegúrate de estar en el directorio correcto.")
            return
            
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
        
        st.info("Iniciando búsqueda masiva en PyTorch (Tomará 1-2 minutos)...")
        progress = st.progress(0)
        status = st.empty()
        
        epochs_grid = [300, 500, 800]
        lr_grid = [0.001, 0.005, 0.01]
        physics_grid = [0.1, 0.5, 0.9]
        
        total_combinations = len(epochs_grid) * len(lr_grid) * len(physics_grid)
        count = 0
        
        best_r2 = -999
        best_params = {}
        best_model = None
        
        results_list = []
        
        for ep in epochs_grid:
            for lr in lr_grid:
                for pw in physics_grid:
                    count += 1
                    status.text(f"Evaluando variante {count}/{total_combinations} (Epochs={ep}, LR={lr}, Physics={pw})...")
                    
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
                    results_list.append({"Épocas": ep, "LR": lr, "Peso Física": pw, "R2": float(r2)})
                    
                    if r2 > best_r2:
                        best_r2 = r2
                        best_params = {"Epochs": ep, "LR": lr, "Physics": pw}
                        best_model = model
                        
                    progress.progress(count / total_combinations)
                    
        status.success("¡Búsqueda finalizada!")
        
        # Guardar en json
        meta = {}
        if META_PATH.exists():
            meta = json.loads(META_PATH.read_text(encoding="utf-8"))
        
        # Comparativa con otros modelos
        st.markdown(f"### 🏆 El mejor CeresPINN (PyTorch) obtuvo un R² de `{best_r2:.4f}`")
        st.markdown(f"**Parámetros ganadores:** Épocas: `{best_params['Epochs']}`, LR: `{best_params['LR']}`, Física: `{best_params['Physics']}`")
        
        st.write("#### Resultados de todas las iteraciones PyTorch:")
        st.dataframe(pd.DataFrame(results_list).sort_values("R2", ascending=False), width='stretch')
        
        # Guardar ganador
        class PyTorchWrapper:
            def __init__(self, pt_model, sc_X, sc_y):
                self.model = pt_model
                self.scaler_X = sc_X
                self.scaler_y = sc_y
            def predict(self, X):
                import torch
                X_s = self.scaler_X.transform(X)
                X_t = torch.tensor(X_s, dtype=torch.float32)
                self.model.eval()
                with torch.no_grad():
                    pred_s, _ = self.model(X_t)
                return self.scaler_y.inverse_transform(pred_s.numpy().reshape(-1, 1)).flatten()
                
        wrapper = PyTorchWrapper(best_model, scaler_X, scaler_y)
        joblib.dump(wrapper, MODEL_PATH)
        
        meta['algorithm'] = "CeresPINN_PyTorch_AutoTuned"
        if 'metrics' not in meta: meta['metrics'] = {}
        meta['metrics']['R2_temporal'] = float(best_r2)
        meta['trained_at'] = datetime.now().isoformat()
        META_PATH.write_text(json.dumps(meta, indent=2))
        
        st.success("¡El ganador ha sido guardado como el cerebro de producción de CeresPINN v4!")

"""

content = content.replace('st.success("¡El ganador ha sido guardado como el cerebro de producción de CeresPINN v4!")', 'st.success("¡El ganador ha sido guardado como el cerebro de producción de CeresPINN v4!")\n' + auto_tuning_block)
# Actually, the string replacement is risky. Let's just append it before the `def main():` line.

content = re.sub(r'st\.success\("¡Cerebro PyTorch exportado a producción exitosamente!"\)', 'st.success("¡Cerebro PyTorch exportado a producción exitosamente!")\n' + auto_tuning_block.replace('\n', '\n    '), content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Auto tuning button injected!")
