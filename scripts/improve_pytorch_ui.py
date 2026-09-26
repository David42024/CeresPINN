import re

file_path = "ml_lab/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Make the form look like a professional control panel
new_ui = """
    st.markdown("<h3 style='color: #3b82f6;'>🧠 CeresPINN Original (Motor PyTorch)</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.info("A diferencia de las redes neuronales estadísticas de Scikit-Learn (MLP), el verdadero **CeresPINN** es una red neuronal informada por la física (PINN) construida en **PyTorch**. Esta arquitectura aplica penalizaciones matemáticas a las derivadas parciales para obligar a la IA a respetar la termodinámica agronómica.")
    
    st.markdown("#### ⚙️ Parámetros de Entrenamiento Simple")
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            epochs = st.number_input("Épocas (Epochs)", min_value=100, max_value=2000, value=300, step=100)
        with col2:
            lr = st.number_input("Tasa de Aprendizaje (LR)", min_value=0.0001, max_value=0.1, value=0.001, step=0.001, format="%f")
        with col3:
            physics_weight = st.slider("Peso de la Física (Physics Loss)", 0.0, 1.0, 0.5)
            
        st.markdown("<br>", unsafe_allow_html=True)
        colA, colB = st.columns(2)
        with colA:
            train_btn = st.button("🔥 Iniciar Entrenamiento Simple", type="primary", use_container_width=True)
        with colB:
            search_btn = st.button("🔍 Iniciar Auto-Tuning (Grid Search)", type="secondary", use_container_width=True)
"""

# We need to replace the old UI layout in render_pytorch
old_ui_pattern = re.compile(r'st\.title\("🧠 Entrenamiento Profundo: CeresPINN Original \(PyTorch\)"\).*?search_btn = st\.button\("🔍 Auto-Tuning \(Grid Search PyTorch\)", type="secondary"\)', re.DOTALL)

content = old_ui_pattern.sub(new_ui.strip(), content)

# Improve the progress output of Auto-Tuning
auto_tuning_ui_old = """        st.info("Iniciando búsqueda masiva en PyTorch (Tomará 1-2 minutos)...")
        progress = st.progress(0)
        status = st.empty()"""
        
auto_tuning_ui_new = """        st.markdown("#### 🚀 Ejecutando Torneo de Hiperparámetros (PyTorch)...")
        status_box = st.info("Inicializando tensores y cargando grafo computacional...")
        progress_bar = st.progress(0)
        
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        best_r2_metric = metrics_col1.empty()
        current_epoch_metric = metrics_col2.empty()
        current_lr_metric = metrics_col3.empty()
        
        status = st.empty()"""
        
content = content.replace(auto_tuning_ui_old, auto_tuning_ui_new)

# Update the loop to use the new progress UI
loop_old = """                    status.text(f"Evaluando variante {count}/{total_combinations} (Epochs={ep}, LR={lr}, Physics={pw})...")"""
loop_new = """                    status_box.info(f"Evaluando variante **{count}/{total_combinations}**...")
                    current_epoch_metric.metric("Épocas", ep)
                    current_lr_metric.metric("LR", lr)
                    best_r2_metric.metric("Mejor R² Actual", f"{best_r2:.4f}" if best_r2 > -999 else "---")"""
                    
content = content.replace(loop_old, loop_new)

progress_old = """progress.progress(count / total_combinations)"""
progress_new = """progress_bar.progress(count / total_combinations)"""
content = content.replace(progress_old, progress_new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("UI improved!")
