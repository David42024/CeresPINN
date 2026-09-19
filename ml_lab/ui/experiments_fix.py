#!/usr/bin/env python3
"""Script to fix the experiment results display issue in ML Lab."""

import re

# Read the file
with open('ml_lab/ui/experiments.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# 1. Add the session state flag check at the beginning of render_experiment_tracking
# Find the line with "st.title" and add the flag check after it
old_title_pattern = r'(st\.title\("🧪 Experiment Tracking"\))'
new_title_replacement = r'''\1

    # ✅ Mostrar experimento recién completado si existe en session state
    if st.session_state.get("experiment_just_completed", False):
        exp_name = st.session_state.get("last_completed_exp", "")
        metrics = st.session_state.get("last_completed_metrics", {})
        if exp_name and metrics:
            st.success(f"🎉 Experimento **{exp_name}** completado exitosamente!")
            st.metric("R²", f"{metrics.get('r2', 0):.4f}")
            st.metric("MAE", f"{metrics.get('mae', 0):.2f}")
            st.metric("RMSE", f"{metrics.get('rmse', 0):.2f}")
            st.metric("MAPE", f"{metrics.get('mape', 0):.2%}")
            st.markdown("---")
            st.info("💡 **Next step (FICHA 5):** Go to **'Validation'** for Hindcast verification (1990–2020) and **'Statistical Tests'** for KS test, paired t-test, and Sobol sensitivity analysis.")
            # Reset the flag
            st.session_state.experiment_just_completed = False
            st.session_state.last_completed_exp = ""
            st.session_state.last_completed_metrics = {}'

# Apply the replacement
content = re.sub(old_title_pattern, new_title_replacement, content, flags=re.MULTILINE)

# 2. Add the st.rerun() call after experiment training completes
# Find the section where experiment results are persisted and add session state flag
old_persist_pattern = r'(artifact_manager\.save_artifact\(\s*project_id,\s*"experiments",\s*f"{config\$name\$}_metadata\.json",\s*config,\)'
new_persist_replacement = r'''\1

                            # ✅ FLAG: Marcar que experimento recién completó
                            # Esto permitirá que la UI se refresque y muestre el experimento
                            st.session_state.experiment_just_completed = True
                            st.session_state.last_completed_exp = exp_name
                            st.session_state.last_completed_metrics = res.metrics if any_success else {}'

content = re.sub(old_persist_pattern, new_persist_replacement, content, flags=re.MULTILINE)

# Write back
with open('ml_lab/ui/experiments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fix applied successfully!")
print("Se han agregado:")
print("  1. Bandera experiment_just_completed en session_state")
print("  2. Mostrar métricas después de rerun")
print("  3. Resetear flags después de mostrar")