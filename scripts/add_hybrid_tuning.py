import re

file_path = "ml_lab/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update UI to add 5. Ensamble
ui_pattern = re.compile(r"st\.markdown\(\"#### 4\. Regresión Ridge\"\).*?rd_svd = st\.checkbox\(\"Solver SVD\", value=True, key=\"d4\"\)", re.DOTALL)

new_ui = """st.markdown("#### 4. Regresión Ridge (Tradicional)")
    col1, col2 = st.columns(2)
    with col1:
        rd_a01 = st.checkbox("Alpha 0.1", value=True, key="d1")
        rd_a1 = st.checkbox("Alpha 1.0", value=True, key="d2")
    with col2:
        rd_auto = st.checkbox("Solver Auto", value=True, key="d3")
        rd_svd = st.checkbox("Solver SVD", value=True, key="d4")
        
    st.markdown("#### 5. Ensamble Físico-Estadístico (Híbrido: Ridge + MLP)")
    st.write("Combina la linealidad matemática de Ridge con la no-linealidad de la red neuronal. Evaluaremos la regularización del juez final (Meta-Modelo).")
    col1, col2 = st.columns(2)
    with col1:
        st_meta_a1 = st.checkbox("Meta-Ridge Alpha 1.0", value=True, key="st1")
    with col2:
        st_meta_a10 = st.checkbox("Meta-Ridge Alpha 10.0", value=True, key="st2")"""
content = ui_pattern.sub(new_ui, content)

# 2. Update Backend to add Stacking
backend_pattern = re.compile(r"grids\[\"Ridge\"\] = \(Ridge\(random_state=42\), \{'model__alpha': r_alphas, 'model__solver': solvers\}\)", re.DOTALL)

new_backend = """grids["Ridge"] = (Ridge(random_state=42), {'model__alpha': r_alphas, 'model__solver': solvers})
        
        # 5. Stacking (Hybrid)
        from sklearn.ensemble import StackingRegressor
        st_alphas = []
        if st_meta_a1: st_alphas.append(1.0)
        if st_meta_a10: st_alphas.append(10.0)
        
        base_estimators = [
            ('ridge', Ridge(alpha=1.0, random_state=42)),
            ('mlp', MLPRegressor(hidden_layer_sizes=(64,32), max_iter=200, random_state=42))
        ]
        
        grids["Ensamble Híbrido"] = (
            StackingRegressor(estimators=base_estimators, final_estimator=Ridge()), 
            {'model__final_estimator__alpha': st_alphas}
        )"""
content = backend_pattern.sub(new_backend, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Hybrid model added to Massive Tuning successfully.")
