import re

file_path = "ml_lab/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the KS section
ks_pattern = re.compile(r"st\.subheader\(\"4\. Prueba de Normalidad \(Kolmogorov-Smirnov\)\"\).*?def render_training\(df\):", re.DOTALL)

new_ks = """st.subheader("4. Prueba de Normalidad (Kolmogorov-Smirnov)")
    st.write("Verifica si los rendimientos siguen una curva Normal o si requieren transformaciones matemáticas.")
    
    transf = st.radio("Aplicar Transformación:", ["Ninguna (Raw Yield)", "Logarítmica (Log Yield)", "Yeo-Johnson (Óptima Machine Learning)"])
    
    if st.button("Ejecutar KS Test"):
        data = df['yield_kg_ha'].dropna()
        if transf == "Logarítmica (Log Yield)":
            data = np.log1p(data)
        elif transf == "Yeo-Johnson (Óptima Machine Learning)":
            from scipy.stats import yeojohnson
            data, _ = yeojohnson(data)
            
        ks_stat, ks_pval = stats.kstest(data, 'norm', args=(data.mean(), data.std()))
        st.write(f"**KS-Statistic:** `{ks_stat:.4f}` | **P-Value:** `{ks_pval:.4e}`")
        if ks_pval < 0.05:
            st.error(f"❌ La distribución **NO** es normal (P-Value < 0.05).")
            st.info("💡 **Nota Agronómica:** Los rendimientos de cultivos casi nunca son normales (suelen tener 'sesgo negativo' porque las sequías provocan colapsos drásticos hacia la izquierda, pero el límite biológico corta la derecha). ¡Que este test falle es exactamente lo que justifica usar Redes Neuronales y Random Forest en lugar de Regresiones Lineales!")
        else:
            st.success(f"✅ La distribución es estadísticamente Normal (Gaussian).")
            
def render_training(df):"""

new_content = ks_pattern.sub(new_ks, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
print("Updated KS test with Yeo-Johnson")
