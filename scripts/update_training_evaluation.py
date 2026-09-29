from pathlib import Path

p = Path(__file__).resolve().parents[1] / 'ml_lab/app.py'
s = p.read_text(encoding='utf-8-sig')
s = s.replace("        X = df[feature_names].fillna(0)\n        y = df['yield_kg_ha'].fillna(0)", "        training_df, excluded = observed_targets(df)\n        st.caption(f'Rendimientos faltantes o no finitos excluidos: {excluded}.')\n        if len(training_df) < 5:\n            st.error('Se requieren al menos cinco rendimientos observados.')\n            return\n        X = training_df[feature_names].replace([np.inf, -np.inf], np.nan).fillna(0)\n        y = training_df['yield_kg_ha']")
start = s.index('def render_pytorch(df):')
end = s.index('def render_final_comparison():', start)
replacement = '''def render_pytorch(df):
    st.title("🧠 Entrenamiento CeresPINN PyTorch")
    st.info("Separación temporal por años: aproximadamente 60% entrenamiento, 20% validación "
            "y 20% prueba final. Los rendimientos faltantes o no finitos se excluyen.")
    # Use the original panel so earlier target-based cleaning cannot bias holdouts.
    source = pd.read_parquet(DATA_PATH) if DATA_PATH.exists() else df.copy()
    if source.empty or not {'year', 'yield_kg_ha'}.issubset(source.columns):
        st.warning("Se necesita un panel con year y yield_kg_ha.")
        return
    try:
        parts, excluded = temporal_partitions(source)
    except ValueError as exc:
        st.error(str(exc))
        return
    names = ['Entrenamiento', 'Validación', 'Prueba independiente']
    st.caption(f"Filas excluidas por rendimiento o año inválido: {excluded}.")
    st.dataframe(pd.DataFrame([{'Partición': name, 'Desde': int(part.year.min()),
        'Hasta': int(part.year.max()), 'Observaciones': len(part)}
        for name, part in zip(names, parts)]), width='stretch')
    epochs = st.number_input("Épocas (Epochs)", 100, 2000, 300, 100)
    lr = st.number_input("Tasa de Aprendizaje (LR)", 0.0001, 0.1, 0.001, format='%f')
    weight = st.slider("Peso de penalización auxiliar", 0.0, 1.0, 0.5)
    train_btn = st.button("🔥 Iniciar Entrenamiento Simple", type='primary')
    search_btn = st.button("🔍 Iniciar Auto-Tuning (Grid Search)")
    if not (train_btn or search_btn):
        return
    import torch
    from sklearn.preprocessing import StandardScaler
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    from backend.training.pinn import CeresPINN
    from backend.training.config import TrainConfig
    from datetime import datetime
    from itertools import product

    feature_names = [f for f in ['year', 'season_temp_mean_c', 'season_tmax_mean_c',
        'season_precip_mm', 'gdd', 'cdd', 'vpd_mean_kpa'] if f in source.columns]
    scaler_X = Pipeline([('imputer', SimpleImputer(strategy='median', keep_empty_features=True)),
                         ('scaler', StandardScaler())])
    scaler_y = StandardScaler()
    X_frames = [part[feature_names].replace([np.inf, -np.inf], np.nan) for part in parts]
    X_train = scaler_X.fit_transform(X_frames[0])
    X_val = scaler_X.transform(X_frames[1])
    X_test = scaler_X.transform(X_frames[2])
    y_train = scaler_y.fit_transform(parts[0]['yield_kg_ha'].to_numpy().reshape(-1, 1))
    x_train = torch.tensor(X_train, dtype=torch.float32)
    x_val = torch.tensor(X_val, dtype=torch.float32)
    x_test = torch.tensor(X_test, dtype=torch.float32)
    y_tensor = torch.tensor(y_train, dtype=torch.float32).squeeze(-1)
    options = list(product([300, 500, 800], [0.001, 0.005, 0.01], [0.1, 0.5, 0.9])) if search_btn else [(epochs, lr, weight)]
    progress = st.progress(0.0)
    chart = st.empty()
    status = st.empty()
    best_score, best_model, best_params = -np.inf, None, None
    results = []
    for number, (ep, rate, pw) in enumerate(options):
        torch.manual_seed(42)
        model = CeresPINN(train_config=TrainConfig(), input_dim=len(feature_names))
        optimizer = torch.optim.Adam(model.parameters(), lr=rate, weight_decay=1e-5)
        history = []
        for epoch in range(1, ep + 1):
            model.train()
            optimizer.zero_grad()
            prediction, auxiliary = model(x_train)
            mse = torch.nn.functional.mse_loss(prediction, y_tensor)
            loss = mse + pw * auxiliary.mean()
            loss.backward()
            optimizer.step()
            if epoch == 1 or epoch % 10 == 0 or epoch == ep:
                model.eval()
                with torch.no_grad():
                    val_pred, _ = model(x_val)
                    val_original = scaler_y.inverse_transform(val_pred.numpy().reshape(-1, 1)).ravel()
                val_mse = mean_squared_error(parts[1]['yield_kg_ha'], val_original)
                history.append({'Época': epoch, 'MSE entrenamiento normalizado': mse.item(),
                                'MSE validación normalizado': val_mse / scaler_y.scale_[0] ** 2})
                if not search_btn:
                    chart.plotly_chart(px.line(pd.DataFrame(history), x='Época',
                        y=['MSE entrenamiento normalizado', 'MSE validación normalizado']), width='stretch')
                status.text(f"Variante {number + 1}/{len(options)}, época {epoch}/{ep}")
        model.eval()
        with torch.no_grad():
            pred_val, _ = model(x_val)
            observed_scale = scaler_y.inverse_transform(pred_val.numpy().reshape(-1, 1)).ravel()
        score = r2_score(parts[1]['yield_kg_ha'], observed_scale)
        results.append({'Épocas': ep, 'LR': rate, 'Peso auxiliar': pw, 'R² validación': score})
        if np.isfinite(score) and score > best_score:
            best_score, best_model = score, model
            best_params = {'epochs': ep, 'lr': rate, 'auxiliary_weight': pw}
        progress.progress((number + 1) / len(options))
    if best_model is None:
        st.error("No se obtuvo un modelo con métricas finitas. No se guardó ningún artefacto.")
        return
    st.dataframe(pd.DataFrame(results).sort_values('R² validación', ascending=False), width='stretch')
    # Test is evaluated once, after selecting the configuration using validation.
    best_model.eval()
    with torch.no_grad():
        test_prediction, _ = best_model(x_test)
        prediction = scaler_y.inverse_transform(test_prediction.numpy().reshape(-1, 1)).ravel()
    actual = parts[2]['yield_kg_ha'].to_numpy()
    metrics = {'R2_test_temporal': float(r2_score(actual, prediction)),
               'RMSE_test_kg_ha': float(np.sqrt(mean_squared_error(actual, prediction))),
               'MAE_test_kg_ha': float(mean_absolute_error(actual, prediction)),
               'R2_validation': float(best_score)}
    st.subheader("Resultados de prueba independiente")
    a, b, c = st.columns(3)
    a.metric("R² prueba", f"{metrics['R2_test_temporal']:.4f}")
    b.metric("RMSE prueba (kg/ha)", f"{metrics['RMSE_test_kg_ha']:.2f}")
    c.metric("MAE prueba (kg/ha)", f"{metrics['MAE_test_kg_ha']:.2f}")
    comparison = pd.DataFrame({'Observado': actual, 'Predicho': prediction, 'Año': parts[2]['year'].to_numpy()})
    st.plotly_chart(px.scatter(comparison, x='Observado', y='Predicho', color='Año',
        title='Rendimiento observado frente a predicho en prueba independiente'), width='stretch')
    st.download_button('Descargar predicciones de prueba', comparison.to_csv(index=False).encode('utf-8-sig'),
                       'pytorch_prueba.csv', 'text/csv')
    wrapper = PyTorchWrapper(best_model, scaler_X, scaler_y)
    joblib.dump(wrapper, MODEL_PATH)
    metadata = {'algorithm': 'CeresPINN_PyTorch_AutoTuned' if search_btn else 'CeresPINN_PyTorch_Real',
        'metrics': metrics, 'feature_names': feature_names, 'best_params': best_params,
        'trained_at': datetime.now().isoformat(), 'excluded_invalid_rows': excluded,
        'evaluation_protocol': 'chronological_year_train_validation_test',
        'partitions': {name: {'years': sorted(int(y) for y in part.year.unique()), 'rows': len(part)}
                       for name, part in zip(['train', 'validation', 'test'], parts)}}
    META_PATH.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    st.success("Modelo y métricas independientes guardados.")


'''
s = s[:start] + replacement + s[end:]
p.write_text(s, encoding='utf-8')
