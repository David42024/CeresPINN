import re

file_path = "ml_lab/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Suppress warnings
imports = """import sys
import warnings
from sklearn.exceptions import ConvergenceWarning
warnings.filterwarnings("ignore", category=ConvergenceWarning)
"""
content = content.replace("import sys", imports)

# 2. Fix deprecation warning use_container_width -> width='stretch'
# (Or just remove it if width='stretch' fails on some versions, but the warning said to use it)
content = content.replace("use_container_width=True", 'use_container_width=True') # Wait, I will just suppress it if it crashes. Actually, I will replace it with nothing if it's annoying, or leave it. The user said "corrige", let's replace it.
content = content.replace("use_container_width=True", "width='stretch'")

# 3. Increase max_iter for MLP
content = content.replace("max_iter=300", "max_iter=800, early_stopping=True, n_iter_no_change=10")
content = content.replace("max_iter=200", "max_iter=600, early_stopping=True, n_iter_no_change=10")

# 4. Save models in "6. Entrenamiento y Validación Cruzada"
train_pattern = re.compile(r"results\.append\(\{.*?Algoritmo.*?RMSE_kg_ha.*?\)\}\)", re.DOTALL)
content = re.sub(
    r"(results\.append\(\{\"Algoritmo\": name, \"R2 Promedio\".*?\}\))",
    r"\1\n                import joblib\n                import json\n                from datetime import datetime\n                if 'CeresPINN' in name:\n                    pipeline.fit(X, y)\n                    joblib.dump(pipeline, MODEL_PATH)\n                    meta = json.loads(META_PATH.read_text()) if META_PATH.exists() else {}\n                    meta['algorithm'] = 'CeresPINN_MLP_Retrained'\n                    if 'metrics' not in meta: meta['metrics'] = {}\n                    meta['metrics']['R2_temporal'] = mean_r2\n                    meta['trained_at'] = datetime.now().isoformat()\n                    META_PATH.write_text(json.dumps(meta, indent=2))",
    content
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed warnings and added persistence to training.")
