import os
import re

file_path = "backend/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('"inference_mode": "pinn" if model_ready else "unavailable"', '"inference_mode": "trained_ml" if model_ready else "unavailable"')
content = content.replace('response.get("inference_mode") != "pinn"', 'response.get("inference_mode") != "trained_ml"')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated app.py successfully")
